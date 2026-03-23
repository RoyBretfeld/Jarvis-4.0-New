"""
AWP-068 – Instruction Weight Manager
Temporäres Regelgewicht für Notfallkorrekturen.

Beispiel: Wenn Security-Agent zu oft fälschlicherweise vetot,
kann ein Operator die Gewichtung temporär reduzieren (TTL-basiert).

Regeln werden in data/instruction_weights.json gespeichert.
Nach Ablauf des TTL werden sie automatisch zurückgesetzt.

Python 3.12
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

log = logging.getLogger("jarvis.instruction_weight")

WEIGHTS_PATH = Path(__file__).parent.parent / "data" / "instruction_weights.json"

# Default weights (1.0 = normal, >1 = amplified, <1 = dampened)
DEFAULT_WEIGHTS: dict[str, float] = {
    "security_veto":       1.0,
    "test_gate":           1.0,
    "tribunal_override":   1.0,
    "human_confirmation":  1.0,
    "rag_recall":          1.0,
    "doc_sync":            1.0,
}


@dataclass
class WeightRule:
    key: str
    weight: float
    reason: str
    set_by: str
    expires_at: str       # ISO-8601 or "" for permanent
    permanent: bool = False


class InstructionWeightManager:
    """Load, set, and expire instruction weights."""

    def __init__(self) -> None:
        self._rules: dict[str, WeightRule] = {}
        self._load()

    # ── Persistence ────────────────────────────────────────────────────────

    def _load(self) -> None:
        try:
            raw = json.loads(WEIGHTS_PATH.read_text(encoding="utf-8"))
            for k, v in raw.items():
                self._rules[k] = WeightRule(**v)
        except (OSError, json.JSONDecodeError, TypeError):
            pass

    def _save(self) -> None:
        WEIGHTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        data = {k: asdict(v) for k, v in self._rules.items()}
        WEIGHTS_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")

    # ── Public API ─────────────────────────────────────────────────────────

    def get(self, key: str) -> float:
        """Return current weight for key, respecting TTL expiry."""
        self._expire()
        rule = self._rules.get(key)
        if rule is None:
            return DEFAULT_WEIGHTS.get(key, 1.0)
        return rule.weight

    def set_weight(
        self,
        key: str,
        weight: float,
        reason: str,
        set_by: str = "operator",
        ttl_hours: float | None = 24.0,
    ) -> WeightRule:
        """
        Set a temporary (or permanent) weight for an instruction key.

        Args:
            key:       Weight key (e.g. "security_veto")
            weight:    New weight factor (0.0–2.0)
            reason:    Human-readable justification
            set_by:    Who issued the override
            ttl_hours: Hours until auto-expiry (None = permanent)
        """
        if not 0.0 <= weight <= 2.0:
            raise ValueError(f"Weight must be in [0.0, 2.0], got {weight}")

        if ttl_hours is not None:
            expires_at = (
                datetime.now(tz=timezone.utc) + timedelta(hours=ttl_hours)
            ).isoformat()
            permanent = False
        else:
            expires_at = ""
            permanent = True

        rule = WeightRule(
            key=key,
            weight=weight,
            reason=reason,
            set_by=set_by,
            expires_at=expires_at,
            permanent=permanent,
        )
        self._rules[key] = rule
        self._save()
        log.warning(
            "Instruction weight set: %s=%.2f by %s (ttl=%s h) — %s",
            key, weight, set_by, ttl_hours, reason,
        )
        return rule

    def reset(self, key: str) -> None:
        """Reset key to default weight."""
        self._rules.pop(key, None)
        self._save()
        log.info("Instruction weight reset: %s", key)

    def reset_all(self) -> None:
        """Reset all weights to defaults."""
        self._rules.clear()
        self._save()
        log.info("All instruction weights reset")

    def list_active(self) -> list[WeightRule]:
        """Return all non-expired rules."""
        self._expire()
        return list(self._rules.values())

    def status_report(self) -> str:
        active = self.list_active()
        if not active:
            return "All instruction weights at default (1.0)."
        lines = ["**Active Instruction Weight Overrides:**"]
        for r in active:
            exp = f"expires {r.expires_at[:16]}" if r.expires_at else "permanent"
            lines.append(
                f"- `{r.key}` = **{r.weight:.2f}** ({exp}) "
                f"by {r.set_by}: _{r.reason}_"
            )
        return "\n".join(lines)

    def _expire(self) -> None:
        now = datetime.now(tz=timezone.utc)
        expired = [
            k for k, r in self._rules.items()
            if not r.permanent and r.expires_at
            and datetime.fromisoformat(r.expires_at) <= now
        ]
        for k in expired:
            log.info("Instruction weight expired: %s", k)
            del self._rules[k]
        if expired:
            self._save()


# Module-level singleton
_manager: InstructionWeightManager | None = None


def get_manager() -> InstructionWeightManager:
    global _manager
    if _manager is None:
        _manager = InstructionWeightManager()
    return _manager


def get_weight(key: str) -> float:
    """Convenience shortcut."""
    return get_manager().get(key)
