"""
Jarvis 4.0 – Memory Interface
Verbindung zu Qdrant (primär) und ChromaDB (Keyword-Fallback).
AWP-012: Connection  |  AWP-014: Similarity Search
Python 3.12 | AsyncIO | RB-Protokoll: Transparenz + Revidierbarkeit
"""

from __future__ import annotations

import asyncio
import logging
import os
import uuid
from dataclasses import dataclass
from typing import Any

log = logging.getLogger("jarvis.memory")

# ─────────────────────────────────────────────
# Config from environment (no hardcoded values)
# ─────────────────────────────────────────────
QDRANT_HOST = os.environ.get("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.environ.get("QDRANT_PORT", "6333"))
QDRANT_COLLECTION = os.environ.get("QDRANT_COLLECTION", "jarvis_knowledge")

CHROMA_HOST = os.environ.get("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.environ.get("CHROMA_PORT", "8001"))

EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "bge-small-en-v1.5")
VECTOR_DIM = 384  # fixed for bge-small-en-v1.5


# ─────────────────────────────────────────────
# Data models
# ─────────────────────────────────────────────
@dataclass
class Document:
    """A document chunk ready for upsert / returned from search."""
    doc_id: str
    text: str
    metadata: dict[str, Any]
    score: float = 0.0          # populated on search results

    @classmethod
    def from_text(cls, text: str, metadata: dict[str, Any]) -> "Document":
        return cls(doc_id=str(uuid.uuid4()), text=text, metadata=metadata)


@dataclass
class SearchResult:
    """Hybrid search result with provenance."""
    document: Document
    source: str                 # "qdrant" | "chroma"
    score: float


# ─────────────────────────────────────────────
# Embedding helper (lazy import)
# ─────────────────────────────────────────────
_encoder: Any | None = None


def _get_encoder() -> Any:
    global _encoder
    if _encoder is None:
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
            _encoder = SentenceTransformer(EMBEDDING_MODEL)
            log.info("Embedding model loaded: %s", EMBEDDING_MODEL)
        except ImportError as exc:
            raise RuntimeError(
                "sentence-transformers not installed. "
                "Run: pip install sentence-transformers"
            ) from exc
    return _encoder


def embed(text: str) -> list[float]:
    """Embed a single text string. Blocking (use run_in_executor for async)."""
    encoder = _get_encoder()
    vector = encoder.encode(text, normalize_embeddings=True)
    return vector.tolist()


async def embed_async(text: str) -> list[float]:
    """Non-blocking embed via thread pool (keeps AsyncIO event loop free)."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, embed, text)


# ─────────────────────────────────────────────
# Qdrant Client (lazy import)
# ─────────────────────────────────────────────
class QdrantMemory:
    """Async wrapper around qdrant-client for Jarvis."""

    def __init__(self) -> None:
        self._client: Any | None = None

    def _ensure_client(self) -> Any:
        if self._client is None:
            try:
                from qdrant_client import QdrantClient  # type: ignore
                from qdrant_client.models import (  # type: ignore
                    Distance, VectorParams
                )
                self._client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
                self._ensure_collection()
                log.info("Qdrant connected: %s:%d", QDRANT_HOST, QDRANT_PORT)
            except ImportError as exc:
                raise RuntimeError(
                    "qdrant-client not installed. Run: pip install qdrant-client"
                ) from exc
        return self._client

    def _ensure_collection(self) -> None:
        from qdrant_client.models import Distance, VectorParams  # type: ignore
        client = self._client
        existing = [c.name for c in client.get_collections().collections]
        if QDRANT_COLLECTION not in existing:
            client.create_collection(
                collection_name=QDRANT_COLLECTION,
                vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE),
            )
            log.info("Created Qdrant collection: %s", QDRANT_COLLECTION)

    async def upsert(self, documents: list[Document]) -> int:
        """Embed and upsert documents. Returns count inserted."""
        if not documents:
            return 0
        client = self._ensure_client()
        from qdrant_client.models import PointStruct  # type: ignore

        loop = asyncio.get_event_loop()
        points = []
        for doc in documents:
            vector = await embed_async(doc.text)
            points.append(PointStruct(
                id=doc.doc_id,
                vector=vector,
                payload={**doc.metadata, "text": doc.text},
            ))

        await loop.run_in_executor(
            None,
            lambda: client.upsert(collection_name=QDRANT_COLLECTION, points=points),
        )
        log.info("Qdrant upsert: %d documents", len(points))
        return len(points)

    async def search(
        self, query: str, top_k: int = 5, score_threshold: float = 0.5
    ) -> list[SearchResult]:
        """Semantic similarity search."""
        client = self._ensure_client()
        query_vector = await embed_async(query)

        loop = asyncio.get_event_loop()
        hits = await loop.run_in_executor(
            None,
            lambda: client.search(
                collection_name=QDRANT_COLLECTION,
                query_vector=query_vector,
                limit=top_k,
                score_threshold=score_threshold,
            ),
        )

        results = []
        for hit in hits:
            payload = hit.payload or {}
            text = payload.pop("text", "")
            doc = Document(doc_id=str(hit.id), text=text, metadata=payload,
                           score=hit.score)
            results.append(SearchResult(document=doc, source="qdrant",
                                        score=hit.score))

        log.info("Qdrant search '%s': %d results", query[:50], len(results))
        return results

    def health(self) -> bool:
        try:
            self._ensure_client()
            return True
        except Exception:
            return False


# ─────────────────────────────────────────────
# ChromaDB Client (keyword fallback)
# ─────────────────────────────────────────────
class ChromaMemory:
    """Thin wrapper around chromadb HttpClient for keyword search."""

    def __init__(self) -> None:
        self._client: Any | None = None
        self._collection: Any | None = None

    def _ensure_client(self) -> Any:
        if self._client is None:
            try:
                import chromadb  # type: ignore
                self._client = chromadb.HttpClient(
                    host=CHROMA_HOST, port=CHROMA_PORT
                )
                self._collection = self._client.get_or_create_collection(
                    name="jarvis_documents",
                    metadata={"hnsw:space": "cosine"},
                )
                log.info("ChromaDB connected: %s:%d", CHROMA_HOST, CHROMA_PORT)
            except ImportError as exc:
                raise RuntimeError(
                    "chromadb not installed. Run: pip install chromadb"
                ) from exc
        return self._client

    async def upsert(self, documents: list[Document]) -> int:
        if not documents:
            return 0
        self._ensure_client()
        col = self._collection
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: col.upsert(
                ids=[d.doc_id for d in documents],
                documents=[d.text for d in documents],
                metadatas=[d.metadata for d in documents],
            ),
        )
        log.info("ChromaDB upsert: %d documents", len(documents))
        return len(documents)

    async def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        self._ensure_client()
        col = self._collection
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            lambda: col.query(query_texts=[query], n_results=top_k),
        )
        output = []
        ids = results.get("ids", [[]])[0]
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for doc_id, text, meta, dist in zip(ids, docs, metas, distances):
            score = 1.0 - dist  # cosine distance → similarity
            doc = Document(doc_id=doc_id, text=text, metadata=meta or {},
                           score=score)
            output.append(SearchResult(document=doc, source="chroma",
                                       score=score))

        log.info("ChromaDB search '%s': %d results", query[:50], len(output))
        return output

    def health(self) -> bool:
        try:
            self._ensure_client()
            return True
        except Exception:
            return False


# ─────────────────────────────────────────────
# Unified Memory Interface (Hybrid Search)
# AWP-014: Similarity Search
# ─────────────────────────────────────────────
class JarvisMemory:
    """
    Unified facade over Qdrant (semantic) + ChromaDB (keyword).
    Hybrid search merges both result sets, deduplicates, and re-ranks by score.
    """

    def __init__(self) -> None:
        self.qdrant = QdrantMemory()
        self.chroma = ChromaMemory()

    async def upsert(self, documents: list[Document]) -> dict[str, int]:
        """Upsert into both backends simultaneously."""
        qdrant_count, chroma_count = await asyncio.gather(
            self.qdrant.upsert(documents),
            self.chroma.upsert(documents),
        )
        return {"qdrant": qdrant_count, "chroma": chroma_count}

    async def search(
        self,
        query: str,
        top_k: int = 5,
        mode: str = "hybrid",       # "semantic" | "keyword" | "hybrid"
        score_threshold: float = 0.3,
    ) -> list[SearchResult]:
        """
        Hybrid search: combine semantic (Qdrant) + keyword (ChromaDB).
        Deduplicates by doc_id, re-ranks by score descending.
        Transparency: logs source and score for each result (RB-Protokoll).
        """
        if mode == "semantic":
            results = await self.qdrant.search(query, top_k, score_threshold)
        elif mode == "keyword":
            results = await self.chroma.search(query, top_k)
        else:  # hybrid
            qdrant_results, chroma_results = await asyncio.gather(
                self.qdrant.search(query, top_k, score_threshold),
                self.chroma.search(query, top_k),
            )
            # Merge + deduplicate (prefer higher score)
            seen: dict[str, SearchResult] = {}
            for r in qdrant_results + chroma_results:
                existing = seen.get(r.document.doc_id)
                if existing is None or r.score > existing.score:
                    seen[r.document.doc_id] = r
            results = sorted(seen.values(), key=lambda r: r.score, reverse=True)[:top_k]

        # Glass-Box transparency log
        for i, r in enumerate(results):
            log.info(
                "  [%d] source=%-8s score=%.3f id=%s text=%.60s…",
                i + 1, r.source, r.score,
                r.document.doc_id[:8],
                r.document.text.replace("\n", " "),
            )
        return results

    def health(self) -> dict[str, bool]:
        return {
            "qdrant": self.qdrant.health(),
            "chroma": self.chroma.health(),
        }


# ─────────────────────────────────────────────
# Module-level singleton
# ─────────────────────────────────────────────
_memory: JarvisMemory | None = None


def get_memory() -> JarvisMemory:
    global _memory
    if _memory is None:
        _memory = JarvisMemory()
    return _memory
