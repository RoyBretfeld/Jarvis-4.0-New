"""
AWP-065 – Auto-Doc-Sync
Überwacht Änderungen in src/ und aktualisiert automatisch
die strategy/*.md Dokumentation wenn sich Standards geändert haben.

Strategie:
  1. Scannt Fingerprints aller .py Dateien in src/
  2. Bei Änderung → extrahiert Docstrings + Signaturen via AST
  3. Gleicht gegen strategy/*.md ab
  4. Schreibt Diff-basierte Updates in strategy/auto_updates/

Python 3.12 | AsyncIO | AST
"""

from __future__ import annotations

import ast
import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

log = logging.getLogger("jarvis.doc_sync")

SRC_DIR      = Path(__file__).parent
STRATEGY_DIR = SRC_DIR.parent / "strategy"
AUTO_DIR     = STRATEGY_DIR / "auto_updates"
FINGERPRINT_CACHE = SRC_DIR.parent / "data" / "doc_sync_fingerprints.json"

# Strategy files that map to source modules
DOC_MAP: dict[str, list[str]] = {
    "architecture.md":   ["memory_interface", "ingest_docs", "vector_pruner"],
    "agent_pipeline.md": ["agents/orchestrator", "agents/coder_agent",
                          "agents/tester_agent", "agents/security_agent"],
    "rag_strategy.md":   ["memory_interface", "ingest_docs", "librarian"],
    "security.md":       ["agents/security_agent", "mcp_client"],
    "performance.md":    ["os_bridge", "context_pruner", "heat_control"],
}


@dataclass
class ModuleSnapshot:
    path: str
    fingerprint: str
    classes: list[str] = field(default_factory=list)
    functions: list[str] = field(default_factory=list)
    module_doc: str = ""
    changed_since: str = ""


def _fingerprint(path: Path) -> str:
    try:
        content = path.read_bytes()
        return hashlib.sha256(content).hexdigest()[:16]
    except OSError:
        return ""


def _extract_api(path: Path) -> tuple[list[str], list[str], str]:
    """Extract public classes, functions, and module docstring via AST."""
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source)
    except (OSError, SyntaxError):
        return [], [], ""

    module_doc = ast.get_docstring(tree) or ""
    classes: list[str] = []
    functions: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            doc = ast.get_docstring(node) or ""
            classes.append(f"**`{node.name}`** — {doc[:80]}" if doc else f"**`{node.name}`**")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                # Build simple signature
                args = [a.arg for a in node.args.args]
                sig = f"{node.name}({', '.join(args)})"
                doc = ast.get_docstring(node) or ""
                functions.append(f"`{sig}` — {doc[:80]}" if doc else f"`{sig}`")

    return classes, functions, module_doc


def _load_fingerprints() -> dict[str, str]:
    try:
        return json.loads(FINGERPRINT_CACHE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _save_fingerprints(fp: dict[str, str]) -> None:
    FINGERPRINT_CACHE.parent.mkdir(parents=True, exist_ok=True)
    FINGERPRINT_CACHE.write_text(json.dumps(fp, indent=2), encoding="utf-8")


def scan_modules() -> list[ModuleSnapshot]:
    """Scan all src/ Python files and detect changes."""
    old_fp = _load_fingerprints()
    new_fp: dict[str, str] = {}
    snapshots: list[ModuleSnapshot] = []

    for py_file in SRC_DIR.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        rel = py_file.relative_to(SRC_DIR)
        key = str(rel).replace("\\", "/").removesuffix(".py")
        current = _fingerprint(py_file)
        new_fp[key] = current

        classes, functions, module_doc = _extract_api(py_file)
        snap = ModuleSnapshot(
            path=key,
            fingerprint=current,
            classes=classes,
            functions=functions,
            module_doc=module_doc,
        )
        if old_fp.get(key) != current:
            snap.changed_since = datetime.now(tz=timezone.utc).isoformat()
            log.info("Module changed: %s", key)
        snapshots.append(snap)

    _save_fingerprints(new_fp)
    return snapshots


def _modules_for_doc(doc_name: str) -> list[str]:
    return DOC_MAP.get(doc_name, [])


def _generate_update_section(
    doc_name: str,
    changed: list[ModuleSnapshot],
) -> str:
    """Build a markdown patch section for changed modules."""
    ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"## Auto-Update: {doc_name}",
        f"_Generiert: {ts}_",
        "",
        "### Geänderte Module",
    ]
    for snap in changed:
        lines.append(f"\n#### `{snap.path}`")
        if snap.module_doc:
            lines.append(f"> {snap.module_doc[:200]}")
        if snap.classes:
            lines.append("\n**Klassen:**")
            for c in snap.classes[:10]:
                lines.append(f"- {c}")
        if snap.functions:
            lines.append("\n**Öffentliche Funktionen:**")
            for f in snap.functions[:20]:
                lines.append(f"- {f}")
    lines.append("\n---")
    return "\n".join(lines)


async def sync_docs(loop: asyncio.AbstractEventLoop | None = None) -> dict[str, int]:
    """
    Main entry point. Scans src/, detects changes, writes auto-update patches.
    Returns dict of {doc_name: num_modules_updated}.
    """
    if loop is None:
        loop = asyncio.get_event_loop()

    snapshots = await loop.run_in_executor(None, scan_modules)
    changed_map: dict[str, ModuleSnapshot] = {
        s.path: s for s in snapshots if s.changed_since
    }

    if not changed_map:
        log.info("Doc sync: no changes detected")
        return {}

    AUTO_DIR.mkdir(parents=True, exist_ok=True)
    results: dict[str, int] = {}

    for doc_name, module_keys in DOC_MAP.items():
        relevant = [changed_map[k] for k in module_keys if k in changed_map]
        if not relevant:
            continue

        patch_text = _generate_update_section(doc_name, relevant)
        out_file = AUTO_DIR / f"patch_{doc_name}"
        await loop.run_in_executor(
            None,
            lambda t=patch_text, p=out_file: p.write_text(t, encoding="utf-8"),
        )
        log.info("Doc patch written: %s (%d modules)", doc_name, len(relevant))
        results[doc_name] = len(relevant)

    # Write summary
    summary_lines = [
        "# Doc Sync Summary",
        f"**Run:** {datetime.now(tz=timezone.utc).isoformat()}",
        f"**Changed modules:** {len(changed_map)}",
        "",
        "| Document | Updated Modules |",
        "|----------|----------------|",
    ]
    for doc, count in results.items():
        summary_lines.append(f"| {doc} | {count} |")

    summary_path = AUTO_DIR / "sync_summary.md"
    await loop.run_in_executor(
        None,
        lambda: summary_path.write_text("\n".join(summary_lines), encoding="utf-8"),
    )
    log.info("Doc sync complete: %d docs updated", len(results))
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    r = asyncio.run(sync_docs())
    print(f"Updated: {r}")
