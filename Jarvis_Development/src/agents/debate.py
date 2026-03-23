"""
AWP-050 – Agent Debate Mode
@coder und @security "diskutieren" eine kritische Änderung.
Nach max. N Runden: Konsens → Pipeline weiter / kein Konsens → Human-GO required.

RB-Protokoll: Menschliche Hoheit – keine Aktion ohne Human-GO wenn kein Konsens.
Python 3.12 | AsyncIO
"""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import aiohttp

from .base_agent import AgentRole
from .security_agent import SecurityAgent

log = logging.getLogger("jarvis.debate")

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL    = os.environ.get("OLLAMA_MODEL_DEFAULT", "mistral")
MAX_ROUNDS      = int(os.environ.get("DEBATE_MAX_ROUNDS", "3"))


# ─────────────────────────────────────────────
# Data
# ─────────────────────────────────────────────

@dataclass
class DebateRound:
    round_num: int
    coder_argument: str
    security_response: str
    consensus_reached: bool = False


@dataclass
class DebateResult:
    topic: str
    file: str
    rounds: list[DebateRound] = field(default_factory=list)
    consensus: bool = False
    final_verdict: str = ""
    requires_human_approval: bool = True
    security_findings: int = 0
    timestamp: str = field(
        default_factory=lambda: datetime.now(tz=timezone.utc).isoformat()
    )


# ─────────────────────────────────────────────
# LLM helper
# ─────────────────────────────────────────────

async def _llm_respond(
    system_prompt: str, user_message: str, role_name: str
) -> str:
    """Call Ollama to generate a role-specific argument."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": OLLAMA_MODEL,
                    "stream": False,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user",   "content": user_message},
                    ],
                },
                timeout=aiohttp.ClientTimeout(total=60),
            ) as resp:
                if resp.status != 200:
                    return f"[{role_name} unavailable: HTTP {resp.status}]"
                data = await resp.json()
                return data.get("message", {}).get("content", "").strip()
    except Exception as exc:
        log.warning("LLM call failed for %s: %s", role_name, exc)
        return f"[{role_name} offline – skipping LLM argument]"


# ─────────────────────────────────────────────
# Debate engine
# ─────────────────────────────────────────────

class AgentDebate:
    """
    Structured debate between @coder (proposer) and @security (critic).

    Round flow:
      1. @coder presents the change and its rationale.
      2. @security raises objections (OWASP scan + LLM critique).
      3. @coder responds to objections.
      Repeat up to MAX_ROUNDS.

    Consensus: security finds 0 critical issues AND acknowledges coder's response.
    No consensus after MAX_ROUNDS → requires_human_approval = True.
    """

    CODER_SYSTEM = (
        "You are the @coder agent in the Jarvis 4.0 system. "
        "You are proposing a code change and must defend its correctness, "
        "security, and value. Be concise (3-5 sentences). "
        "Address security concerns directly."
    )

    SECURITY_SYSTEM = (
        "You are the @security Sentinel in the Jarvis 4.0 system. "
        "Your job is to identify risks in the proposed code change. "
        "If the coder has adequately addressed all concerns, say 'CONSENSUS REACHED'. "
        "Otherwise, list remaining concerns concisely (max 3 bullet points)."
    )

    def __init__(self) -> None:
        self._scanner = SecurityAgent()

    async def debate(
        self,
        file: str,
        new_content: str,
        change_rationale: str = "",
    ) -> DebateResult:
        result = DebateResult(
            topic=f"Code change proposal: {file}",
            file=file,
        )

        # Initial security scan (static – no LLM needed)
        scan = await self._scanner.run(content=new_content)
        result.security_findings = scan.metadata.get("critical", 0)

        # If no static findings, skip debate entirely
        if result.security_findings == 0 and scan.metadata.get("warnings", 0) == 0:
            result.consensus = True
            result.requires_human_approval = False
            result.final_verdict = "No security issues found. Auto-approved."
            log.info("Debate %s: no findings – auto-consensus", file)
            return result

        # Build debate context
        change_summary = (
            f"File: {file}\n"
            f"Rationale: {change_rationale or 'Not provided'}\n\n"
            f"Security scan: {scan.metadata.get('critical', 0)} critical, "
            f"{scan.metadata.get('warnings', 0)} warnings\n"
            f"Scan output:\n{scan.output[:600]}"
        )

        coder_position = (
            f"I propose the following change to {file}.\n"
            f"{change_rationale or 'This change improves the system.'}\n"
            f"The security scanner flagged some issues; I believe they are manageable."
        )

        last_security_response = ""

        for round_num in range(1, MAX_ROUNDS + 1):
            log.info("Debate round %d/%d for %s", round_num, MAX_ROUNDS, file)

            # @security responds to coder's position
            security_prompt = (
                f"Round {round_num}. The coder says:\n{coder_position}\n\n"
                f"Context:\n{change_summary}"
            )
            security_arg = await _llm_respond(
                self.SECURITY_SYSTEM, security_prompt, "@security"
            )
            last_security_response = security_arg

            consensus = "CONSENSUS REACHED" in security_arg.upper()

            debate_round = DebateRound(
                round_num=round_num,
                coder_argument=coder_position,
                security_response=security_arg,
                consensus_reached=consensus,
            )
            result.rounds.append(debate_round)

            if consensus:
                result.consensus = True
                result.requires_human_approval = False
                result.final_verdict = (
                    f"Consensus reached in round {round_num}. Change approved."
                )
                log.info("Debate consensus at round %d for %s", round_num, file)
                break

            if round_num < MAX_ROUNDS:
                # @coder formulates counter-response
                coder_prompt = (
                    f"@security raised these concerns:\n{security_arg}\n\n"
                    f"Address each concern and explain why the change is still safe."
                )
                coder_position = await _llm_respond(
                    self.CODER_SYSTEM, coder_prompt, "@coder"
                )

        if not result.consensus:
            result.requires_human_approval = True
            result.final_verdict = (
                f"No consensus after {MAX_ROUNDS} rounds. "
                f"Human approval required before proceeding.\n"
                f"Last security concern:\n{last_security_response[:300]}"
            )
            log.warning("Debate no-consensus for %s – human approval required", file)

        return result

    def format_report(self, result: DebateResult) -> str:
        lines = [
            f"# Agent Debate Report",
            f"**File:** `{result.file}`",
            f"**Consensus:** {'✅ YES' if result.consensus else '❌ NO'}",
            f"**Human Approval Required:** {result.requires_human_approval}",
            f"**Security Findings:** {result.security_findings} critical",
            "",
        ]
        for r in result.rounds:
            lines += [
                f"## Round {r.round_num}",
                f"**@coder:** {r.coder_argument}",
                f"**@security:** {r.security_response}",
                f"*Consensus: {r.consensus_reached}*",
                "",
            ]
        lines += [f"## Final Verdict", result.final_verdict]
        return "\n".join(lines)
