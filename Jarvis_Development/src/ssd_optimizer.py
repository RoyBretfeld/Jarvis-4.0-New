"""
AWP-072 – SSD I/O Optimizer
Bündelt DB-Writes auf E:\ um SSD-Wear zu reduzieren.

Strategie:
  - Pufferung von Write-Ops in einer In-Memory Queue
  - Flush alle FLUSH_INTERVAL Sekunden ODER wenn Buffer >= MAX_BUFFER_SIZE
  - WAL-Mode für alle SQLite-DBs (bereits in decisions.db via aiosqlite)
  - Schreibt Telemetrie in data/io_stats.json

Python 3.12 | AsyncIO
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections import deque
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Awaitable

log = logging.getLogger("jarvis.ssd_optimizer")

FLUSH_INTERVAL   = int(__import__("os").environ.get("SSD_FLUSH_INTERVAL", "5"))   # seconds
MAX_BUFFER_SIZE  = int(__import__("os").environ.get("SSD_MAX_BUFFER",     "50"))  # operations
STATS_PATH       = Path(__file__).parent.parent / "data" / "io_stats.json"


@dataclass
class WriteOp:
    path: str
    content: bytes | str
    mode: str = "text"       # "text" | "binary" | "append"
    encoding: str = "utf-8"
    queued_at: float = field(default_factory=time.monotonic)


@dataclass
class IOStats:
    total_writes: int = 0
    total_flushes: int = 0
    total_bytes: int = 0
    ops_batched: int = 0
    ops_direct: int = 0
    last_flush: str = ""
    avg_batch_size: float = 0.0


class SSDOptimizer:
    """
    Buffered write queue to reduce random I/O on SSD.

    Usage:
        optimizer = SSDOptimizer()
        await optimizer.start()
        await optimizer.write("path/to/file.txt", "content")
        await optimizer.stop()
    """

    def __init__(self) -> None:
        self._queue: deque[WriteOp] = deque()
        self._stats = IOStats()
        self._running = False
        self._flush_task: asyncio.Task | None = None
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        """Start the background flush loop."""
        self._running = True
        self._flush_task = asyncio.create_task(self._flush_loop())
        log.info(
            "SSD optimizer started (flush=%ds, max_buf=%d)",
            FLUSH_INTERVAL, MAX_BUFFER_SIZE,
        )

    async def stop(self) -> None:
        """Flush remaining ops and stop."""
        self._running = False
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        await self._flush_all()
        await self._save_stats()
        log.info("SSD optimizer stopped. Stats: %s", asdict(self._stats))

    async def write(self, path: str | Path, content: str | bytes, mode: str = "text") -> None:
        """Queue a write operation."""
        op = WriteOp(path=str(path), content=content, mode=mode)
        async with self._lock:
            self._queue.append(op)
            if len(self._queue) >= MAX_BUFFER_SIZE:
                await self._flush_all()

    async def write_json(self, path: str | Path, data: Any) -> None:
        """Queue a JSON write."""
        await self.write(path, json.dumps(data, indent=2, ensure_ascii=False))

    async def append(self, path: str | Path, line: str) -> None:
        """Queue an append operation."""
        op = WriteOp(path=str(path), content=line, mode="append")
        async with self._lock:
            self._queue.append(op)

    # ── Internal ───────────────────────────────────────────────────────────

    async def _flush_loop(self) -> None:
        while self._running:
            await asyncio.sleep(FLUSH_INTERVAL)
            async with self._lock:
                if self._queue:
                    await self._flush_all()

    async def _flush_all(self) -> None:
        if not self._queue:
            return

        ops = list(self._queue)
        self._queue.clear()

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._write_batch, ops)

        batch_size = len(ops)
        self._stats.total_writes += batch_size
        self._stats.total_flushes += 1
        self._stats.ops_batched += batch_size
        self._stats.last_flush = datetime.now(tz=timezone.utc).isoformat()
        # Running average
        n = self._stats.total_flushes
        self._stats.avg_batch_size = (
            (self._stats.avg_batch_size * (n - 1) + batch_size) / n
        )
        log.debug("SSD flush: %d ops in batch", batch_size)

    def _write_batch(self, ops: list[WriteOp]) -> None:
        """Synchronous batch write — runs in executor."""
        for op in ops:
            p = Path(op.path)
            p.parent.mkdir(parents=True, exist_ok=True)
            try:
                if op.mode == "binary":
                    assert isinstance(op.content, bytes)
                    p.write_bytes(op.content)
                    self._stats.total_bytes += len(op.content)
                elif op.mode == "append":
                    assert isinstance(op.content, str)
                    with p.open("a", encoding=op.encoding) as f:
                        f.write(op.content)
                    self._stats.total_bytes += len(op.content.encode(op.encoding))
                else:
                    assert isinstance(op.content, str)
                    p.write_text(op.content, encoding=op.encoding)
                    self._stats.total_bytes += len(op.content.encode(op.encoding))
            except OSError as exc:
                log.error("SSD write failed for %s: %s", op.path, exc)

    async def _save_stats(self) -> None:
        STATS_PATH.parent.mkdir(parents=True, exist_ok=True)
        data = asdict(self._stats)
        data["saved_at"] = datetime.now(tz=timezone.utc).isoformat()
        STATS_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


# Module-level singleton
_optimizer: SSDOptimizer | None = None


async def get_optimizer() -> SSDOptimizer:
    """Return the global SSDOptimizer, starting it if needed."""
    global _optimizer
    if _optimizer is None:
        _optimizer = SSDOptimizer()
        await _optimizer.start()
    return _optimizer


async def buffered_write(path: str | Path, content: str) -> None:
    """Convenience: write via global optimizer."""
    opt = await get_optimizer()
    await opt.write(path, content)
