"""
Jarvis 4.0 – Coder Agent (@coder)
AWP-032: Filesystem write with backup
AWP-043: Memory-Recall-Loop — RAG search before every code change
RB-Protokoll: Revidierbarkeit + Transparenz
"""

from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .base_agent import AgentResult, AgentRole, BaseAgent


class CoderAgent(BaseAgent):
    role = AgentRole.CODER

    async def execute(
        self,
        file: str | None = None,
        content: str | None = None,
        operation: str = "write",   # "write" | "refactor" | "create"
        skip_rag: bool = False,
        **_: Any,
    ) -> AgentResult:
        if not file:
            return self._fail("No file specified")

        target = self._safe_path(file)

        # ── AWP-043: Memory-Recall-Loop ───────
        rag_context: list[dict] = []
        if not skip_rag and content:
            rag_context = await self._recall_similar(content, file)

        if operation == "write":
            return await self._write(target, content or "", rag_context)
        if operation == "refactor":
            return await self._refactor(target, content, rag_context)
        if operation == "create":
            return await self._create(target, content or "")
        return self._fail(f"Unknown operation: {operation!r}")

    # ── AWP-043: RAG recall ───────────────────
    async def _recall_similar(
        self, content: str, filename: str
    ) -> list[dict]:
        """Query RAG for similar existing solutions before writing."""
        try:
            import sys
            sys.path.insert(0, str(self._project_root / "src"))
            from memory_interface import get_memory  # type: ignore

            # Use first 300 chars as query (function signatures / class names)
            query = content[:300].strip()
            results = await get_memory().search(
                query=query, top_k=3, mode="hybrid", score_threshold=0.5
            )
            if results:
                self.log.info(
                    "@coder RAG recall: %d similar chunks found for %s",
                    len(results), filename,
                )
            return [
                {
                    "source": r.document.metadata.get("source", "?"),
                    "score": r.score,
                    "snippet": r.document.text[:200],
                }
                for r in results
            ]
        except Exception as exc:
            self.log.warning("@coder RAG recall skipped: %s", exc)
            return []

    # ── File operations ───────────────────────
    async def _write(
        self, path: Path, content: str, rag_context: list[dict]
    ) -> AgentResult:
        backup_path: Path | None = None
        if path.exists():
            backup_path = self._backup(path)

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        self.log.info(
            "@coder WRITE %s (%d chars, backup=%s, rag_hits=%d)",
            path.name, len(content),
            backup_path.name if backup_path else "none",
            len(rag_context),
        )
        return self._ok(
            f"Written {len(content)} chars to {path.name}",
            backup=str(backup_path) if backup_path else None,
            rag_context=rag_context,
        )

    async def _create(self, path: Path, content: str) -> AgentResult:
        if path.exists():
            return self._fail(
                f"File already exists: {path}. Use 'write' to overwrite."
            )
        return await self._write(path, content, [])

    async def _refactor(
        self, path: Path, new_content: str | None, rag_context: list[dict]
    ) -> AgentResult:
        if not path.exists():
            return self._fail(f"File not found: {path}")
        if new_content is None:
            return self._fail("No refactored content provided")
        old = path.read_text(encoding="utf-8")
        diff = self._unified_diff(old, new_content, str(path))
        result = await self._write(path, new_content, rag_context)
        result.metadata["diff"] = diff
        result.output = f"Refactored {path.name}: {len(diff.splitlines())} diff lines"
        return result

    def _backup(self, path: Path) -> Path:
        ts = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%S")
        backup_dir = self._project_root / "logs" / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        dest = backup_dir / f"{path.stem}_{ts}{path.suffix}"
        shutil.copy2(path, dest)
        return dest

    @staticmethod
    def _unified_diff(old: str, new: str, filename: str) -> str:
        import difflib
        return "".join(difflib.unified_diff(
            old.splitlines(keepends=True),
            new.splitlines(keepends=True),
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
        ))
