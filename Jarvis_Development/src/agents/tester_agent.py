"""
AWP-033 – Tester Agent (@tester)
Führt pytest und Ruff-Linting in der Sandbox aus.
Gibt Exit-Code, stdout/stderr als AgentResult zurück.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any

from .base_agent import AgentResult, AgentRole, BaseAgent

TIMEOUT = 120  # seconds


class TesterAgent(BaseAgent):
    role = AgentRole.TESTER

    async def execute(
        self,
        target: str = "tests",
        lint: bool = True,
        **_: Any,
    ) -> AgentResult:
        test_dir = self._safe_path(target)
        if not test_dir.exists():
            return self._fail(f"Test directory not found: {target}")

        results: list[str] = []
        errors: list[str] = []

        # ── Ruff Lint ─────────────────────────
        if lint:
            lint_result = await self._run_command(
                [sys.executable, "-m", "ruff", "check",
                 str(self._project_root / "src"), "--output-format=text"],
                label="ruff",
            )
            results.append(f"=== LINT ===\n{lint_result.output}")
            if not lint_result.success:
                errors.extend(lint_result.errors)

        # ── Pytest ────────────────────────────
        pytest_result = await self._run_command(
            [sys.executable, "-m", "pytest", str(test_dir),
             "-v", "--tb=short", "--no-header"],
            label="pytest",
        )
        results.append(f"=== TESTS ===\n{pytest_result.output}")
        if not pytest_result.success:
            errors.extend(pytest_result.errors)

        overall_ok = not errors
        return AgentResult(
            success=overall_ok,
            role=self.role,
            output="\n".join(results),
            errors=errors,
            metadata={"exit_codes": {
                "lint": 0 if lint_result.success else 1 if lint else "skipped",
                "pytest": 0 if pytest_result.success else 1,
            }},
        )

    async def _run_command(
        self, cmd: list[str], label: str
    ) -> AgentResult:
        self.log.info("@tester RUN %s: %s", label, " ".join(cmd))
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=str(self._project_root),
            )
            try:
                stdout, _ = await asyncio.wait_for(
                    proc.communicate(), timeout=TIMEOUT
                )
            except asyncio.TimeoutError:
                proc.kill()
                return self._fail(f"{label} timed out after {TIMEOUT}s")

            out = stdout.decode(errors="replace")
            success = proc.returncode == 0
            self.log.info("@tester %s exit=%d", label, proc.returncode)
            return AgentResult(
                success=success, role=self.role,
                output=out,
                errors=[] if success else [f"{label} failed (exit {proc.returncode})"],
            )
        except FileNotFoundError as exc:
            return self._fail(f"{label} not found: {exc}")
