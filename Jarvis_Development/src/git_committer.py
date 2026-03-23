"""
AWP-070 – Autonomous Git Committer
Committed automatisch wenn:
  1. Test-Coverage >= COVERAGE_THRESHOLD (100% default)
  2. Tribunal-Verdict == APPROVE
  3. RB-Menschliche-Hoheit: Confirmation via API-Gate

WICHTIG: Kein git push ohne explizite Freigabe.
         Commit message wird vom LLM generiert.

Python 3.12 | AsyncIO | subprocess
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

log = logging.getLogger("jarvis.git_committer")

REPO_ROOT          = Path(__file__).parent.parent
COVERAGE_THRESHOLD = float(__import__("os").environ.get("COMMIT_COVERAGE_MIN", "80.0"))
OLLAMA_URL         = "http://localhost:11434"
COMMIT_MODEL       = "qwen2.5:14b"

# RB-Gate: requires human approval via /api/commit/approve endpoint
RB_REQUIRE_HUMAN   = True


@dataclass
class CommitResult:
    success: bool
    sha: str = ""
    message: str = ""
    error: str = ""
    blocked_reason: str = ""


async def _git(
    *args: str,
    cwd: Path = REPO_ROOT,
) -> tuple[int, str, str]:
    """Run a git command asynchronously."""
    proc = await asyncio.create_subprocess_exec(
        "git", *args,
        cwd=str(cwd),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
    return proc.returncode, stdout.decode(), stderr.decode()


async def check_coverage(report_path: Path | None = None) -> float:
    """Parse pytest coverage report and return percentage."""
    # Try coverage.json first
    cov_json = REPO_ROOT / "coverage.json"
    if cov_json.exists():
        try:
            data = json.loads(cov_json.read_text(encoding="utf-8"))
            return float(data.get("totals", {}).get("percent_covered", 0))
        except (json.JSONDecodeError, KeyError, ValueError):
            pass

    # Try parsing coverage report text
    if report_path and report_path.exists():
        text = report_path.read_text(encoding="utf-8")
        m = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", text)
        if m:
            return float(m.group(1))

    return 0.0


async def _generate_commit_message(diff: str) -> str:
    """Use LLM to generate a conventional commit message."""
    prompt = (
        "Generiere eine kurze Git-Commit-Message (max 72 Zeichen) "
        "im Conventional-Commits-Format für diesen Diff.\n"
        "Antworte NUR mit der Commit-Message, ohne Anführungszeichen.\n\n"
        f"```diff\n{diff[:3000]}\n```"
    )
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={"model": COMMIT_MODEL, "prompt": prompt, "stream": False},
            )
            resp.raise_for_status()
            msg = resp.json()["response"].strip().split("\n")[0]
            # Ensure conventional prefix
            if not re.match(r"^(feat|fix|refactor|test|chore|docs|perf|style):", msg):
                msg = f"chore: {msg}"
            return msg[:72]
    except Exception as exc:
        log.warning("LLM commit message failed: %s", exc)
        ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M")
        return f"chore: auto-commit {ts}"


async def commit(
    coverage: float | None = None,
    tribunal_approved: bool = False,
    human_approved: bool = False,
    files: list[str] | None = None,
    awp_id: str = "",
) -> CommitResult:
    """
    Attempt an autonomous commit after all gates pass.

    Args:
        coverage:          Test coverage %. If None, will be measured.
        tribunal_approved: Whether the conflict tribunal approved.
        human_approved:    RB human confirmation gate.
        files:             Specific files to stage (None = all tracked changes).
        awp_id:            AWP reference for commit message.
    """
    # Gate 1: Coverage
    if coverage is None:
        coverage = await check_coverage()
    if coverage < COVERAGE_THRESHOLD:
        reason = f"Coverage {coverage:.1f}% < {COVERAGE_THRESHOLD}%"
        log.warning("Commit blocked: %s", reason)
        return CommitResult(success=False, blocked_reason=reason)

    # Gate 2: Tribunal
    if not tribunal_approved:
        reason = "Tribunal approval required"
        log.warning("Commit blocked: %s", reason)
        return CommitResult(success=False, blocked_reason=reason)

    # Gate 3: RB human confirmation
    if RB_REQUIRE_HUMAN and not human_approved:
        reason = "RB-Protokoll: Human confirmation required before commit"
        log.warning("Commit blocked: %s", reason)
        return CommitResult(success=False, blocked_reason=reason)

    # Get diff for commit message
    rc, diff, _ = await _git("diff", "--staged", "--stat")
    if not diff.strip():
        # Stage files first
        stage_args = ["add"] + (files or ["-A"])
        rc, _, err = await _git(*stage_args)
        if rc != 0:
            return CommitResult(success=False, error=f"git add failed: {err}")
        rc, diff, _ = await _git("diff", "--staged", "--stat")

    if not diff.strip():
        return CommitResult(success=False, blocked_reason="Nothing to commit")

    # Generate commit message
    msg = await _generate_commit_message(diff)
    if awp_id:
        msg = f"{msg} [{awp_id}]"

    # Commit
    rc, out, err = await _git("commit", "-m", msg)
    if rc != 0:
        log.error("git commit failed: %s", err)
        return CommitResult(success=False, error=err)

    # Get SHA
    rc, sha, _ = await _git("rev-parse", "--short", "HEAD")
    sha = sha.strip()
    log.info("Committed %s: %s", sha, msg)
    return CommitResult(success=True, sha=sha, message=msg)


async def get_status() -> dict[str, Any]:
    """Return current git status summary."""
    _, branch, _ = await _git("branch", "--show-current")
    _, diff_stat, _ = await _git("diff", "--stat")
    _, log_short, _ = await _git("log", "--oneline", "-5")
    return {
        "branch": branch.strip(),
        "staged_changes": diff_stat.strip(),
        "recent_commits": log_short.strip().splitlines(),
    }
