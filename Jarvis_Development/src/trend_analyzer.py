"""
AWP-063 – Trend Analyzer
Analysiert logs/ der letzten N AWP-Zyklen, erkennt Fehlermuster
und schreibt antizipative Warnungen in logs/trend_report.md.
Python 3.12 | AsyncIO
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

log = logging.getLogger("jarvis.trend_analyzer")

LOG_DIR      = Path(__file__).parent.parent / "logs"
REPORT_PATH  = LOG_DIR / "trend_report.md"

# Patterns we track
_ERROR_CATS = {
    "import":     re.compile(r"ImportError|ModuleNotFoundError", re.I),
    "connection": re.compile(r"ConnectionRefusedError|ConnectionError|ECONNREFUSED", re.I),
    "timeout":    re.compile(r"TimeoutError|timed out", re.I),
    "path":       re.compile(r"FileNotFoundError|No such file", re.I),
    "permission": re.compile(r"PermissionError|Access is denied", re.I),
    "memory":     re.compile(r"MemoryError|OOM|out of memory", re.I),
    "assertion":  re.compile(r"AssertionError", re.I),
    "type":       re.compile(r"TypeError|AttributeError", re.I),
}

_SELF_HEAL_RE = re.compile(r"Self-heal|RESTARTED", re.I)
_PIPELINE_RE  = re.compile(r"Pipeline (SUCCESS|FAIL|GATE|complete)", re.I)


class TrendReport:
    def __init__(self) -> None:
        self.window_days: int = 0
        self.total_errors: int = 0
        self.error_by_category: dict[str, int] = {}
        self.top_error_messages: list[tuple[str, int]] = []
        self.self_heal_count: int = 0
        self.pipeline_success_rate: float | None = None
        self.recurring_errors: list[str] = []
        self.predictions: list[str] = []
        self.generated_at: str = ""


async def analyze(window_days: int = 60) -> TrendReport:
    report = TrendReport()
    report.window_days = window_days
    report.generated_at = datetime.now(tz=timezone.utc).isoformat()

    loop = asyncio.get_event_loop()
    all_lines: list[str] = []

    log_files = list(LOG_DIR.glob("*.log")) + list(LOG_DIR.glob("daily/*.md"))
    for lf in log_files:
        try:
            text = await loop.run_in_executor(
                None, lambda p=lf: p.read_text(encoding="utf-8", errors="replace")
            )
            all_lines.extend(text.splitlines())
        except OSError:
            pass

    # Categorize errors
    cat_counts: Counter = Counter()
    error_msgs: list[str] = []
    self_heals = 0
    pipeline_runs = 0
    pipeline_ok = 0

    for line in all_lines:
        if "ERROR" in line or "error" in line.lower():
            for cat, pattern in _ERROR_CATS.items():
                if pattern.search(line):
                    cat_counts[cat] += 1
                    error_msgs.append(line.strip()[:100])
        if _SELF_HEAL_RE.search(line):
            self_heals += 1
        m = _PIPELINE_RE.search(line)
        if m:
            pipeline_runs += 1
            if "SUCCESS" in m.group(1).upper() or "complete" in m.group(1).lower():
                pipeline_ok += 1

    report.total_errors = sum(cat_counts.values())
    report.error_by_category = dict(cat_counts.most_common())
    report.top_error_messages = Counter(error_msgs).most_common(5)
    report.self_heal_count = self_heals
    if pipeline_runs > 0:
        report.pipeline_success_rate = round(pipeline_ok / pipeline_runs * 100, 1)

    # Recurring errors: appeared > 3 times
    report.recurring_errors = [
        msg for msg, cnt in Counter(error_msgs).most_common() if cnt >= 3
    ][:5]

    # Predictive warnings
    preds = []
    if cat_counts.get("connection", 0) > 5:
        preds.append("⚠ Häufige Connection-Fehler → RAG-Container möglicherweise instabil. "
                     "Empfehlung: health-check interval verkürzen.")
    if cat_counts.get("import", 0) > 3:
        preds.append("⚠ Mehrere ImportErrors → requirements.txt möglicherweise unvollständig. "
                     "Empfehlung: `pip-audit` ausführen.")
    if self_heals > 5:
        preds.append("⚠ Häufige Self-Heals → Docker resource limits möglicherweise zu niedrig.")
    if report.pipeline_success_rate is not None and report.pipeline_success_rate < 70:
        preds.append("⚠ Pipeline-Erfolgsrate unter 70% → Tester-Konfiguration überprüfen.")
    if not preds:
        preds.append("✅ Keine kritischen Muster erkannt. System stabil.")
    report.predictions = preds

    await loop.run_in_executor(None, lambda: _write_report(report))
    log.info("Trend analysis complete: %d errors, %d predictions", report.total_errors, len(preds))
    return report


def _write_report(r: TrendReport) -> None:
    lines = [
        f"# Jarvis 4.0 – Trend Analysis Report",
        f"**Analysefenster:** {r.window_days} Tage  |  **Generiert:** {r.generated_at}",
        "",
        "## Fehler-Statistik",
        f"- Gesamtfehler: **{r.total_errors}**",
        f"- Self-Heals: **{r.self_heal_count}**",
        f"- Pipeline-Erfolgsrate: **{r.pipeline_success_rate or 'N/A'}%**",
        "",
        "## Fehler nach Kategorie",
    ]
    for cat, cnt in sorted(r.error_by_category.items(), key=lambda x: -x[1]):
        bar = "█" * min(cnt, 20)
        lines.append(f"- `{cat:<12}` {bar} ({cnt})")
    lines += ["", "## Wiederkehrende Fehlermuster"]
    if r.recurring_errors:
        for msg in r.recurring_errors:
            lines.append(f"- `{msg}`")
    else:
        lines.append("_Keine wiederkehrenden Fehler._")
    lines += ["", "## 🔮 Prognosen & Empfehlungen"]
    for p in r.predictions:
        lines.append(f"- {p}")
    lines += ["", "---", "_Auto-generiert von Jarvis Trend Analyzer (AWP-063)_"]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    import asyncio as _asyncio
    logging.basicConfig(level=logging.INFO)
    _asyncio.run(analyze())
