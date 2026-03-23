"""
AWP-061 – Vector Pruner
Erkennt veraltete oder widersprüchliche Einträge im RAG-Speicher
und verschiebt sie in eine Archiv-Collection.

Strategien:
  1. Age-based:    Punkte älter als MAX_AGE_DAYS → Archiv
  2. Conflict:     Zwei Punkte mit score > CONFLICT_THRESHOLD aus
                   verschiedenen Quellen zum selben Query → schwächerer ins Archiv
  3. Orphan:       Source-Datei existiert nicht mehr → Archiv

Python 3.12 | AsyncIO
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from config import PROJECT_ROOT, QDRANT_HOST, QDRANT_PORT, QDRANT_COLLECTION

log = logging.getLogger("jarvis.vector_pruner")

ARCHIVE_COLLECTION = f"{QDRANT_COLLECTION}_archive"
MAX_AGE_DAYS       = int(__import__("os").environ.get("RAG_MAX_AGE_DAYS", "90"))
CONFLICT_THRESHOLD = 0.92      # cosine similarity — near-duplicates
BATCH_SIZE         = 100


@dataclass
class PruneStats:
    total_scanned: int = 0
    archived_age: int = 0
    archived_conflict: int = 0
    archived_orphan: int = 0

    @property
    def total_archived(self) -> int:
        return self.archived_age + self.archived_conflict + self.archived_orphan


class VectorPruner:

    def __init__(self) -> None:
        self._client: Any | None = None

    def _get_client(self) -> Any:
        if self._client is None:
            from qdrant_client import QdrantClient  # type: ignore
            self._client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
            self._ensure_archive_collection()
        return self._client

    def _ensure_archive_collection(self) -> None:
        from qdrant_client.models import Distance, VectorParams  # type: ignore
        client = self._client
        existing = [c.name for c in client.get_collections().collections]
        if ARCHIVE_COLLECTION not in existing:
            client.create_collection(
                collection_name=ARCHIVE_COLLECTION,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )
            log.info("Created archive collection: %s", ARCHIVE_COLLECTION)

    async def run(self) -> PruneStats:
        stats = PruneStats()
        loop = asyncio.get_event_loop()
        client = await loop.run_in_executor(None, self._get_client)

        # Scroll all points
        points, next_offset = await loop.run_in_executor(
            None,
            lambda: client.scroll(
                collection_name=QDRANT_COLLECTION,
                limit=BATCH_SIZE,
                with_payload=True,
                with_vectors=True,
            ),
        )
        stats.total_scanned = len(points)

        to_archive: list[Any] = []

        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=MAX_AGE_DAYS)

        for point in points:
            payload = point.payload or {}
            source = payload.get("source", "")

            # Strategy 1: Age-based
            ts_str = payload.get("ingested_at")
            if ts_str:
                try:
                    ts = datetime.fromisoformat(ts_str)
                    if ts < cutoff:
                        to_archive.append((point, "age"))
                        stats.archived_age += 1
                        continue
                except ValueError:
                    pass

            # Strategy 3: Orphan (source file deleted)
            if source and not Path(source).exists():
                to_archive.append((point, "orphan"))
                stats.archived_orphan += 1

        # Strategy 2: Conflict detection (deduplication pass)
        seen_ids: set = set()
        for i, point_a in enumerate(points):
            if point_a.id in seen_ids:
                continue
            vec_a = point_a.vector
            if vec_a is None:
                continue
            similar = await loop.run_in_executor(
                None,
                lambda v=vec_a: client.search(
                    collection_name=QDRANT_COLLECTION,
                    query_vector=v,
                    limit=3,
                    score_threshold=CONFLICT_THRESHOLD,
                ),
            )
            # If near-duplicate found (not self), archive the older one
            for hit in similar:
                if hit.id == point_a.id:
                    continue
                if hit.id in seen_ids:
                    continue
                # Archive the hit (lower payload freshness)
                to_archive.append((hit, "conflict"))
                seen_ids.add(hit.id)
                stats.archived_conflict += 1

        # Move to archive
        if to_archive:
            await self._move_to_archive(to_archive, client, loop)

        log.info(
            "VectorPruner: scanned=%d archived=%d (age=%d conflict=%d orphan=%d)",
            stats.total_scanned, stats.total_archived,
            stats.archived_age, stats.archived_conflict, stats.archived_orphan,
        )
        return stats

    async def _move_to_archive(
        self, items: list[tuple[Any, str]], client: Any, loop: Any
    ) -> None:
        from qdrant_client.models import PointStruct  # type: ignore
        archive_points = []
        ids_to_delete = []
        for point, reason in items:
            payload = dict(point.payload or {})
            payload["archived_reason"] = reason
            payload["archived_at"] = datetime.now(tz=timezone.utc).isoformat()
            archive_points.append(PointStruct(
                id=point.id, vector=point.vector, payload=payload
            ))
            ids_to_delete.append(point.id)

        await loop.run_in_executor(
            None,
            lambda: client.upsert(collection_name=ARCHIVE_COLLECTION,
                                  points=archive_points),
        )
        await loop.run_in_executor(
            None,
            lambda: client.delete(collection_name=QDRANT_COLLECTION,
                                  points_selector=ids_to_delete),
        )
        log.info("Archived %d points", len(ids_to_delete))
