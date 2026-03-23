"""
AWP-078 – Latency Audit
Misst End-to-End Latenz von User-Command bis UI-Reaktion.

Messpunkte:
  T1: Command empfangen (API endpoint)
  T2: Agent-Pipeline gestartet
  T3: Agent-Pipeline abgeschlossen
  T4: WebSocket-Broadcast an UI gesendet
  T5: (estimated) Browser render

Ergebnis: data/latency_report.json + logs/latency_report.md

Python 3.12 | AsyncIO | contextvars
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncGenerator

log = logging.getLogger("jarvis.latency_audit")

REPORT_JSON = Path(__file__).parent.parent / "data" / "latency_report.json"
REPORT_MD   = Path(__file__).parent.parent / "logs" / "latency_report.md"
MAX_HISTORY = 200   # rolling window of measurements


@dataclass
class LatencySpan:
    trace_id: str
    label: str           # "api_receive" | "pipeline_start" | "pipeline_end" | "ws_broadcast"
    t_ns: int            # time.perf_counter_ns()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LatencyTrace:
    trace_id: str
    command: str
    spans: list[LatencySpan] = field(default_factory=list)
    completed: bool = False

    def duration_ms(self, from_label: str, to_label: str) -> float | None:
        t_from = next((s.t_ns for s in self.spans if s.label == from_label), None)
        t_to   = next((s.t_ns for s in self.spans if s.label == to_label), None)
        if t_from is None or t_to is None:
            return None
        return (t_to - t_from) / 1_000_000


@dataclass
class LatencySummary:
    sample_count: int
    p50_ms: float
    p95_ms: float
    p99_ms: float
    max_ms: float
    min_ms: float
    avg_ms: float


class LatencyAuditor:
    """
    Collects and analyses latency spans across the request lifecycle.

    Usage:
        auditor = LatencyAuditor()
        async with auditor.trace("search query") as t:
            t.mark("pipeline_start")
            await run_pipeline()
            t.mark("pipeline_end")
    """

    def __init__(self) -> None:
        self._traces: deque[LatencyTrace] = deque(maxlen=MAX_HISTORY)
        self._active: dict[str, LatencyTrace] = {}

    @asynccontextmanager
    async def trace(self, command: str) -> AsyncGenerator["TraceContext", None]:
        trace_id = f"{int(time.time() * 1000)}"
        trace = LatencyTrace(trace_id=trace_id, command=command)
        self._active[trace_id] = trace
        ctx = TraceContext(trace)
        ctx.mark("api_receive")
        try:
            yield ctx
            trace.completed = True
        finally:
            trace.completed = True
            ctx.mark("trace_end")
            del self._active[trace_id]
            self._traces.append(trace)
            total = trace.duration_ms("api_receive", "trace_end")
            log.info(
                "Latency [%s] %s: %.1f ms",
                trace_id, command[:40], total or -1,
            )

    def summarize(self, from_label: str = "api_receive", to_label: str = "pipeline_end") -> LatencySummary:
        durations = [
            d for t in self._traces
            if (d := t.duration_ms(from_label, to_label)) is not None
        ]
        if not durations:
            return LatencySummary(0, 0, 0, 0, 0, 0, 0)

        durations.sort()
        n = len(durations)
        return LatencySummary(
            sample_count=n,
            p50_ms=durations[int(n * 0.50)],
            p95_ms=durations[int(n * 0.95)],
            p99_ms=durations[min(int(n * 0.99), n - 1)],
            max_ms=durations[-1],
            min_ms=durations[0],
            avg_ms=sum(durations) / n,
        )

    def export(self) -> None:
        summary = self.summarize()
        data = {
            "generated_at": datetime.now(tz=timezone.utc).isoformat(),
            "summary": asdict(summary),
            "recent_traces": [
                {
                    "trace_id": t.trace_id,
                    "command": t.command,
                    "total_ms": t.duration_ms("api_receive", "trace_end"),
                    "pipeline_ms": t.duration_ms("pipeline_start", "pipeline_end"),
                    "spans": len(t.spans),
                }
                for t in list(self._traces)[-20:]
            ],
        }
        REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
        REPORT_JSON.write_text(json.dumps(data, indent=2), encoding="utf-8")

        md_lines = [
            "# Jarvis 4.0 – Latency Audit Report",
            f"**Generated:** {data['generated_at']}",
            "",
            "## End-to-End Latency Summary",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Samples | {summary.sample_count} |",
            f"| P50 | {summary.p50_ms:.1f} ms |",
            f"| P95 | {summary.p95_ms:.1f} ms |",
            f"| P99 | {summary.p99_ms:.1f} ms |",
            f"| Max | {summary.max_ms:.1f} ms |",
            f"| Min | {summary.min_ms:.1f} ms |",
            f"| Avg | {summary.avg_ms:.1f} ms |",
            "",
            "## Recent Traces",
        ]
        for tr in data["recent_traces"]:
            total = f"{tr['total_ms']:.1f}" if tr["total_ms"] else "N/A"
            pipeline = f"{tr['pipeline_ms']:.1f}" if tr["pipeline_ms"] else "N/A"
            md_lines.append(
                f"- `{tr['trace_id']}` — `{tr['command'][:40]}` "
                f"total={total}ms pipeline={pipeline}ms"
            )

        REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
        REPORT_MD.write_text("\n".join(md_lines), encoding="utf-8")
        log.info("Latency report exported: %s", REPORT_JSON)


class TraceContext:
    """Returned by LatencyAuditor.trace() context manager."""

    def __init__(self, trace: LatencyTrace) -> None:
        self._trace = trace

    def mark(self, label: str, **metadata: Any) -> None:
        self._trace.spans.append(LatencySpan(
            trace_id=self._trace.trace_id,
            label=label,
            t_ns=time.perf_counter_ns(),
            metadata=metadata,
        ))


# Module-level singleton
_auditor: LatencyAuditor | None = None


def get_auditor() -> LatencyAuditor:
    global _auditor
    if _auditor is None:
        _auditor = LatencyAuditor()
    return _auditor
