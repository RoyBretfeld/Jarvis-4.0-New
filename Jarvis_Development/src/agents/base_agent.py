"""
AWP-031 – Base Agent  (updated AWP-081: Git-Checkpointing + AWP-083: Reasoning-Log)
Abstrakte Basisklasse für alle Jarvis-Agenten.
Rollen: @coder, @tester, @security

AWP-081: pre_awp_checkpoint() creates a git commit "PRE-AWP: [id]" before any AWP.
AWP-083: log_reasoning() writes 3-sentence strategy to logs/reasoning.log
         before any write_file call.

Python 3.12 | AsyncIO | SOLID: Single Responsibility per subclass
"""

from __future__ import annotations

import abc
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


class AgentRole(str, Enum):
    CODER     = "coder"
    TESTER    = "tester"
    SECURITY  = "security"
    ARCHITECT = "architect"


@dataclass
class AgentResult:
    success: bool
    role: AgentRole
    output: str
    artifacts: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __bool__(self) -> bool:
        return self.success


_PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
_REASONING_LOG = _PROJECT_ROOT / "logs" / "reasoning.log"


class BaseAgent(abc.ABC):
    """
    Abstract base for all Jarvis agents.
    Each subclass implements execute() with a single clear responsibility.
    RB-Protokoll: every action is logged (Transparenz).

    AWP-081: call await self.pre_awp_checkpoint("AWP-NNN") before starting work.
    AWP-083: call await self.log_reasoning("s1", "s2", "s3") before write_file.
    """

    role: AgentRole           # must be set by subclass

    def __init__(self) -> None:
        self.log = logging.getLogger(f"jarvis.agent.{self.role.value}")
        self._project_root = _PROJECT_ROOT

    # ── Public API ─────────────────────────────────────────────────────────

    async def run(self, **kwargs: Any) -> AgentResult:
        self.log.info("@%s START %s", self.role.value, kwargs)
        result = await self.execute(**kwargs)
        icon = "✅" if result.success else "❌"
        self.log.info("@%s %s END output=%s errors=%s",
                      self.role.value, icon,
                      result.output[:120], result.errors)
        return result

    @abc.abstractmethod
    async def execute(self, **kwargs: Any) -> AgentResult:
        """Agent-specific logic. Override in subclasses."""

    # ── AWP-081: Git Checkpointing ─────────────────────────────────────────

    async def pre_awp_checkpoint(self, awp_id: str) -> bool:
        """
        Create a git commit 'PRE-AWP: [awp_id]' before starting an AWP.
        Stages all tracked changes. Returns True on success.
        """
        msg = f"PRE-AWP: {awp_id} [@{self.role.value}]"
        try:
            loop = asyncio.get_event_loop()
            ok = await loop.run_in_executor(None, self._git_checkpoint, msg)
            if ok:
                self.log.info("Git checkpoint: %s", msg)
            return ok
        except Exception as exc:
            self.log.warning("Git checkpoint failed: %s", exc)
            return False

    def _git_checkpoint(self, message: str) -> bool:
        import subprocess
        cwd = str(self._project_root)
        # Stage everything tracked
        r1 = subprocess.run(
            ["git", "add", "-u"],
            cwd=cwd, capture_output=True,
        )
        # Only commit if there's something staged
        r2 = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=cwd,
        )
        if r2.returncode == 0:
            return True   # nothing to commit — that's fine
        r3 = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=cwd, capture_output=True,
        )
        return r3.returncode == 0

    # ── AWP-083: Reasoning Log ─────────────────────────────────────────────

    async def log_reasoning(
        self,
        sentence1: str,
        sentence2: str,
        sentence3: str,
        task: str = "",
    ) -> None:
        """
        Log 3-sentence strategy to logs/reasoning.log BEFORE calling write_file.
        Mandatory for all agents per AWP-083.
        """
        ts = datetime.now(tz=timezone.utc).isoformat()
        entry = (
            f"\n[{ts}] @{self.role.value}"
            + (f" | task={task[:60]}" if task else "")
            + f"\n  1. {sentence1}"
            f"\n  2. {sentence2}"
            f"\n  3. {sentence3}\n"
        )
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._append_reasoning, entry)
        self.log.debug("Reasoning logged: %s…", sentence1[:60])

    def _append_reasoning(self, entry: str) -> None:
        _REASONING_LOG.parent.mkdir(parents=True, exist_ok=True)
        with _REASONING_LOG.open("a", encoding="utf-8") as f:
            f.write(entry)

    # ── Helpers ────────────────────────────────────────────────────────────

    def _safe_path(self, relative: str) -> Path:
        """Resolve a relative path and guard against traversal."""
        target = (self._project_root / relative).resolve()
        if not str(target).startswith(str(self._project_root)):
            raise ValueError(f"Path traversal blocked: {relative!r}")
        return target

    def _ok(self, output: str, **meta: Any) -> AgentResult:
        return AgentResult(success=True, role=self.role, output=output, metadata=meta)

    def _fail(self, error: str, **meta: Any) -> AgentResult:
        return AgentResult(success=False, role=self.role, output="",
                           errors=[error], metadata=meta)
