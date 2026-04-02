"""
Jarvis 4.0 – Core API Server (FastAPI)
AWP-017: REST endpoints  |  AWP-024: WebSocket log stream
AWP-029: File browser API
Endpoints: /health /status /search /ingest /skills /ws/logs /ws/terminal
           /files /files/content /system/threads /agent/*
Python 3.12 | FastAPI | RB-Protokoll: Glass-Box (alle Aktionen geloggt)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re as _re
import stat
from pathlib import Path
from typing import Any

import shutil
import tempfile

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

# ─────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_DIR / "api.log", encoding="utf-8"),
    ],
)
log = logging.getLogger("jarvis.api")

# ─────────────────────────────────────────────
# App
# ─────────────────────────────────────────────
MAX_UPLOAD_MB = int(os.environ.get("MAX_UPLOAD_MB", "200"))

app = FastAPI(
    title="Jarvis 4.0 Core API",
    version="1.0.0",
    description="Internal API for Jarvis dashboard and agent communication.",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS: nur localhost (kein externer Zugriff)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1",
        "http://127.0.0.1:3001",
    ],
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────
# Request / Response models
# ─────────────────────────────────────────────
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(default=5, ge=1, le=20)
    mode: str = Field(default="hybrid", pattern="^(hybrid|semantic|keyword)$")
    score_threshold: float = Field(default=0.3, ge=0.0, le=1.0)


class SearchResultItem(BaseModel):
    doc_id: str
    text: str
    score: float
    source: str
    metadata: dict[str, Any]


class SearchResponse(BaseModel):
    query: str
    count: int
    results: list[SearchResultItem]


class IngestRequest(BaseModel):
    target_dir: str = Field(default="strategy",
                            description="Relative path inside project root")


class IngestResponse(BaseModel):
    status: str
    totals: dict[str, int]


class HealthResponse(BaseModel):
    status: str
    backends: dict[str, bool]
    version: str = "1.0.0"


# ─────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────
@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health() -> HealthResponse:
    """Prüft Backend-Verbindungen (Qdrant, ChromaDB)."""
    try:
        from memory_interface import get_memory  # type: ignore
        backends = get_memory().health()
        overall = "healthy" if all(backends.values()) else "degraded"
    except Exception as exc:
        log.error("Health check failed: %s", exc)
        backends = {"qdrant": False, "chroma": False}
        overall = "unhealthy"

    log.info("GET /health → %s", overall)
    return HealthResponse(status=overall, backends=backends)


@app.get("/status", tags=["System"])
async def status() -> dict[str, Any]:
    """Gibt den aktuellen state.json Inhalt zurück."""
    import json
    state_path = Path(__file__).parent.parent / "state.json"
    if not state_path.exists():
        raise HTTPException(status_code=404, detail="state.json not found")
    data = json.loads(state_path.read_text(encoding="utf-8"))
    log.info("GET /status → phase=%s", data.get("current_phase"))
    return data


@app.post("/search", response_model=SearchResponse, tags=["RAG"])
async def search(req: SearchRequest) -> SearchResponse:
    """
    Semantische / Hybrid-Suche im RAG-Gedächtnis.
    Transparenz: jedes Ergebnis enthält Score und Quelle.
    """
    log.info("POST /search query='%s' mode=%s top_k=%d",
             req.query[:60], req.mode, req.top_k)
    try:
        from memory_interface import get_memory  # type: ignore
        results = await get_memory().search(
            query=req.query,
            top_k=req.top_k,
            mode=req.mode,
            score_threshold=req.score_threshold,
        )
    except Exception as exc:
        log.error("Search error: %s", exc, exc_info=True)
        raise HTTPException(status_code=503, detail=f"RAG backend error: {exc}") from exc

    items = [
        SearchResultItem(
            doc_id=r.document.doc_id,
            text=r.document.text,
            score=r.score,
            source=r.source,
            metadata=r.document.metadata,
        )
        for r in results
    ]
    return SearchResponse(query=req.query, count=len(items), results=items)


@app.post("/ingest", response_model=IngestResponse, tags=["RAG"])
async def ingest(req: IngestRequest) -> IngestResponse:
    """
    Startet die Ingestion-Pipeline für ein Verzeichnis.
    Nur intern erreichbar (kein exterener Port exposed).
    """
    project_root = Path(__file__).parent.parent
    target = (project_root / req.target_dir).resolve()

    # Path traversal guard
    if not str(target).startswith(str(project_root.resolve())):
        raise HTTPException(status_code=400, detail="Path traversal not allowed")

    if not target.is_dir():
        raise HTTPException(status_code=404,
                            detail=f"Directory not found: {req.target_dir}")

    log.info("POST /ingest target=%s", target)
    try:
        from ingest_docs import IngestionPipeline  # type: ignore
        pipeline = IngestionPipeline(docs_dir=target)
        totals = await pipeline.run()
        return IngestResponse(status="completed", totals=totals)
    except Exception as exc:
        log.error("Ingest error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/upload", tags=["RAG"])
async def upload_document(file: UploadFile = File(...)) -> dict[str, Any]:
    """
    Nimmt PDF, MD oder TXT entgegen (max 200MB), verarbeitet es und
    bettet es in ChromaDB/Qdrant ein. PDFs werden mit VLM gescannt.
    """
    allowed_ext = {".pdf", ".md", ".txt"}
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in allowed_ext:
        raise HTTPException(status_code=400,
                            detail=f"Unsupported file type: {suffix}. Allowed: {allowed_ext}")

    # Größe prüfen (Content-Length Header wenn verfügbar)
    max_bytes = MAX_UPLOAD_MB * 1024 * 1024

    tmp_path: Path | None = None
    try:
        # In temp-Datei streamen (kein RAM-Overflow bei 200MB)
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp_path = Path(tmp.name)
            total = 0
            chunk_size = 1024 * 1024  # 1MB chunks
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large. Max {MAX_UPLOAD_MB}MB."
                    )
                tmp.write(chunk)

        log.info("Upload received: %s (%.1f MB)", file.filename, total / 1024 / 1024)

        # ── Verarbeitung ──────────────────────────
        from ingest_docs import MarkdownChunker, TextChunk  # type: ignore
        from memory_interface import Document, get_memory  # type: ignore

        chunks: list[TextChunk] = []

        if suffix == ".pdf":
            from pdf_processor import extract_pdf  # type: ignore
            from vlm_scanner import scan_page_images  # type: ignore

            pdf_doc = extract_pdf(tmp_path)
            chunker = MarkdownChunker()
            source_label = f"upload::{file.filename}"

            for page in pdf_doc.pages:
                # VLM-Scan wenn die Seite signifikante Bilder hat
                vlm_text = ""
                if page.has_significant_visuals:
                    log.info("VLM scanning page %d of %s…", page.page_num, file.filename)
                    vlm_text = await scan_page_images(page.images_b64)

                # Text + VLM-Beschreibung zusammenführen
                combined = page.text
                if vlm_text:
                    combined += f"\n\n[VLM-Analyse Seite {page.page_num}]:\n{vlm_text}"

                if combined.strip():
                    page_chunks = chunker.chunk(
                        combined,
                        source=f"{source_label}::page_{page.page_num}"
                    )
                    chunks.extend(page_chunks)

        else:
            # MD / TXT
            text = tmp_path.read_text(encoding="utf-8", errors="replace")
            chunker = MarkdownChunker()
            chunks = chunker.chunk(text, source=f"upload::{file.filename}")

        if not chunks:
            return {"status": "empty", "filename": file.filename, "chunks": 0}

        # Embedding + Upsert
        from ingest_docs import _embed_chunk  # type: ignore
        from concurrent.futures import ProcessPoolExecutor  # type: ignore

        loop = asyncio.get_event_loop()
        with ProcessPoolExecutor(max_workers=4) as pool:
            vectors = await asyncio.gather(
                *[loop.run_in_executor(pool, _embed_chunk, c.text) for c in chunks]
            )

        memory = get_memory()
        docs = [
            Document(
                doc_id=f"{c.source_file}::chunk_{c.chunk_index}",
                text=c.text,
                metadata={"source": c.source_file, "chunk_index": c.chunk_index,
                          "filename": file.filename},
            )
            for c in chunks
        ]
        totals = await memory.upsert(docs)
        log.info("Upload ingested: %s → %d chunks, %s", file.filename, len(chunks), totals)
        return {
            "status": "completed",
            "filename": file.filename,
            "size_mb": round(total / 1024 / 1024, 2),
            "chunks": len(chunks),
            "totals": totals,
        }

    except HTTPException:
        raise
    except Exception as exc:
        log.error("Upload error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        if tmp_path and tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


@app.get("/skills", tags=["Skills"])
async def list_skills() -> list[dict[str, Any]]:
    """Gibt alle geladenen Skills als JSON zurück."""
    try:
        from librarian import load_skills  # type: ignore
        skills_dir = Path(__file__).parent.parent / "skills"
        skills = load_skills(skills_dir)
        return [
            {
                "name": s.name,
                "description": s.description,
                "version": s.version,
                "tools": s.tools,
            }
            for s in skills
        ]
    except Exception as exc:
        log.error("Skills list error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ─────────────────────────────────────────────
# AWP-024: WebSocket – Live Log Stream
# ─────────────────────────────────────────────
class _LogBroadcaster(logging.Handler):
    """Forwards log records to all connected WebSocket clients."""

    def __init__(self) -> None:
        super().__init__()
        self._clients: set[WebSocket] = set()
        self._loop: asyncio.AbstractEventLoop | None = None

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def add_client(self, ws: WebSocket) -> None:
        self._clients.add(ws)

    def remove_client(self, ws: WebSocket) -> None:
        self._clients.discard(ws)

    def emit(self, record: logging.LogRecord) -> None:
        if not self._clients or self._loop is None:
            return
        import datetime as _dt
        payload = json.dumps({
            "ts": _dt.datetime.fromtimestamp(record.created).strftime("%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "service": record.name,
            "message": record.getMessage(),
        })
        asyncio.run_coroutine_threadsafe(self._broadcast(payload), self._loop)

    async def _broadcast(self, payload: str) -> None:
        dead: list[WebSocket] = []
        for ws in list(self._clients):
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._clients.discard(ws)


_broadcaster = _LogBroadcaster()
logging.getLogger().addHandler(_broadcaster)


@app.on_event("startup")
async def _attach_broadcaster() -> None:
    _broadcaster.set_loop(asyncio.get_event_loop())


@app.websocket("/ws/logs")
async def ws_logs(ws: WebSocket) -> None:
    """Stream live log lines to the UI."""
    await ws.accept()
    _broadcaster.add_client(ws)
    log.info("WS /ws/logs client connected")
    try:
        while True:
            await asyncio.sleep(30)  # keep-alive ping
            await ws.send_text(json.dumps({
                "ts": "", "level": "DEBUG", "service": "ws", "message": "ping",
            }))
    except WebSocketDisconnect:
        pass
    finally:
        _broadcaster.remove_client(ws)
        log.info("WS /ws/logs client disconnected")


@app.websocket("/ws/terminal")
async def ws_terminal(ws: WebSocket) -> None:
    """Proxy terminal I/O to jarvis-sandbox via subprocess."""
    import subprocess, shutil
    await ws.accept()
    shell = shutil.which("bash") or shutil.which("sh") or "sh"
    proc = await asyncio.create_subprocess_exec(
        shell,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        env={**os.environ, "TERM": "xterm-256color"},
    )
    log.info("WS /ws/terminal: shell PID %d", proc.pid)

    async def _stdout_to_ws() -> None:
        assert proc.stdout
        while True:
            chunk = await proc.stdout.read(1024)
            if not chunk:
                break
            await ws.send_text(chunk.decode(errors="replace"))

    reader_task = asyncio.create_task(_stdout_to_ws())

    try:
        while True:
            raw = await ws.receive_text()
            msg = json.loads(raw)
            if msg.get("type") == "input" and proc.stdin:
                proc.stdin.write(msg["data"].encode())
                await proc.stdin.drain()
            # resize messages are logged but ptty control is not implemented here
    except (WebSocketDisconnect, Exception):
        pass
    finally:
        reader_task.cancel()
        proc.kill()


# ─────────────────────────────────────────────
# AWP-029: File Browser API
# ─────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
_ALLOWED_EXTENSIONS = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".md", ".json",
    ".yml", ".yaml", ".txt", ".cfg", ".toml", ".env",
}


def _build_tree(path: Path, depth: int = 0, max_depth: int = 4) -> list[dict]:
    if depth > max_depth:
        return []
    items = []
    try:
        for child in sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name)):
            if child.name.startswith(".") and child.name not in (".env",):
                continue
            if child.name in ("node_modules", "__pycache__", ".next", ".git"):
                continue
            entry: dict[str, Any] = {
                "name": child.name,
                "path": str(child.relative_to(PROJECT_ROOT)),
                "type": "file" if child.is_file() else "directory",
            }
            if child.is_file():
                entry["size"] = child.stat().st_size
            else:
                entry["children"] = _build_tree(child, depth + 1, max_depth)
            items.append(entry)
    except PermissionError:
        pass
    return items


@app.get("/files", tags=["Files"])
async def list_files() -> list[dict]:
    return _build_tree(PROJECT_ROOT)


@app.get("/files/content", tags=["Files"])
async def get_file_content(path: str) -> dict[str, str]:
    target = (PROJECT_ROOT / path).resolve()
    if not str(target).startswith(str(PROJECT_ROOT)):
        raise HTTPException(400, "Path traversal not allowed")
    if not target.is_file():
        raise HTTPException(404, "File not found")
    if target.suffix not in _ALLOWED_EXTENSIONS:
        raise HTTPException(403, f"Extension {target.suffix!r} not allowed")
    if target.stat().st_size > 512 * 1024:
        raise HTTPException(413, "File too large (max 512 KB)")
    return {"content": target.read_text(encoding="utf-8", errors="replace")}


# ─────────────────────────────────────────────
# System Threads API (AWP-037)
# ─────────────────────────────────────────────
@app.get("/system/threads", tags=["System"])
async def system_threads() -> dict:
    try:
        import psutil  # type: ignore
        pct = psutil.cpu_percent(percpu=True, interval=0.1)
        # Pad to 32 threads (Ryzen 9 7950X)
        while len(pct) < 32:
            pct.append(0.0)
        return {"threads": pct[:32], "timestamp": __import__("datetime").datetime.utcnow().isoformat()}
    except ImportError:
        from datetime import datetime
        return {"threads": [0.0] * 32, "timestamp": datetime.utcnow().isoformat(),
                "note": "psutil not installed"}


# ─────────────────────────────────────────────
# Agent dispatch endpoints (AWP-035)
# ─────────────────────────────────────────────
class AgentTaskRequest(BaseModel):
    file: str | None = None
    content: str | None = None

@app.post("/agent/{agent_name}", tags=["Agents"])
async def dispatch_agent(agent_name: str, req: AgentTaskRequest) -> dict:
    ALLOWED = {"refactor", "test", "security", "overdrive", "coder"}
    if agent_name not in ALLOWED:
        raise HTTPException(400, f"Unknown agent: {agent_name!r}")
    log.info("Agent dispatch: @%s file=%s", agent_name, req.file)
    try:
        from agents.orchestrator import Orchestrator  # type: ignore
        orch = Orchestrator()
        result = await orch.dispatch(agent_name, file=req.file, content=req.content)
        return {"status": "ok", "agent": agent_name, "result": result}
    except Exception as exc:
        log.error("Agent %s error: %s", agent_name, exc, exc_info=True)
        raise HTTPException(500, str(exc)) from exc


# ─────────────────────────────────────────────
# AWP-102/105/106/110 – Knowledge Ingestion Endpoints
# ─────────────────────────────────────────────
UPLOADS_DIR = Path(__file__).parent.parent / "data" / "uploads"
REGISTRY_FILE = UPLOADS_DIR / "registry.json"


def _load_registry() -> list[dict]:
    if not REGISTRY_FILE.exists():
        return []
    try:
        return json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save_registry(docs: list[dict]) -> None:
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    REGISTRY_FILE.write_text(json.dumps(docs, indent=2, ensure_ascii=False),
                              encoding="utf-8")


@app.post("/ingest/upload", tags=["Ingest"])
async def ingest_upload(file: UploadFile = File(...)) -> dict[str, Any]:
    """
    AWP-102: Nimmt PDF, MD oder TXT entgegen.
    AWP-103: Parst mit parser_logic (PyMuPDF für PDFs).
    AWP-104: Chunked in ~500-Token-Blöcke (10% Overlap).
    AWP-105/106: Embedding via ProcessPoolExecutor + Upsert in Qdrant/ChromaDB.
    """
    allowed_ext = {".pdf", ".md", ".txt"}
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in allowed_ext:
        raise HTTPException(400, f"Nicht unterstützt: {suffix}. Erlaubt: {allowed_ext}")

    max_bytes = MAX_UPLOAD_MB * 1024 * 1024
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    save_path = UPLOADS_DIR / (file.filename or "upload")

    # ── Empfang ────────────────────────────────
    total = 0
    try:
        with save_path.open("wb") as f:
            chunk_size = 1024 * 1024
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    save_path.unlink(missing_ok=True)
                    raise HTTPException(413, f"Datei zu groß. Max {MAX_UPLOAD_MB}MB.")
                f.write(chunk)
    except HTTPException:
        raise
    except Exception as exc:
        save_path.unlink(missing_ok=True)
        raise HTTPException(500, f"Empfangsfehler: {exc}") from exc

    log.info("Ingest upload received: %s (%.1f MB)", file.filename, total / 1024 / 1024)

    # ── Parse (AWP-103) ────────────────────────
    try:
        from parser_logic import parse_document, chunk_document  # type: ignore
        parsed = parse_document(save_path)
    except Exception as exc:
        log.error("Parser error: %s", exc, exc_info=True)
        raise HTTPException(500, f"Parse-Fehler: {exc}") from exc

    # ── Chunk (AWP-104) ────────────────────────
    chunks = chunk_document(parsed)
    if not chunks:
        return {"status": "empty", "filename": file.filename, "chunks": 0}

    # ── Embed + Upsert (AWP-105/106) ──────────────────────────────────────────
    # embed_async läuft im ThreadPool (kein Fork → kein Socket-Kill bei Qdrant/Chroma).
    # memory.upsert() embedded intern, kein doppeltes Embedding nötig.
    from memory_interface import Document, get_memory  # type: ignore
    import datetime as _dt

    ts = _dt.datetime.utcnow().isoformat()
    docs = [
        Document(
            doc_id=f"{c.source_file}::chunk_{c.chunk_index}",
            text=c.text,
            metadata={
                "source": c.source_file,
                "filename": file.filename,
                "chunk_index": c.chunk_index,
                "uploaded_at": ts,
            },
        )
        for c in chunks
    ]
    totals = await get_memory().upsert(docs)

    # ── Registry updaten ───────────────────────
    registry = _load_registry()
    registry = [r for r in registry if r.get("filename") != file.filename]
    registry.append({
        "filename": file.filename,
        "source_id": parsed.source_id,
        "uploaded_at": ts,
        "chunks": len(chunks),
        "size_mb": round(total / 1024 / 1024, 2),
        "pages": parsed.page_count,
    })
    _save_registry(registry)

    log.info("Ingest complete: %s → %d chunks, %s", file.filename, len(chunks), totals)
    return {
        "status": "ok",
        "filename": file.filename,
        "size_mb": round(total / 1024 / 1024, 2),
        "pages": parsed.page_count,
        "chunks": len(chunks),
        "vectors": totals,
    }


@app.get("/ingest/documents", tags=["Ingest"])
async def list_ingest_documents() -> list[dict]:
    """AWP-110: Listet alle hochgeladenen Dokumente aus dem Registry."""
    return _load_registry()


@app.delete("/ingest/document", tags=["Ingest"])
async def delete_ingest_document(filename: str) -> dict[str, Any]:
    """AWP-110: Entfernt ein Dokument vollständig aus Qdrant + ChromaDB + Registry."""
    registry = _load_registry()
    entry = next((r for r in registry if r.get("filename") == filename), None)
    if not entry:
        raise HTTPException(404, f"Dokument nicht gefunden: {filename!r}")

    source_id = entry.get("source_id", f"upload::{filename}")
    log.info("Delete ingest document: %s (source=%s)", filename, source_id)

    try:
        from memory_interface import get_memory  # type: ignore
        result = await get_memory().delete_by_source(source_id)
    except Exception as exc:
        log.error("Delete error: %s", exc, exc_info=True)
        raise HTTPException(500, f"Lösch-Fehler: {exc}") from exc

    # Datei aus uploads löschen
    upload_file = UPLOADS_DIR / filename
    upload_file.unlink(missing_ok=True)

    # Registry aktualisieren
    _save_registry([r for r in registry if r.get("filename") != filename])

    return {"status": "deleted", "filename": filename, "vectors": result}


# ─────────────────────────────────────────────
# AWP-102/104/105/108/109 – Chat Session Upload
# In-Memory-Store: Text sofort verfügbar, RAG im Hintergrund
# ─────────────────────────────────────────────
SESSION_DIR = Path(__file__).parent.parent / "data" / "session_files"

# In-memory Session-Store (wird bei Container-Neustart geleert)
_SESSION: dict[str, dict[str, Any]] = {}   # filename → metadata + text

# AWP-@security: Prompt-Injection & Shell-Escape Patterns
_INJECTION_PATTERNS = [
    r"ignore\s+previous\s+instructions",
    r"disregard\s+your\s+instructions",
    r"new\s+system\s+prompt",
    r"<\s*script[\s>\/]",
    r"eval\s*\(",
    r"exec\s*\(",
    r"__import__\s*\(",
    r"subprocess\.",
    r"os\.system\s*\(",
]


def _security_scan(text: str) -> list[str]:
    """AWP @security: Scannt auf Prompt-Injection und Shell-Command-Patterns."""
    found = []
    probe = text[:8000]
    for p in _INJECTION_PATTERNS:
        if _re.search(p, probe, flags=_re.IGNORECASE):
            found.append(p)
    return found


async def _background_rag_index(text: str, filename: str, source_id: str) -> None:
    """AWP-108: Nicht-blockierendes RAG-Embedding via FastAPI BackgroundTask."""
    try:
        from parser_logic import ParsedDocument, chunk_document  # type: ignore
        from memory_interface import Document, get_memory        # type: ignore
        import datetime as _dt

        parsed = ParsedDocument(
            filename=filename,
            source_id=source_id,
            text_by_page=[text],
            page_count=1,
            size_bytes=len(text.encode()),
        )
        chunks = chunk_document(parsed)
        if not chunks:
            return

        ts = _dt.datetime.utcnow().isoformat()
        docs = [
            Document(
                doc_id=f"{c.source_file}::chunk_{c.chunk_index}",
                text=c.text,
                metadata={
                    "source": c.source_file,
                    "filename": filename,
                    "chunk_index": c.chunk_index,
                    "uploaded_at": ts,
                    "tag": "session_upload",   # AWP-104
                },
            )
            for c in chunks
        ]
        await get_memory().upsert(docs)
        log.info("Session RAG complete: %s → %d chunks", filename, len(docs))
    except Exception as exc:
        log.error("Background RAG index error for %s: %s", filename, exc)


@app.post("/chat/upload", tags=["Chat"])
async def chat_upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
) -> dict[str, Any]:
    """
    AWP-102: Lädt Datei hoch, extrahiert sofort Text → sofortige Response.
    AWP-104: Session-Store mit tag='session_upload'.
    AWP-108: RAG-Indizierung via BackgroundTask (non-blocking).
    AWP-@security: Prüft auf Injection-Patterns vor der Speicherung.
    """
    allowed_ext = {".pdf", ".md", ".txt"}
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in allowed_ext:
        raise HTTPException(400, f"Nicht unterstützt: {suffix}. Erlaubt: {allowed_ext}")

    max_bytes = MAX_UPLOAD_MB * 1024 * 1024
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    save_path = SESSION_DIR / (file.filename or "upload")

    # Datei speichern
    total = 0
    try:
        with save_path.open("wb") as fh:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    save_path.unlink(missing_ok=True)
                    raise HTTPException(413, f"Max {MAX_UPLOAD_MB}MB überschritten.")
                fh.write(chunk)
    except HTTPException:
        raise
    except Exception as exc:
        save_path.unlink(missing_ok=True)
        raise HTTPException(500, f"Empfangsfehler: {exc}") from exc

    # AWP-103: Text extrahieren
    try:
        from parser_logic import parse_document  # type: ignore
        parsed = parse_document(save_path)
        full_text = "\n\n".join(parsed.text_by_page)
    except Exception as exc:
        save_path.unlink(missing_ok=True)
        raise HTTPException(500, f"Parse-Fehler: {exc}") from exc

    if not full_text.strip():
        return {"status": "empty", "filename": file.filename, "pages": 0, "chars": 0}

    # AWP-@security: Scan bevor irgend etwas gespeichert wird
    threats = _security_scan(full_text)
    if threats:
        log.warning("Security BLOCK: %s — Patterns: %s", file.filename, threats)
        save_path.unlink(missing_ok=True)
        raise HTTPException(
            422,
            f"Datei abgelehnt — @security hat verdächtige Muster gefunden: {threats}",
        )

    # AWP-104/105: Im Session-Store ablegen (direkte System-Prompt-Injektion)
    import datetime as _dt
    ts = _dt.datetime.utcnow().isoformat()
    source_id = f"session::{file.filename}"
    _SESSION[file.filename] = {
        "filename":   file.filename,
        "source_id":  source_id,
        "text":       full_text[:16000],  # max 16K Zeichen für Context-Window
        "pages":      parsed.page_count,
        "size_mb":    round(total / 1024 / 1024, 2),
        "chars":      len(full_text),
        "uploaded_at": ts,
    }

    # AWP-108: RAG im Hintergrund — Response ist bereits draußen
    background_tasks.add_task(_background_rag_index, full_text, file.filename, source_id)

    log.info("Chat upload OK: %s (%.1fMB, %d chars) → session+RAG(bg)",
             file.filename, total / 1024 / 1024, len(full_text))
    return {
        "status":   "ok",
        "filename": file.filename,
        "pages":    parsed.page_count,
        "size_mb":  round(total / 1024 / 1024, 2),
        "chars":    len(full_text),
        "preview":  full_text[:300].replace("\n", " "),
    }


@app.get("/chat/session-files", tags=["Chat"])
async def list_session_files() -> list[dict]:
    """AWP-105/109: Aktive Session-Dateien (ohne vollen Text)."""
    return [
        {k: v for k, v in entry.items() if k != "text"}
        for entry in _SESSION.values()
    ]


@app.get("/chat/session-context", tags=["Chat"])
async def get_session_context() -> dict[str, Any]:
    """AWP-105: Kombinierten Session-Text für System-Prompt-Injektion."""
    if not _SESSION:
        return {"context": "", "files": []}
    parts = [
        f"[Session-Datei: {e['filename']} | {e['pages']} Seite(n) | {e['chars']} Zeichen]\n{e['text']}"
        for e in _SESSION.values()
    ]
    return {
        "context": "\n\n---\n\n".join(parts),
        "files":   [e["filename"] for e in _SESSION.values()],
    }


@app.delete("/chat/clear-session", tags=["Chat"])
async def clear_session() -> dict[str, Any]:
    """AWP-109: Löscht alle Session-Dateien aus Memory und Disk."""
    filenames = list(_SESSION.keys())
    _SESSION.clear()
    deleted = 0
    for name in filenames:
        p = SESSION_DIR / name
        if p.exists():
            p.unlink(missing_ok=True)
            deleted += 1
    log.info("Session cleared: %d Dateien", len(filenames))
    return {"status": "cleared", "files_removed": len(filenames), "disk_deleted": deleted}


# ─────────────────────────────────────────────
# TTS endpoint – Thorsten via Piper (AWP-054)
# ─────────────────────────────────────────────

class TTSRequest(BaseModel):
    text: str = Field(..., max_length=2000)

@app.post("/tts", tags=["TTS"])
async def text_to_speech(req: TTSRequest) -> StreamingResponse:
    """Convert text to speech using Piper (Thorsten de_DE-thorsten-high).
    Returns WAV audio stream.
    """
    text = req.text.strip()
    if not text:
        raise HTTPException(400, "text must not be empty")

    piper_path = Path(os.environ.get("PIPER_PATH", "piper"))
    model_path = Path(os.environ.get(
        "PIPER_MODEL",
        str(Path(__file__).parent.parent / "models" / "de_DE-thorsten-high.onnx"),
    ))

    if not model_path.exists():
        raise HTTPException(503, f"Piper model not found: {model_path}")

    try:
        proc = await asyncio.create_subprocess_exec(
            str(piper_path),
            "--model", str(model_path),
            "--output-raw",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        raw_audio, _ = await proc.communicate(input=text.encode("utf-8"))
    except FileNotFoundError as exc:
        raise HTTPException(503, f"Piper not found at {piper_path}") from exc
    except Exception as exc:
        log.error("TTS error: %s", exc, exc_info=True)
        raise HTTPException(500, str(exc)) from exc

    # Wrap raw PCM (s16le 22050 Hz mono) in a minimal WAV container
    import struct
    sample_rate = 22050
    num_channels = 1
    bits_per_sample = 16
    byte_rate = sample_rate * num_channels * bits_per_sample // 8
    block_align = num_channels * bits_per_sample // 8
    data_size = len(raw_audio)
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF", 36 + data_size, b"WAVE",
        b"fmt ", 16, 1, num_channels,
        sample_rate, byte_rate, block_align, bits_per_sample,
        b"data", data_size,
    )
    wav_bytes = header + raw_audio

    log.info("TTS: %d chars → %d bytes WAV (Thorsten)", len(text), len(wav_bytes))
    return StreamingResponse(
        iter([wav_bytes]),
        media_type="audio/wav",
        headers={"Content-Length": str(len(wav_bytes))},
    )


# ─────────────────────────────────────────────
# Dev entry point
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("CORE_API_PORT", "8000"))
    uvicorn.run("api_main:app", host="127.0.0.1", port=port,
                reload=False, log_level="info")
