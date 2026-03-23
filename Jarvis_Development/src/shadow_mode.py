"""
AWP-069 – Shadow Mode (Dry-Run Simulator)
Führt Agenten-Pipelines in einer isolierten Sandbox durch,
bevor Ergebnisse im Dashboard angezeigt werden.

Sandbox: Temporäres Verzeichnis + eigene SQLite-Instanz.
Ergebnisse werden als ShadowReport gespeichert (nicht committed).

Python 3.12 | AsyncIO
"""

from __future__ import annotations

import asyncio
import json
import logging
import shutil
import tempfile
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

log = logging.getLogger("jarvis.shadow_mode")

REPORT_DIR = Path(__file__).parent.parent / "data" / "shadow_reports"


@dataclass
class ShadowAction:
    action_type: str       # "file_write" | "file_delete" | "db_insert" | "shell"
    target: str            # path or query
    content: str = ""      # what would be written
    outcome: str = ""      # "ok" | "would_fail: <reason>"


@dataclass
class ShadowReport:
    run_id: str
    pipeline: str
    started_at: str
    finished_at: str = ""
    actions: list[ShadowAction] = field(default_factory=list)
    final_status: str = "pending"   # "ok" | "would_fail" | "partial"
    risk_flags: list[str] = field(default_factory=list)
    approved_for_real: bool = False


class ShadowMode:
    """
    Intercept agent file operations in a temp directory.
    Real filesystem is never touched.
    """

    def __init__(self, pipeline_name: str) -> None:
        self.pipeline_name = pipeline_name
        self.run_id = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
        self._sandbox: Path | None = None
        self._report = ShadowReport(
            run_id=self.run_id,
            pipeline=pipeline_name,
            started_at=datetime.now(tz=timezone.utc).isoformat(),
        )

    # ── Lifecycle ──────────────────────────────────────────────────────────

    async def __aenter__(self) -> "ShadowMode":
        loop = asyncio.get_event_loop()
        self._sandbox = Path(
            await loop.run_in_executor(None, tempfile.mkdtemp, "jarvis_shadow_")
        )
        log.info("Shadow sandbox: %s", self._sandbox)
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self._finalize()
        if self._sandbox and self._sandbox.exists():
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, shutil.rmtree, self._sandbox, True
            )
        log.info("Shadow run %s complete: %s", self.run_id, self._report.final_status)

    # ── Intercepted operations ─────────────────────────────────────────────

    async def write_file(self, real_path: Path, content: str) -> ShadowAction:
        """Intercept a file write — writes to sandbox instead."""
        if self._sandbox is None:
            raise RuntimeError("ShadowMode not entered")

        rel = real_path.name
        shadow_path = self._sandbox / rel
        action = ShadowAction(
            action_type="file_write",
            target=str(real_path),
            content=content[:500],  # truncate for report
        )
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: shadow_path.write_text(content, encoding="utf-8"),
            )
            action.outcome = "ok"
            # Risk flags
            if "password" in content.lower() or "secret" in content.lower():
                self._report.risk_flags.append(
                    f"Potential secret in {real_path.name}"
                )
        except OSError as exc:
            action.outcome = f"would_fail: {exc}"
            self._report.final_status = "would_fail"

        self._report.actions.append(action)
        return action

    async def delete_file(self, real_path: Path) -> ShadowAction:
        """Simulate a file deletion (just records it)."""
        action = ShadowAction(
            action_type="file_delete",
            target=str(real_path),
        )
        if real_path.exists():
            action.outcome = "ok (would delete)"
        else:
            action.outcome = "would_fail: file not found"
        self._report.actions.append(action)
        return action

    async def shell_command(self, cmd: str) -> ShadowAction:
        """Record a shell command without executing it."""
        action = ShadowAction(
            action_type="shell",
            target=cmd,
            outcome="dry-run: not executed",
        )
        # Flag dangerous patterns
        danger = ["rm -rf", "format", "DROP TABLE", "del /f"]
        for d in danger:
            if d.lower() in cmd.lower():
                action.outcome = f"would_fail: dangerous pattern '{d}' detected"
                self._report.risk_flags.append(f"Dangerous command: {cmd[:80]}")
                break
        self._report.actions.append(action)
        return action

    # ── Report ─────────────────────────────────────────────────────────────

    async def _finalize(self) -> None:
        self._report.finished_at = datetime.now(tz=timezone.utc).isoformat()
        if self._report.final_status == "pending":
            self._report.final_status = (
                "would_fail" if self._report.risk_flags else "ok"
            )

        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        out = REPORT_DIR / f"shadow_{self.run_id}.json"
        loop = asyncio.get_event_loop()
        data = asdict(self._report)
        await loop.run_in_executor(
            None,
            lambda: out.write_text(json.dumps(data, indent=2), encoding="utf-8"),
        )
        log.info("Shadow report: %s", out)

    @property
    def report(self) -> ShadowReport:
        return self._report

    def approve(self) -> None:
        """Mark this shadow run as approved for real execution."""
        self._report.approved_for_real = True
        log.info("Shadow run %s APPROVED for real execution", self.run_id)


async def run_shadow_pipeline(
    pipeline_name: str,
    actions: list[dict],
) -> ShadowReport:
    """
    High-level helper: simulate a sequence of actions.

    Each action dict: {"type": "write"|"delete"|"shell", "target": str, "content": str}
    """
    async with ShadowMode(pipeline_name) as shadow:
        for act in actions:
            t = act.get("type", "")
            if t == "write":
                await shadow.write_file(Path(act["target"]), act.get("content", ""))
            elif t == "delete":
                await shadow.delete_file(Path(act["target"]))
            elif t == "shell":
                await shadow.shell_command(act["target"])
        return shadow.report
