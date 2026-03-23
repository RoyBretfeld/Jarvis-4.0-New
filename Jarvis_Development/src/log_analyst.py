"""
AWP-049 – Log Analysis Agent
Background task: analysiert nächtlich alle logs/ und erstellt
daily_efficiency_report.md mit Metriken, Fehler-Mustern und Empfehlungen.
Python 3.12 | AsyncIO | kann als Cron-Job oder asyncio.Task laufen
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

log = logging.getLogger("jarvis.log_analyst")

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
LOG_DIR      = PROJECT_ROOT / "logs"
REPORT_DIR   = PROJECT_ROOT / "logs" / "daily"


# ─────────────────────────────────────────────
# Log parsers
# ─────────────────────────────────────────────

_LOG_LINE_RE = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})"
    r",\d+\s+\[(?P<level>\w+)\]\s+"
    r"(?P<logger>[\w.]+):\s+"
    r"(?P<message>.+)$"
)
_JSON_LINE_RE = re.compile(r"^\{.*\}$")


def _parse_log_file(path: Path) -> list[dict[str, str]]:
    entries = []
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            m = _LOG_LINE_RE.match(line)
            if m:
                entries.append(m.groupdict())
            elif _JSON_LINE_RE.match(line):
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    except OSError:
        pass
    return entries


# ─────────────────────────────────────────────
# Metrics aggregation
# ─────────────────────────────────────────────

def _aggregate(entries: list[dict]) -> dict[str, Any]:
    level_counts: Counter = Counter()
    error_messages: list[str] = []
    service_counts: Counter = Counter()
    self_heals = 0
    pipeline_runs = 0
    pipeline_successes = 0

    for e in entries:
        level = e.get("level", e.get("levelname", "INFO")).upper()
        level_counts[level] += 1
        logger = e.get("logger", e.get("service", "unknown"))
        service_counts[logger] += 1
        msg = e.get("message", e.get("msg", ""))
        if level == "ERROR":
            error_messages.append(msg[:120])
        if "RESTARTED" in msg or "self-heal" in msg.lower():
            self_heals += 1
        if "Pipeline" in msg:
            pipeline_runs += 1
            if "SUCCESS" in msg:
                pipeline_successes += 1

    top_errors: Counter = Counter(error_messages)
    return {
        "total_entries": len(entries),
        "level_counts": dict(level_counts),
        "top_services": service_counts.most_common(10),
        "top_errors": top_errors.most_common(5),
        "self_heals": self_heals,
        "pipeline_runs": pipeline_runs,
        "pipeline_success_rate": (
            round(pipeline_successes / pipeline_runs * 100, 1)
            if pipeline_runs else None
        ),
    }


# ─────────────────────────────────────────────
# Heartbeat report loader
# ─────────────────────────────────────────────

def _load_heartbeat() -> dict | None:
    p = LOG_DIR / "heartbeat_latest.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


# ─────────────────────────────────────────────
# Report generator
# ─────────────────────────────────────────────

def _build_report(date_str: str, metrics: dict, hb: dict | None) -> str:
    lines = [
        f"# Jarvis 4.0 – Daily Efficiency Report",
        f"**Date:** {date_str}",
        f"**Generated:** {datetime.now(tz=timezone.utc).isoformat()}",
        "",
        "---",
        "",
        "## 📊 Log Summary",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total log entries | {metrics['total_entries']} |",
    ]
    for level, count in sorted(metrics["level_counts"].items()):
        lines.append(f"| {level} entries | {count} |")
    lines += [
        f"| Self-heals (container restarts) | {metrics['self_heals']} |",
        f"| Pipeline runs | {metrics['pipeline_runs']} |",
        f"| Pipeline success rate | {metrics['pipeline_success_rate'] or 'N/A'}% |",
        "",
        "## 🏆 Top Services (by log volume)",
        "",
    ]
    for svc, cnt in metrics["top_services"][:8]:
        lines.append(f"- `{svc}`: {cnt} entries")

    lines += ["", "## ⚠️ Top Error Patterns", ""]
    if metrics["top_errors"]:
        for msg, cnt in metrics["top_errors"]:
            lines.append(f"- ({cnt}×) `{msg}`")
    else:
        lines.append("_No errors recorded. ✅_")

    lines += ["", "## 💓 Heartbeat Status", ""]
    if hb:
        lines.append(f"- Overall: **{hb.get('overall', '?')}**")
        lines.append(f"- Self-heals this run: {hb.get('self_heals', 0)}")
        for c in hb.get("containers", []):
            icon = "✅" if c["status"] == "healthy" else "❌"
            lines.append(f"  {icon} `{c['name']}`: {c['status']}")
        ollama = hb.get("ollama", {})
        lines.append(
            f"- Ollama: {'✅' if ollama.get('reachable') else '❌'} "
            f"{ollama.get('message', '')}"
        )
    else:
        lines.append("_No heartbeat data available._")

    lines += [
        "",
        "## 🔧 Recommendations",
        "",
    ]
    recs = []
    if metrics["level_counts"].get("ERROR", 0) > 10:
        recs.append("High error rate detected – investigate `logs/api.log`.")
    if metrics["self_heals"] > 3:
        recs.append("Frequent container restarts – check Docker resource limits.")
    if metrics["pipeline_success_rate"] is not None and metrics["pipeline_success_rate"] < 80:
        recs.append("Pipeline success rate below 80% – review test failures.")
    if not recs:
        recs.append("System operating normally. No action required.")
    for r in recs:
        lines.append(f"- {r}")

    lines += ["", "---", "_Auto-generated by Jarvis Log Analyst (AWP-049)_"]
    return "\n".join(lines)


# ─────────────────────────────────────────────
# Main task
# ─────────────────────────────────────────────

async def run_analysis() -> Path:
    """Run analysis on all .log files, write daily report. Returns report path."""
    loop = asyncio.get_event_loop()
    date_str = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    log.info("Log analysis started for %s", date_str)

    # Parse all log files in background thread (I/O bound but blocking)
    all_entries: list[dict] = []
    log_files = list(LOG_DIR.glob("*.log"))
    for lf in log_files:
        entries = await loop.run_in_executor(None, _parse_log_file, lf)
        all_entries.extend(entries)

    log.info("Parsed %d entries from %d files", len(all_entries), len(log_files))
    metrics = await loop.run_in_executor(None, _aggregate, all_entries)
    hb = await loop.run_in_executor(None, _load_heartbeat)
    report_text = _build_report(date_str, metrics, hb)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / f"daily_efficiency_report_{date_str}.md"
    report_path.write_text(report_text, encoding="utf-8")

    # Also write latest symlink
    latest = LOG_DIR / "daily_efficiency_report.md"
    latest.write_text(report_text, encoding="utf-8")

    log.info("Daily report written: %s", report_path)
    return report_path


async def run_scheduled(hour: int = 2, minute: int = 0) -> None:
    """Run analysis every day at specified UTC hour:minute."""
    log.info("Log analyst scheduler running (daily at %02d:%02dZ)", hour, minute)
    while True:
        now = datetime.now(tz=timezone.utc)
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if next_run <= now:
            next_run = next_run.replace(day=next_run.day + 1)
        wait_secs = (next_run - now).total_seconds()
        log.info("Next log analysis in %.0f seconds", wait_secs)
        await asyncio.sleep(wait_secs)
        try:
            await run_analysis()
        except Exception as exc:
            log.error("Log analysis failed: %s", exc, exc_info=True)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    import sys
    if "--now" in sys.argv:
        asyncio.run(run_analysis())
    else:
        asyncio.run(run_scheduled())
