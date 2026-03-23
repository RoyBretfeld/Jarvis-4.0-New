"""
AWP-062 – Decision Log
SQLite-Datenbank: Jarvis begründet WARUM Architektur-Entscheidungen
getroffen wurden (Forensik / Langzeitgedächtnis).

Schema:
  decisions(id, timestamp, awp_id, category, title, rationale,
            alternatives, chosen, impact, agent, tags)

Python 3.12 | AsyncIO | aiosqlite
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

log = logging.getLogger("jarvis.decision_log")

DB_PATH = Path(__file__).parent.parent / "data" / "decisions.db"


# ─────────────────────────────────────────────
# Schema init
# ─────────────────────────────────────────────

CREATE_DDL = """
CREATE TABLE IF NOT EXISTS decisions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   TEXT    NOT NULL,
    awp_id      TEXT,
    category    TEXT    NOT NULL,   -- architecture | security | performance | tooling
    title       TEXT    NOT NULL,
    rationale   TEXT    NOT NULL,
    alternatives TEXT   DEFAULT '[]',
    chosen      TEXT    NOT NULL,
    impact      TEXT    DEFAULT 'low',  -- low | medium | high | critical
    agent       TEXT    DEFAULT 'system',
    tags        TEXT    DEFAULT '[]'
);

CREATE INDEX IF NOT EXISTS idx_decisions_awp ON decisions(awp_id);
CREATE INDEX IF NOT EXISTS idx_decisions_cat ON decisions(category);
CREATE INDEX IF NOT EXISTS idx_decisions_ts  ON decisions(timestamp);

CREATE TABLE IF NOT EXISTS decision_revisions (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_id  INTEGER REFERENCES decisions(id),
    revised_at   TEXT    NOT NULL,
    old_rationale TEXT,
    new_rationale TEXT,
    revised_by   TEXT
);
"""


async def _get_conn() -> Any:
    try:
        import aiosqlite  # type: ignore
    except ImportError:
        raise RuntimeError("aiosqlite not installed. Run: pip install aiosqlite")
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = await aiosqlite.connect(DB_PATH)
    conn.row_factory = aiosqlite.Row
    await conn.executescript(CREATE_DDL)
    await conn.commit()
    return conn


# ─────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────

async def log_decision(
    title: str,
    rationale: str,
    chosen: str,
    category: str = "architecture",
    awp_id: str | None = None,
    alternatives: list[str] | None = None,
    impact: str = "medium",
    agent: str = "system",
    tags: list[str] | None = None,
) -> int:
    """Insert a decision record. Returns the new row ID."""
    conn = await _get_conn()
    try:
        ts = datetime.now(tz=timezone.utc).isoformat()
        cursor = await conn.execute(
            """INSERT INTO decisions
               (timestamp, awp_id, category, title, rationale,
                alternatives, chosen, impact, agent, tags)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (ts, awp_id, category, title, rationale,
             json.dumps(alternatives or []), chosen, impact,
             agent, json.dumps(tags or [])),
        )
        await conn.commit()
        row_id = cursor.lastrowid
        log.info("Decision logged [%s]: %s → %s (id=%d)", awp_id, title, chosen, row_id)
        return row_id
    finally:
        await conn.close()


async def get_decisions(
    awp_id: str | None = None,
    category: str | None = None,
    limit: int = 50,
) -> list[dict]:
    conn = await _get_conn()
    try:
        where_clauses = []
        params: list[Any] = []
        if awp_id:
            where_clauses.append("awp_id = ?")
            params.append(awp_id)
        if category:
            where_clauses.append("category = ?")
            params.append(category)
        where = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
        params.append(limit)
        cursor = await conn.execute(
            f"SELECT * FROM decisions {where} ORDER BY timestamp DESC LIMIT ?",
            params,
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        await conn.close()


async def revise_decision(
    decision_id: int,
    new_rationale: str,
    revised_by: str = "system",
) -> None:
    conn = await _get_conn()
    try:
        row = await (await conn.execute(
            "SELECT rationale FROM decisions WHERE id=?", (decision_id,)
        )).fetchone()
        if not row:
            raise ValueError(f"Decision {decision_id} not found")
        await conn.execute(
            """INSERT INTO decision_revisions
               (decision_id, revised_at, old_rationale, new_rationale, revised_by)
               VALUES (?,?,?,?,?)""",
            (decision_id, datetime.now(tz=timezone.utc).isoformat(),
             row["rationale"], new_rationale, revised_by),
        )
        await conn.execute(
            "UPDATE decisions SET rationale=? WHERE id=?",
            (new_rationale, decision_id),
        )
        await conn.commit()
        log.info("Decision %d revised by %s", decision_id, revised_by)
    finally:
        await conn.close()


# ─────────────────────────────────────────────
# Seed initial architectural decisions
# ─────────────────────────────────────────────

SEED_DECISIONS = [
    dict(title="4-Container Architecture", awp_id="AWP-003",
         rationale="Isolation of concerns: core/rag/gateway/sandbox prevents "
                   "a compromised agent from accessing the host filesystem.",
         chosen="Docker Compose with jarvis-internal network",
         alternatives=["Monolith", "Kubernetes (overkill for single-node)"],
         category="architecture", impact="critical", tags=["docker", "security"]),
    dict(title="Hybrid RAG: Qdrant + ChromaDB", awp_id="AWP-007",
         rationale="Qdrant handles semantic (vector) search; ChromaDB handles "
                   "keyword/BM25 search. Together they provide higher recall.",
         chosen="Both backends, unified via JarvisMemory facade",
         alternatives=["Qdrant only", "ChromaDB only", "Weaviate"],
         category="architecture", impact="high", tags=["rag", "vector-db"]),
    dict(title="bge-small-en-v1.5 as embedding model", awp_id="AWP-013",
         rationale="384 dimensions keeps memory footprint small on the Ryzen. "
                   "Quality sufficient for code and docs retrieval.",
         chosen="bge-small-en-v1.5 via SentenceTransformers",
         alternatives=["text-embedding-ada-002 (cloud, privacy risk)",
                       "bge-large (2x RAM)"],
         category="performance", impact="high", tags=["embedding", "rag"]),
    dict(title="ProcessPoolExecutor for embedding", awp_id="AWP-018",
         rationale="SentenceTransformers releases the GIL during inference. "
                   "4 workers map to Ryzen threads 4-7 (RAG cpuset).",
         chosen="ProcessPoolExecutor(max_workers=4)",
         alternatives=["ThreadPoolExecutor (GIL-limited)", "Single-threaded"],
         category="performance", impact="medium", tags=["multiprocessing", "ryzen"]),
]


async def seed_initial_decisions() -> None:
    """Idempotent: only seeds if decisions table is empty."""
    conn = await _get_conn()
    try:
        count = (await (
            await conn.execute("SELECT COUNT(*) FROM decisions")
        ).fetchone())[0]
        if count > 0:
            return
    finally:
        await conn.close()
    for d in SEED_DECISIONS:
        await log_decision(**d)
    log.info("Seeded %d initial decisions", len(SEED_DECISIONS))
