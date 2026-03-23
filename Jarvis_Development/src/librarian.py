"""
Jarvis 4.0 – Skill Librarian
Parst .md-Dateien aus /skills/ und extrahiert YAML-Frontmatter-Metadaten.
Python 3.12 | RB-Protokoll: Transparenz (Glass-Box)
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

log = logging.getLogger("jarvis.librarian")

# YAML-Frontmatter zwischen den ersten beiden "---" Trennern
_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


# ─────────────────────────────────────────────
# Data model
# ─────────────────────────────────────────────
@dataclass
class Skill:
    name: str
    description: str
    version: str
    tools: list[str]
    body: str                   # Markdown-Inhalt ohne Frontmatter
    source_path: Path
    raw_meta: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return f"Skill({self.name!r} v{self.version}, tools={self.tools})"


# ─────────────────────────────────────────────
# YAML-Parser (minimalistisch, kein PyYAML-Import nötig)
# Unterstützt: str, list (- item), bool, int
# ─────────────────────────────────────────────
def _parse_yaml_block(block: str) -> dict[str, Any]:
    """Parse simple key: value YAML (no nested objects)."""
    result: dict[str, Any] = {}
    current_key: str | None = None
    current_list: list[str] | None = None

    for raw_line in block.splitlines():
        line = raw_line.rstrip()

        # List item belonging to previous key
        if line.startswith("- ") and current_key and current_list is not None:
            current_list.append(line[2:].strip().strip('"').strip("'"))
            continue

        # Flush pending list
        if current_list is not None and current_key is not None:
            result[current_key] = current_list
            current_list = None
            current_key = None

        if ":" not in line:
            continue

        key, _, raw_val = line.partition(":")
        key = key.strip().strip('"').strip("'")
        val = raw_val.strip().strip('"').strip("'")

        if val == "":
            # Next lines expected to be a list
            current_key = key
            current_list = []
        elif val.startswith("[") and val.endswith("]"):
            # Inline list: ["a", "b"]
            items = [i.strip().strip('"').strip("'") for i in val[1:-1].split(",")]
            result[key] = [i for i in items if i]
        elif val.lower() in ("true", "false"):
            result[key] = val.lower() == "true"
        elif val.isdigit():
            result[key] = int(val)
        else:
            result[key] = val

    # Flush trailing list
    if current_list is not None and current_key is not None:
        result[current_key] = current_list

    return result


def _clean_escaped_markdown(text: str) -> str:
    """Remove backslash-escapes injected by some Markdown exporters (\\# -> #)."""
    return re.sub(r"\\([#*\-_\[\]|>])", r"\1", text)


# ─────────────────────────────────────────────
# Core parsing
# ─────────────────────────────────────────────
def parse_skill_file(path: Path) -> Skill | None:
    """Parse a single skill .md file. Returns None on parse failure."""
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        log.error("Cannot read %s: %s", path, exc)
        return None

    raw = _clean_escaped_markdown(raw)
    match = _FRONTMATTER_RE.match(raw)

    if not match:
        log.warning("No YAML frontmatter found in %s – skipping.", path.name)
        return None

    meta = _parse_yaml_block(match.group(1))
    body = raw[match.end():].strip()

    return Skill(
        name=str(meta.get("name", path.stem)),
        description=str(meta.get("description", "")),
        version=str(meta.get("version", "0.0.0")),
        tools=meta.get("tools", []),
        body=body,
        source_path=path,
        raw_meta=meta,
    )


# ─────────────────────────────────────────────
# Directory scan
# ─────────────────────────────────────────────
def load_skills(skills_dir: Path) -> list[Skill]:
    """Load all .md skill files from a directory."""
    if not skills_dir.is_dir():
        log.error("Skills directory not found: %s", skills_dir)
        return []

    skills: list[Skill] = []
    md_files = sorted(skills_dir.glob("*.md"))
    log.info("Scanning %d .md files in %s", len(md_files), skills_dir)

    for path in md_files:
        skill = parse_skill_file(path)
        if skill:
            log.info("  Loaded: %s", skill)
            skills.append(skill)
        else:
            log.warning("  Skipped: %s", path.name)

    log.info("Skill-Librarian: %d/%d skills loaded.", len(skills), len(md_files))
    return skills


def get_skill_by_name(skills: list[Skill], name: str) -> Skill | None:
    """Case-insensitive lookup by skill name."""
    needle = name.lower()
    return next((s for s in skills if s.name.lower() == needle), None)


# ─────────────────────────────────────────────
# CLI entry point
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")

    target = Path(sys.argv[1]) if len(sys.argv) > 1 else (
        Path(__file__).parent.parent / "skills"
    )
    loaded = load_skills(target)
    for s in loaded:
        print(f"\n{'─'*50}")
        print(f"Name:        {s.name}")
        print(f"Description: {s.description}")
        print(f"Version:     {s.version}")
        print(f"Tools:       {', '.join(s.tools)}")
        print(f"Body length: {len(s.body)} chars")
