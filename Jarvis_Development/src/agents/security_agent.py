"""
AWP-034 – Security Agent (@security / Sentinel)
Prüft Code-Diffs und Dateien auf Secrets, Injection, veraltete Algorithmen.
Skill: owasp_scanner_logic.md v1.0
Veto-Recht: Bei kritischem Fund → success=False → Handover-Protokoll stoppt.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .base_agent import AgentResult, AgentRole, BaseAgent

# ─────────────────────────────────────────────
# Regexes (static, compiled once)
# ─────────────────────────────────────────────
_SECRET_PATTERNS = [
    (re.compile(r'(?i)(password|passwd|secret|api[_-]?key|token|auth)\s*=\s*["\'][^"\']{4,}'),
     "Hardcoded secret/credential"),
    (re.compile(r'(?i)-----BEGIN (RSA|EC|OPENSSH|PGP) PRIVATE KEY-----'),
     "Private key in source"),
    (re.compile(r'(?i)(aws_access_key_id|aws_secret_access_key)\s*=\s*\S+'),
     "AWS credential"),
    (re.compile(r'(?i)ghp_[A-Za-z0-9]{36}'),
     "GitHub Personal Access Token"),
]

_INJECTION_PATTERNS = [
    (re.compile(r'subprocess\.(call|run|Popen)\(.*shell\s*=\s*True', re.DOTALL),
     "subprocess with shell=True (command injection risk)"),
    (re.compile(r'eval\s*\('),
     "eval() usage (code injection)"),
    (re.compile(r'exec\s*\('),
     "exec() usage (code injection)"),
    (re.compile(r'os\.system\('),
     "os.system() (command injection risk)"),
    (re.compile(r'__import__\s*\('),
     "Dynamic __import__ (code injection)"),
]

_CRYPTO_PATTERNS = [
    (re.compile(r'(?i)(import|from)\s+.*\bmd5\b'),
     "MD5 usage (deprecated hash)"),
    (re.compile(r'(?i)hashlib\.new\(["\']md5["\']'),
     "MD5 via hashlib"),
    (re.compile(r'(?i)hashlib\.sha1\b'),
     "SHA1 usage (deprecated)"),
    (re.compile(r'(?i)DES\b'),
     "DES cipher (deprecated)"),
]


@dataclass
class Finding:
    severity: str   # "CRITICAL" | "WARNING" | "INFO"
    rule: str
    line: int
    snippet: str


class SecurityAgent(BaseAgent):
    role = AgentRole.SECURITY

    async def execute(
        self,
        content: str | None = None,
        file: str | None = None,
        **_: Any,
    ) -> AgentResult:
        if content is None and file:
            try:
                path = self._safe_path(file)
                content = path.read_text(encoding="utf-8", errors="replace")
            except (ValueError, OSError) as exc:
                return self._fail(str(exc))

        if content is None:
            return self._fail("No content provided for security scan")

        findings = self._scan(content)
        critical = [f for f in findings if f.severity == "CRITICAL"]
        warnings_ = [f for f in findings if f.severity == "WARNING"]

        report_lines = [f"Security Scan: {len(findings)} finding(s)"]
        for f in findings:
            report_lines.append(
                f"  [{f.severity}] L{f.line}: {f.rule}\n    ↳ {f.snippet[:80]}"
            )

        report = "\n".join(report_lines)
        self.log.info("@security scan: %d critical, %d warnings", len(critical), len(warnings_))

        if critical:
            self.log.warning("@security VETO: critical findings – blocking handover")

        return AgentResult(
            success=len(critical) == 0,  # VETO if any critical finding
            role=self.role,
            output=report,
            errors=[f.rule for f in critical],
            metadata={
                "critical": len(critical),
                "warnings": len(warnings_),
                "findings": [
                    {"severity": f.severity, "rule": f.rule, "line": f.line}
                    for f in findings
                ],
            },
        )

    def _scan(self, content: str) -> list[Finding]:
        findings: list[Finding] = []
        lines = content.splitlines()

        for i, line in enumerate(lines, 1):
            for pattern, rule in _SECRET_PATTERNS:
                if pattern.search(line):
                    findings.append(Finding("CRITICAL", rule, i, line.strip()))

            for pattern, rule in _INJECTION_PATTERNS:
                if pattern.search(line):
                    findings.append(Finding("CRITICAL", rule, i, line.strip()))

            for pattern, rule in _CRYPTO_PATTERNS:
                if pattern.search(line):
                    findings.append(Finding("WARNING", rule, i, line.strip()))

        return findings
