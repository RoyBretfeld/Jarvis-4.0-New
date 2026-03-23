"""
AWP-079 – Clean Slate Protocol
Vollständiger System-Rebuild aus Backups in < 5 Minuten.

Schritte:
  1. Stoppe alle Container
  2. Restore src/ aus logs/backups/ (neuester Snapshot)
  3. Restore data/ (decisions.db, vector snapshots)
  4. Rebuild Docker-Stack
  5. Verify: heartbeat + API health check
  6. Report: time-to-recovery

RB-Protokoll: Requires explicit human confirmation before execution.
Python 3.12 | AsyncIO
"""

from __future__ import annotations

import asyncio
import json
import logging
import shutil
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

log = logging.getLogger("jarvis.clean_slate")

PROJECT_ROOT = Path(__file__).parent.parent
BACKUP_DIR   = PROJECT_ROOT / "logs" / "backups"
DATA_DIR     = PROJECT_ROOT / "data"
SRC_DIR      = PROJECT_ROOT / "src"
COMPOSE_FILE = PROJECT_ROOT / "docker-compose.yml"

HEALTH_TIMEOUT   = 120   # seconds to wait for containers to be healthy
VERIFY_URL       = "http://localhost:8000/health"


@dataclass
class RestoreStep:
    name: str
    duration_s: float = 0.0
    status: str = "pending"    # "ok" | "failed" | "skipped"
    detail: str = ""


@dataclass
class CleanSlateReport:
    started_at: str
    finished_at: str = ""
    total_seconds: float = 0.0
    success: bool = False
    steps: list[RestoreStep] = field(default_factory=list)
    backup_used: str = ""
    error: str = ""


async def _run_cmd(*args: str, cwd: Path = PROJECT_ROOT) -> tuple[int, str]:
    proc = await asyncio.create_subprocess_exec(
        *args, cwd=str(cwd),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    out, _ = await asyncio.wait_for(proc.communicate(), timeout=300)
    return proc.returncode, out.decode()


def _find_latest_backup() -> Path | None:
    """Find the most recent backup directory."""
    if not BACKUP_DIR.exists():
        return None
    candidates = [
        d for d in BACKUP_DIR.iterdir()
        if d.is_dir() and d.name.startswith("snapshot_")
    ]
    return max(candidates, key=lambda d: d.stat().st_mtime, default=None)


async def _stop_containers(report: CleanSlateReport) -> bool:
    step = RestoreStep(name="stop_containers")
    t0 = time.monotonic()
    try:
        rc, out = await _run_cmd("docker", "compose", "down", "--timeout", "10")
        step.status = "ok" if rc == 0 else "failed"
        step.detail = out[:200]
    except Exception as exc:
        step.status = "failed"
        step.detail = str(exc)
    step.duration_s = time.monotonic() - t0
    report.steps.append(step)
    return step.status == "ok"


async def _restore_src(backup: Path, report: CleanSlateReport) -> bool:
    step = RestoreStep(name="restore_src")
    t0 = time.monotonic()
    backup_src = backup / "src"
    try:
        if not backup_src.exists():
            step.status = "skipped"
            step.detail = "No src/ in backup"
        else:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: shutil.copytree(
                    str(backup_src), str(SRC_DIR),
                    dirs_exist_ok=True,
                ),
            )
            step.status = "ok"
            step.detail = f"Restored from {backup_src}"
    except Exception as exc:
        step.status = "failed"
        step.detail = str(exc)
    step.duration_s = time.monotonic() - t0
    report.steps.append(step)
    return step.status in ("ok", "skipped")


async def _restore_data(backup: Path, report: CleanSlateReport) -> bool:
    step = RestoreStep(name="restore_data")
    t0 = time.monotonic()
    backup_data = backup / "data"
    try:
        if not backup_data.exists():
            step.status = "skipped"
            step.detail = "No data/ in backup"
        else:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: shutil.copytree(
                    str(backup_data), str(DATA_DIR),
                    dirs_exist_ok=True,
                ),
            )
            step.status = "ok"
    except Exception as exc:
        step.status = "failed"
        step.detail = str(exc)
    step.duration_s = time.monotonic() - t0
    report.steps.append(step)
    return step.status in ("ok", "skipped")


async def _rebuild_containers(report: CleanSlateReport) -> bool:
    step = RestoreStep(name="rebuild_containers")
    t0 = time.monotonic()
    try:
        rc, out = await _run_cmd(
            "docker", "compose", "up", "-d", "--build", "--wait"
        )
        step.status = "ok" if rc == 0 else "failed"
        step.detail = out[:300]
    except Exception as exc:
        step.status = "failed"
        step.detail = str(exc)
    step.duration_s = time.monotonic() - t0
    report.steps.append(step)
    return step.status == "ok"


async def _verify_health(report: CleanSlateReport) -> bool:
    step = RestoreStep(name="verify_health")
    t0 = time.monotonic()
    deadline = time.monotonic() + HEALTH_TIMEOUT
    try:
        import httpx
        while time.monotonic() < deadline:
            try:
                async with httpx.AsyncClient(timeout=5) as client:
                    resp = await client.get(VERIFY_URL)
                    if resp.status_code == 200:
                        step.status = "ok"
                        step.detail = f"API healthy in {time.monotonic()-t0:.1f}s"
                        break
            except Exception:
                await asyncio.sleep(3)
        else:
            step.status = "failed"
            step.detail = f"Timeout after {HEALTH_TIMEOUT}s"
    except ImportError:
        step.status = "skipped"
        step.detail = "httpx not available"
    step.duration_s = time.monotonic() - t0
    report.steps.append(step)
    return step.status in ("ok", "skipped")


async def execute(
    human_confirmed: bool = False,
    backup_path: str | None = None,
) -> CleanSlateReport:
    """
    Execute the Clean Slate Protocol.

    Args:
        human_confirmed: RB gate — must be True to proceed.
        backup_path:     Optional explicit backup directory path.
    """
    report = CleanSlateReport(
        started_at=datetime.now(tz=timezone.utc).isoformat()
    )
    t_start = time.monotonic()

    if not human_confirmed:
        report.error = "RB-Protokoll: Human confirmation required (human_confirmed=True)"
        log.error(report.error)
        return report

    backup = Path(backup_path) if backup_path else _find_latest_backup()
    if backup is None:
        report.error = "No backup found in logs/backups/"
        log.error(report.error)
        return report

    report.backup_used = str(backup)
    log.warning("CLEAN SLATE initiated from backup: %s", backup)

    steps = [
        _stop_containers,
        lambda r: _restore_src(backup, r),
        lambda r: _restore_data(backup, r),
        _rebuild_containers,
        _verify_health,
    ]

    for step_fn in steps:
        ok = await step_fn(report)
        if not ok and report.steps[-1].status == "failed":
            report.error = f"Step '{report.steps[-1].name}' failed: {report.steps[-1].detail}"
            break

    report.total_seconds = time.monotonic() - t_start
    report.finished_at = datetime.now(tz=timezone.utc).isoformat()
    report.success = all(s.status in ("ok", "skipped") for s in report.steps)

    _write_report(report)
    log.info(
        "Clean Slate complete: success=%s, time=%.1fs",
        report.success, report.total_seconds,
    )
    return report


def _write_report(report: CleanSlateReport) -> None:
    out = PROJECT_ROOT / "logs" / "clean_slate_report.md"
    status_icon = "✅" if report.success else "❌"
    lines = [
        "# Clean Slate Protocol Report",
        f"**{status_icon} {'SUCCESS' if report.success else 'FAILED'}**",
        f"- Started: {report.started_at}",
        f"- Finished: {report.finished_at}",
        f"- Duration: {report.total_seconds:.1f}s",
        f"- Backup: `{report.backup_used}`",
        "",
        "## Steps",
    ]
    for step in report.steps:
        icon = "✅" if step.status == "ok" else "⏭" if step.status == "skipped" else "❌"
        lines.append(f"- {icon} **{step.name}** ({step.duration_s:.1f}s): {step.detail}")
    if report.error:
        lines.append(f"\n**Error:** {report.error}")
    out.write_text("\n".join(lines), encoding="utf-8")
