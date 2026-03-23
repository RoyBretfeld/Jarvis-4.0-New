"""
Jarvis 4.0 – Document Ingestion Script
Liest alle .md-Dateien aus /strategy/, chunked sie und lädt sie in die Vektor-DB.
AWP-013: Ingestion  |  AWP-018: Multiprocessing-Optimierung (Ryzen 9 7950X)

Architektur (refactor_logic_v1 angewandt):
  - SOLID: Jede Klasse hat eine einzige Verantwortung.
  - DRY:   Chunking und Embedding sind getrennte, wiederverwendbare Module.
  - Ryzen: Embedding-Phase nutzt ProcessPoolExecutor (Threads 4-7 via cpuset).
Python 3.12 | AsyncIO + Multiprocessing
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger("jarvis.ingest")

CHUNK_SIZE = int(os.environ.get("RAG_CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.environ.get("RAG_CHUNK_OVERLAP", "100"))
# Nutze Threads 4-7 (cpuset) für Embedding-Parallelisierung
EMBED_WORKERS = int(os.environ.get("EMBED_WORKERS", "4"))
BATCH_SIZE = int(os.environ.get("INGEST_BATCH_SIZE", "32"))


# ─────────────────────────────────────────────
# Text Chunker (Single Responsibility)
# ─────────────────────────────────────────────
@dataclass
class TextChunk:
    text: str
    source_file: str
    chunk_index: int
    char_start: int
    char_end: int


class MarkdownChunker:
    """Splits Markdown into overlapping token-aware chunks."""

    def __init__(self, chunk_size: int = CHUNK_SIZE,
                 overlap: int = CHUNK_OVERLAP) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def _token_count(self, text: str) -> int:
        # Approximation: 1 token ≈ 4 chars (English/German mixed)
        return len(text) // 4

    def _strip_frontmatter(self, text: str) -> str:
        return re.sub(r"^---\s*\n.*?\n---\s*\n", "", text, flags=re.DOTALL)

    def chunk(self, text: str, source: str) -> list[TextChunk]:
        """Split text into overlapping chunks by approximate token count."""
        clean = self._strip_frontmatter(text).strip()
        if not clean:
            return []

        # Split on paragraph boundaries first (better semantic coherence)
        paragraphs = re.split(r"\n\n+", clean)
        chunks: list[TextChunk] = []
        current_parts: list[str] = []
        current_tokens = 0
        char_cursor = 0

        for para in paragraphs:
            para_tokens = self._token_count(para)

            if current_tokens + para_tokens > self.chunk_size and current_parts:
                chunk_text = "\n\n".join(current_parts)
                start = char_cursor - len(chunk_text)
                chunks.append(TextChunk(
                    text=chunk_text,
                    source_file=source,
                    chunk_index=len(chunks),
                    char_start=max(0, start),
                    char_end=char_cursor,
                ))
                # Overlap: keep last paragraph
                overlap_parts = current_parts[-1:]
                current_parts = overlap_parts
                current_tokens = self._token_count("\n\n".join(overlap_parts))

            current_parts.append(para)
            current_tokens += para_tokens
            char_cursor += len(para) + 2

        # Flush remaining
        if current_parts:
            chunk_text = "\n\n".join(current_parts)
            chunks.append(TextChunk(
                text=chunk_text,
                source_file=source,
                chunk_index=len(chunks),
                char_start=max(0, char_cursor - len(chunk_text)),
                char_end=char_cursor,
            ))

        return chunks


# ─────────────────────────────────────────────
# Embedding Worker (runs in subprocess for Multiprocessing)
# Isolated function – must be picklable (top-level)
# ─────────────────────────────────────────────
def _embed_chunk(text: str) -> list[float]:
    """Embed a single text in a worker process (CPU-bound)."""
    from sentence_transformers import SentenceTransformer  # type: ignore
    import os as _os
    model_name = _os.environ.get("EMBEDDING_MODEL", "bge-small-en-v1.5")
    model = SentenceTransformer(model_name)
    return model.encode(text, normalize_embeddings=True).tolist()


# ─────────────────────────────────────────────
# Ingestion Pipeline (orchestrates the above)
# ─────────────────────────────────────────────
class IngestionPipeline:
    """
    Phase 1 – Extraction:  read .md files
    Phase 2 – Chunking:    MarkdownChunker
    Phase 3 – Embedding:   ProcessPoolExecutor (Ryzen Threads 4-7)
    Phase 4 – Upsert:      JarvisMemory
    """

    def __init__(self, docs_dir: Path, workers: int = EMBED_WORKERS) -> None:
        self.docs_dir = docs_dir
        self.workers = workers
        self.chunker = MarkdownChunker()

    # ── Phase 1: Extraction ────────────────────
    def _load_files(self) -> list[tuple[Path, str]]:
        files = sorted(self.docs_dir.glob("**/*.md"))
        result = []
        for f in files:
            try:
                result.append((f, f.read_text(encoding="utf-8")))
            except OSError as exc:
                log.warning("Cannot read %s: %s", f, exc)
        log.info("Extraction: %d .md files loaded from %s", len(result), self.docs_dir)
        return result

    # ── Phase 2: Chunking ──────────────────────
    def _chunk_files(
        self, files: list[tuple[Path, str]]
    ) -> list[TextChunk]:
        all_chunks: list[TextChunk] = []
        for path, text in files:
            chunks = self.chunker.chunk(text, source=str(path))
            all_chunks.extend(chunks)
        log.info("Chunking: %d total chunks (size≈%d tokens, overlap=%d)",
                 len(all_chunks), CHUNK_SIZE, CHUNK_OVERLAP)
        return all_chunks

    # ── Phase 3: Embedding (Multiprocessing) ──
    async def _embed_all(
        self, chunks: list[TextChunk]
    ) -> list[tuple[TextChunk, list[float]]]:
        loop = asyncio.get_event_loop()
        log.info("Embedding: %d chunks using %d workers (Ryzen Threads 4-7)…",
                 len(chunks), self.workers)
        t0 = time.perf_counter()

        with ProcessPoolExecutor(max_workers=self.workers) as pool:
            futures = [
                loop.run_in_executor(pool, _embed_chunk, c.text)
                for c in chunks
            ]
            vectors = await asyncio.gather(*futures)

        elapsed = time.perf_counter() - t0
        log.info("Embedding complete: %.1fs (%.0f chunks/s)",
                 elapsed, len(chunks) / elapsed if elapsed else 0)
        return list(zip(chunks, vectors))

    # ── Phase 4: Upsert ────────────────────────
    async def _upsert_batches(
        self, embedded: list[tuple[TextChunk, list[float]]]
    ) -> dict[str, int]:
        from memory_interface import Document, get_memory  # type: ignore
        memory = get_memory()
        total: dict[str, int] = {"qdrant": 0, "chroma": 0}

        for batch_start in range(0, len(embedded), BATCH_SIZE):
            batch = embedded[batch_start:batch_start + BATCH_SIZE]
            docs = [
                Document(
                    doc_id=f"{chunk.source_file}::chunk_{chunk.chunk_index}",
                    text=chunk.text,
                    metadata={
                        "source": chunk.source_file,
                        "chunk_index": chunk.chunk_index,
                        "char_start": chunk.char_start,
                        "char_end": chunk.char_end,
                    },
                )
                for chunk, _ in batch
            ]
            counts = await memory.upsert(docs)
            for k, v in counts.items():
                total[k] = total.get(k, 0) + v
            log.info(
                "Upsert batch %d-%d: %s",
                batch_start, batch_start + len(batch), counts
            )

        return total

    # ── Orchestrator ───────────────────────────
    async def run(self) -> dict[str, int]:
        log.info("═══ Ingestion Pipeline START ═══")
        files = self._load_files()
        if not files:
            log.warning("No .md files found in %s", self.docs_dir)
            return {}

        chunks = self._chunk_files(files)
        embedded = await self._embed_all(chunks)
        totals = await self._upsert_batches(embedded)

        log.info("═══ Ingestion Pipeline COMPLETE: %s ═══", totals)
        return totals


# ─────────────────────────────────────────────
# CLI entry point
# ─────────────────────────────────────────────
async def main(target_dir: Path) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    pipeline = IngestionPipeline(docs_dir=target_dir)
    totals = await pipeline.run()
    print(f"\nIngestion complete: {totals}")


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else (
        Path(__file__).parent.parent / "strategy"
    )
    asyncio.run(main(target))
