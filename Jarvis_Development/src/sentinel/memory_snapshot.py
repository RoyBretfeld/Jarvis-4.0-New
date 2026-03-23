"""
AWP-088 – Memory Snapshot
Stündlicher Export der RAG-Vektor-Datenbank als Backup.

Backup-Inhalt:
  - Qdrant collection → JSONL (payload + vector)
  - ChromaDB collection → JSONL (document + embedding)
  - Snapshot manifest (count, timestamp, sha256)

Ablage: logs/backups/rag_snapshots/YYYY-MM-DD_HH-MM/

Python 3.12 | AsyncIO
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

log = logging.getLogger("jarvis.sentinel.memory_snapshot")

PROJECT_ROOT  = Path(__file__).parent.parent.parent
SNAPSHOT_ROOT = PROJECT_ROOT / "logs" / "backups" / "rag_snapshots"
KEEP_SNAPSHOTS = int(__import__("os").environ.get("RAG_KEEP_SNAPSHOTS", "24"))  # hours

try:
    from config import QDRANT_HOST, QDRANT_PORT, QDRANT_COLLECTION  # type: ignore
except ImportError:
    QDRANT_HOST       = "localhost"
    QDRANT_PORT       = 6333
    QDRANT_COLLECTION = "jarvis_knowledge"


@dataclass
class SnapshotManifest:
    snapshot_id: str
    started_at: str
    finished_at: str = ""
    qdrant_count: int = 0
    chroma_count: int = 0
    total_bytes: int = 0
    sha256: str = ""
    success: bool = False
    error: str = ""


async def _export_qdrant(out_path: Path, loop: asyncio.AbstractEventLoop) -> int:
    """Export all Qdrant points to JSONL. Returns count."""
    try:
        from qdrant_client import QdrantClient  # type: ignore
    except ImportError:
        log.warning("qdrant_client not installed — Qdrant snapshot skipped")
        return 0

    def _do_export() -> int:
        client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT, timeout=10)
        count = 0
        offset = None
        with out_path.open("w", encoding="utf-8") as f:
            while True:
                points, next_offset = client.scroll(
                    collection_name=QDRANT_COLLECTION,
                    limit=200,
                    offset=offset,
                    with_payload=True,
                    with_vectors=True,
                )
                if not points:
                    break
                for p in points:
                    record = {
                        "id": str(p.id),
                        "payload": p.payload,
                        "vector": p.vector,
                    }
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
                    count += 1
                offset = next_offset
                if offset is None:
                    break
        return count

    try:
        return await loop.run_in_executor(None, _do_export)
    except Exception as exc:
        log.error("Qdrant export failed: %s", exc)
        return 0


async def _export_chroma(out_path: Path, loop: asyncio.AbstractEventLoop) -> int:
    """Export ChromaDB collection to JSONL. Returns count."""
    try:
        import chromadb  # type: ignore
    except ImportError:
        log.warning("chromadb not installed — ChromaDB snapshot skipped")
        return 0

    def _do_export() -> int:
        client = chromadb.HttpClient(host="localhost", port=8001)
        try:
            col = client.get_collection("jarvis_knowledge")
        except Exception:
            return 0
        results = col.get(include=["documents", "metadatas", "embeddings"])
        ids  = results.get("ids", [])
        docs = results.get("documents", [])
        metas = results.get("metadatas", [])
        embeds = results.get("embeddings", [])
        with out_path.open("w", encoding="utf-8") as f:
            for i, doc_id in enumerate(ids):
                record = {
                    "id": doc_id,
                    "document": docs[i] if i < len(docs) else "",
                    "metadata": metas[i] if i < len(metas) else {},
                    "embedding": embeds[i] if i < len(embeds) else None,
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return len(ids)

    try:
        return await loop.run_in_executor(None, _do_export)
    except Exception as exc:
        log.error("ChromaDB export failed: %s", exc)
        return 0


def _sha256_dir(directory: Path) -> str:
    """Compute combined SHA-256 of all files in a directory."""
    h = hashlib.sha256()
    for f in sorted(directory.rglob("*")):
        if f.is_file():
            h.update(f.read_bytes())
    return h.hexdigest()


async def take_snapshot() -> SnapshotManifest:
    """
    Export both RAG backends to a timestamped snapshot directory.
    Returns SnapshotManifest with counts and integrity hash.
    """
    ts = datetime.now(tz=timezone.utc)
    snap_id = ts.strftime("%Y-%m-%d_%H-%M")
    snap_dir = SNAPSHOT_ROOT / snap_id
    snap_dir.mkdir(parents=True, exist_ok=True)

    manifest = SnapshotManifest(
        snapshot_id=snap_id,
        started_at=ts.isoformat(),
    )

    loop = asyncio.get_event_loop()

    qdrant_file = snap_dir / "qdrant.jsonl"
    chroma_file = snap_dir / "chroma.jsonl"

    manifest.qdrant_count, manifest.chroma_count = await asyncio.gather(
        _export_qdrant(qdrant_file, loop),
        _export_chroma(chroma_file, loop),
    )

    # Compute size + integrity hash
    manifest.total_bytes = sum(
        f.stat().st_size for f in snap_dir.iterdir() if f.is_file()
    )
    manifest.sha256 = await loop.run_in_executor(None, _sha256_dir, snap_dir)
    manifest.finished_at = datetime.now(tz=timezone.utc).isoformat()
    manifest.success = True

    # Write manifest
    manifest_path = snap_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest.__dict__, indent=2), encoding="utf-8"
    )

    log.info(
        "RAG snapshot %s: qdrant=%d chroma=%d size=%d bytes sha256=%s…",
        snap_id, manifest.qdrant_count, manifest.chroma_count,
        manifest.total_bytes, manifest.sha256[:12],
    )

    # Prune old snapshots
    await loop.run_in_executor(None, _prune_old_snapshots)
    return manifest


def _prune_old_snapshots() -> None:
    """Keep only KEEP_SNAPSHOTS most recent snapshots."""
    if not SNAPSHOT_ROOT.exists():
        return
    snapshots = sorted(
        [d for d in SNAPSHOT_ROOT.iterdir() if d.is_dir()],
        key=lambda d: d.name,
    )
    to_delete = snapshots[:-KEEP_SNAPSHOTS] if len(snapshots) > KEEP_SNAPSHOTS else []
    for d in to_delete:
        import shutil
        shutil.rmtree(d, ignore_errors=True)
        log.info("Pruned old snapshot: %s", d.name)


async def run_hourly_loop() -> None:
    """Run take_snapshot() every hour indefinitely."""
    log.info("Memory snapshot loop started (interval=1h, keep=%d)", KEEP_SNAPSHOTS)
    while True:
        try:
            manifest = await take_snapshot()
            log.info("Hourly snapshot complete: %s", manifest.snapshot_id)
        except Exception as exc:
            log.error("Snapshot failed: %s", exc)
        await asyncio.sleep(3600)


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    cmd = sys.argv[1] if len(sys.argv) > 1 else "once"
    if cmd == "once":
        m = asyncio.run(take_snapshot())
        print(f"Snapshot: {m.snapshot_id} | qdrant={m.qdrant_count} chroma={m.chroma_count}")
    elif cmd == "loop":
        asyncio.run(run_hourly_loop())
