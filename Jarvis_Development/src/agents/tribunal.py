"""
AWP-066 – Conflict Resolution Tribunal
Ein @architect-Agent vermittelt bei widersprüchlichen Agenten-Urteilen.

Pipeline:
  1. Coder schlägt Änderung vor
  2. Tester/Security widersprechen (conflicting=True)
  3. Tribunal: @architect analysiert beide Seiten
  4. Verdict: APPROVE / REJECT / REVISE mit Begründung

Python 3.12 | AsyncIO
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import httpx

log = logging.getLogger("jarvis.tribunal")

OLLAMA_URL   = "http://localhost:11434"
ARCH_MODEL   = "qwen2.5:14b"
LOG_DIR      = Path(__file__).parent.parent.parent / "logs"
TRIBUNAL_LOG = LOG_DIR / "tribunal_decisions.jsonl"


@dataclass
class TribunalCase:
    case_id: str
    title: str
    proposal: str            # what the coder wants to do
    objections: list[str]    # tester/security objections
    context: str = ""        # relevant code snippet
    awp_id: str = ""


@dataclass
class TribunalVerdict:
    case_id: str
    verdict: Literal["APPROVE", "REJECT", "REVISE"]
    rationale: str
    conditions: list[str] = field(default_factory=list)   # if REVISE
    decided_at: str = ""
    requires_human: bool = False


ARCHITECT_SYSTEM = """\
Du bist @architect, der leitende Software-Architekt von Jarvis 4.0.
Deine Aufgabe: Widersprüche zwischen Agenten-Urteilen zu lösen.

Entscheidungsprinzipien:
1. Security und Korrektheit haben Vorrang vor Features.
2. Bewerte immer beide Seiten fair.
3. Wenn unklar: REVISE mit konkreten Bedingungen, nicht REJECT.
4. Begründe jede Entscheidung mit dem RB-Protokoll (Transparenz).

Antworte IMMER als JSON:
{
  "verdict": "APPROVE|REJECT|REVISE",
  "rationale": "...",
  "conditions": ["..."],
  "requires_human": false
}
"""


async def _call_architect(prompt: str) -> dict:
    payload = {
        "model": ARCH_MODEL,
        "messages": [
            {"role": "system", "content": ARCHITECT_SYSTEM},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.2},
    }
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(f"{OLLAMA_URL}/api/chat", json=payload)
        resp.raise_for_status()
        raw = resp.json()["message"]["content"]
        return json.loads(raw)


class ConflictTribunal:

    async def adjudicate(self, case: TribunalCase) -> TribunalVerdict:
        """Run the tribunal for a conflict case."""
        prompt = self._build_prompt(case)

        try:
            result = await _call_architect(prompt)
        except Exception as exc:
            log.error("Tribunal LLM call failed: %s", exc)
            # Fail safe: require human review
            return TribunalVerdict(
                case_id=case.case_id,
                verdict="REVISE",
                rationale=f"Tribunal LLM unavailable: {exc}",
                requires_human=True,
                decided_at=datetime.now(tz=timezone.utc).isoformat(),
            )

        verdict = TribunalVerdict(
            case_id=case.case_id,
            verdict=result.get("verdict", "REVISE"),
            rationale=result.get("rationale", ""),
            conditions=result.get("conditions", []),
            requires_human=result.get("requires_human", False),
            decided_at=datetime.now(tz=timezone.utc).isoformat(),
        )

        await self._log_verdict(case, verdict)
        log.info(
            "Tribunal [%s]: %s → %s",
            case.case_id, case.title, verdict.verdict
        )
        return verdict

    def _build_prompt(self, case: TribunalCase) -> str:
        objections_text = "\n".join(f"  - {o}" for o in case.objections)
        ctx = f"\n\nRelevanter Code:\n```\n{case.context}\n```" if case.context else ""
        return (
            f"**Fall:** {case.case_id} – {case.title}\n"
            f"**AWP:** {case.awp_id or 'N/A'}\n\n"
            f"**Vorschlag (@coder):**\n{case.proposal}\n\n"
            f"**Einwände:**\n{objections_text}"
            f"{ctx}"
        )

    async def _log_verdict(
        self, case: TribunalCase, verdict: TribunalVerdict
    ) -> None:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        record = {
            "case_id": case.case_id,
            "title": case.title,
            "awp_id": case.awp_id,
            "verdict": verdict.verdict,
            "rationale": verdict.rationale,
            "conditions": verdict.conditions,
            "requires_human": verdict.requires_human,
            "decided_at": verdict.decided_at,
        }
        with TRIBUNAL_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
