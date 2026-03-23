"""
AWP-045 – Context Pruner
Bereinigt den Token-Kontext von LLM-Anfragen automatisch,
wenn eine AWP-Kette zu lang wird (Präzisions-Sicherung).

Strategie:
  1. FIFO:         Älteste Nachrichten werden verworfen (sliding window).
  2. Summarize:    Lange Verläufe werden durch den LLM zusammengefasst.
  3. RAG-Replace:  Wiederholende Kontext-Blöcke werden durch RAG-Zitate ersetzt.

Token-Zählung: tiktoken (cl100k_base) als Approximation für Qwen 14b.
Python 3.12 | AsyncIO
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

log = logging.getLogger("jarvis.context_pruner")

# Qwen 14b effective context window (conservative limit)
DEFAULT_MAX_TOKENS = 8_192
SUMMARY_TRIGGER_PCT = 0.80      # prune when context reaches 80% of limit
SUMMARY_TARGET_PCT  = 0.40      # summarize down to 40%


# ─────────────────────────────────────────────
# Message types
# ─────────────────────────────────────────────

@dataclass
class ContextMessage:
    role: str                   # "system" | "user" | "assistant"
    content: str
    token_count: int = 0
    pinned: bool = False        # pinned messages are never pruned


@dataclass
class PruneReport:
    original_tokens: int
    final_tokens: int
    messages_removed: int
    messages_summarized: int
    strategy_used: str


# ─────────────────────────────────────────────
# Token counter
# ─────────────────────────────────────────────

def count_tokens(text: str) -> int:
    """Fast token approximation. Uses tiktoken if available, else char-based."""
    try:
        import tiktoken  # type: ignore
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except ImportError:
        # Fallback: ~4 chars per token (reasonable for German/English mix)
        return max(1, len(text) // 4)


def count_message_tokens(msg: ContextMessage) -> int:
    return count_tokens(msg.content) + 4   # +4 for role/formatting overhead


# ─────────────────────────────────────────────
# Pruner
# ─────────────────────────────────────────────

class ContextPruner:
    """
    Manages a conversation context list and prunes it when needed.

    Usage:
        pruner = ContextPruner(max_tokens=8192)
        pruner.add("user", "Implement feature X")
        pruner.add("assistant", "Here is the code...")
        messages = await pruner.get_pruned()
    """

    def __init__(
        self,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        ollama_url: str | None = None,
    ) -> None:
        self.max_tokens = max_tokens
        self._messages: list[ContextMessage] = []
        self._ollama_url = ollama_url

    # ── Public API ────────────────────────────

    def add(self, role: str, content: str, pinned: bool = False) -> None:
        msg = ContextMessage(role=role, content=content, pinned=pinned)
        msg.token_count = count_message_tokens(msg)
        self._messages.append(msg)

    def total_tokens(self) -> int:
        return sum(m.token_count for m in self._messages)

    def needs_pruning(self) -> bool:
        return self.total_tokens() > int(self.max_tokens * SUMMARY_TRIGGER_PCT)

    async def get_pruned(self) -> list[dict[str, str]]:
        """Return messages as dicts, pruning first if necessary."""
        if self.needs_pruning():
            report = await self._prune()
            log.info(
                "Context pruned: %d→%d tokens, strategy=%s removed=%d summarized=%d",
                report.original_tokens, report.final_tokens,
                report.strategy_used, report.messages_removed,
                report.messages_summarized,
            )
        return [{"role": m.role, "content": m.content} for m in self._messages]

    # ── Pruning strategies ────────────────────

    async def _prune(self) -> PruneReport:
        original = self.total_tokens()
        target = int(self.max_tokens * SUMMARY_TARGET_PCT)

        # Strategy 1: FIFO – drop oldest non-pinned non-system messages
        removed = self._fifo_drop(target)
        if self.total_tokens() <= target:
            return PruneReport(original, self.total_tokens(), removed, 0, "fifo")

        # Strategy 2: Summarize middle section via LLM
        summarized = await self._summarize_middle(target)
        if summarized > 0:
            return PruneReport(original, self.total_tokens(), removed, summarized, "summarize")

        # Strategy 3: Hard truncate (last resort)
        self._hard_truncate(target)
        return PruneReport(original, self.total_tokens(), removed, 0, "truncate")

    def _fifo_drop(self, target_tokens: int) -> int:
        """Remove oldest non-pinned, non-system messages."""
        removed = 0
        i = 0
        while self.total_tokens() > target_tokens and i < len(self._messages):
            msg = self._messages[i]
            if not msg.pinned and msg.role != "system":
                self._messages.pop(i)
                removed += 1
            else:
                i += 1
        return removed

    async def _summarize_middle(self, target_tokens: int) -> int:
        """Summarize the middle N messages using Ollama."""
        if not self._ollama_url:
            return 0
        try:
            import aiohttp  # type: ignore

            # Find summarizable range (non-pinned, middle third)
            n = len(self._messages)
            start = n // 4
            end = 3 * n // 4
            to_summarize = [m for m in self._messages[start:end] if not m.pinned]
            if not to_summarize:
                return 0

            block = "\n\n".join(f"[{m.role}]: {m.content}" for m in to_summarize)
            prompt = (
                "Summarize the following conversation excerpt in 3-5 sentences, "
                "preserving key decisions and code changes:\n\n" + block
            )
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self._ollama_url}/api/generate",
                    json={"model": "mistral", "prompt": prompt, "stream": False},
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as resp:
                    if resp.status != 200:
                        return 0
                    data = await resp.json()
                    summary = data.get("response", "").strip()

            if not summary:
                return 0

            # Replace summarized messages with single summary message
            count = len(to_summarize)
            self._messages = (
                self._messages[:start]
                + [ContextMessage(
                    role="assistant",
                    content=f"[Summary of {count} messages]: {summary}",
                    token_count=count_tokens(summary) + 4,
                    pinned=True,
                )]
                + self._messages[end:]
            )
            return count
        except Exception as exc:
            log.warning("Summarization failed: %s", exc)
            return 0

    def _hard_truncate(self, target_tokens: int) -> None:
        """Keep only system messages + most recent messages up to target."""
        system_msgs = [m for m in self._messages if m.role == "system"]
        rest = [m for m in self._messages if m.role != "system"]
        # Keep most recent
        kept: list[ContextMessage] = []
        budget = target_tokens - sum(m.token_count for m in system_msgs)
        for msg in reversed(rest):
            if budget - msg.token_count >= 0:
                kept.insert(0, msg)
                budget -= msg.token_count
            else:
                break
        self._messages = system_msgs + kept

    def reset(self) -> None:
        """Clear all non-pinned messages."""
        self._messages = [m for m in self._messages if m.pinned]
