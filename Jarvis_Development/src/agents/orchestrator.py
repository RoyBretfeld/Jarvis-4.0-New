"""
AWP-035 – Handover Orchestrator
Automatischer Wechsel: @coder → @tester → @security
Pipeline stoppt bei @security VETO (critical findings).
RB-Protokoll: Transparenz – jeder Handover-Schritt wird geloggt.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from .base_agent import AgentResult
from .coder_agent import CoderAgent
from .security_agent import SecurityAgent
from .tester_agent import TesterAgent

log = logging.getLogger("jarvis.orchestrator")


@dataclass
class PipelineResult:
    success: bool
    steps: list[dict[str, Any]] = field(default_factory=list)
    stopped_at: str | None = None
    final_output: str = ""

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "stopped_at": self.stopped_at,
            "final_output": self.final_output,
            "steps": self.steps,
        }


class Orchestrator:
    """
    Runs the Coder → Tester → Security pipeline.
    Any failed step halts the pipeline (SEC-Protokoll gate).
    """

    def __init__(self) -> None:
        self.coder    = CoderAgent()
        self.tester   = TesterAgent()
        self.security = SecurityAgent()

    async def dispatch(
        self,
        agent_name: str,
        file: str | None = None,
        content: str | None = None,
        **kwargs: Any,
    ) -> dict:
        """Route a single-agent request (from API)."""
        agents = {
            "coder":    self.coder,
            "refactor": self.coder,
            "test":     self.tester,
            "security": self.security,
        }
        agent = agents.get(agent_name)
        if agent is None:
            return {"success": False, "error": f"Unknown agent: {agent_name!r}"}

        op = "refactor" if agent_name == "refactor" else "write"
        result = await agent.run(file=file, content=content, operation=op, **kwargs)
        return {"success": result.success, "output": result.output,
                "errors": result.errors, "metadata": result.metadata}

    async def run_pipeline(
        self,
        file: str,
        new_content: str,
    ) -> PipelineResult:
        """
        Full Coder → Tester → Security pipeline.
        Step 1 (@coder):    Write file with backup.
        Step 2 (@tester):   Run tests. Fail → rollback.
        Step 3 (@security): Scan new content. Veto → rollback.
        """
        pipeline = PipelineResult(success=False)

        # ── Step 1: Coder ─────────────────────
        log.info("Pipeline STEP 1/3: @coder writing %s", file)
        coder_result = await self.coder.run(
            file=file, content=new_content, operation="write"
        )
        pipeline.steps.append(self._step_dict("coder", coder_result))

        if not coder_result:
            pipeline.stopped_at = "coder"
            pipeline.final_output = f"Coder failed: {coder_result.errors}"
            return pipeline

        # ── Step 2: Tester ────────────────────
        log.info("Pipeline STEP 2/3: @tester running tests")
        tester_result = await self.tester.run(target="tests")
        pipeline.steps.append(self._step_dict("tester", tester_result))

        if not tester_result:
            log.warning("Pipeline GATE: tester failed – initiating rollback")
            await self._rollback(coder_result)
            pipeline.stopped_at = "tester"
            pipeline.final_output = f"Tests failed. Rolled back {file}."
            return pipeline

        # ── Step 3: Security ──────────────────
        log.info("Pipeline STEP 3/3: @security scanning %s", file)
        security_result = await self.security.run(content=new_content, file=file)
        pipeline.steps.append(self._step_dict("security", security_result))

        if not security_result:
            log.warning("Pipeline GATE: security VETO – initiating rollback")
            await self._rollback(coder_result)
            pipeline.stopped_at = "security"
            pipeline.final_output = (
                f"Security VETO. Rolled back {file}.\n"
                f"Critical findings: {security_result.errors}"
            )
            return pipeline

        # ── All clear ─────────────────────────
        pipeline.success = True
        pipeline.final_output = (
            f"Pipeline complete: {file} written, tests passed, security clean."
        )
        log.info("Pipeline SUCCESS: %s", file)
        return pipeline

    @staticmethod
    def _step_dict(name: str, result: AgentResult) -> dict:
        return {
            "agent": name,
            "success": result.success,
            "output": result.output[:500],
            "errors": result.errors,
        }

    async def _rollback(self, coder_result: AgentResult) -> None:
        backup = coder_result.metadata.get("backup")
        if backup:
            from pathlib import Path
            import shutil
            src = Path(backup)
            # Derive original path from backup filename
            original_name = src.stem.rsplit("_", 1)[0] + src.suffix
            dest = src.parent.parent.parent / "src" / original_name
            if src.exists() and dest.exists():
                shutil.copy2(src, dest)
                log.info("Rollback: restored %s from %s", dest.name, src.name)
            else:
                log.error("Rollback failed: src=%s dest=%s", src, dest)
        else:
            log.warning("Rollback skipped: no backup path in coder result")
