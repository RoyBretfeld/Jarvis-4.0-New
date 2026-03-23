"""
Tests für src/librarian.py
Läuft ohne Docker/RAG-Backend – nur Dateisystem.
pytest 8.x | Python 3.12
"""

import sys
import textwrap
from pathlib import Path

import pytest

# Ensure src/ is on the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from librarian import (
    Skill,
    _parse_yaml_block,
    _clean_escaped_markdown,
    parse_skill_file,
    load_skills,
    get_skill_by_name,
)


# ─────────────────────────────────────────────
# _parse_yaml_block
# ─────────────────────────────────────────────
class TestParseYamlBlock:
    def test_simple_string_values(self):
        block = 'name: "My Skill"\nversion: "1.2.3"'
        result = _parse_yaml_block(block)
        assert result["name"] == "My Skill"
        assert result["version"] == "1.2.3"

    def test_inline_list(self):
        block = 'tools: ["terminal", "docker_api"]'
        result = _parse_yaml_block(block)
        assert result["tools"] == ["terminal", "docker_api"]

    def test_block_list(self):
        block = "tools:\n- terminal\n- rag_access"
        result = _parse_yaml_block(block)
        assert result["tools"] == ["terminal", "rag_access"]

    def test_boolean_true(self):
        block = "enabled: true"
        assert _parse_yaml_block(block)["enabled"] is True

    def test_boolean_false(self):
        block = "enabled: false"
        assert _parse_yaml_block(block)["enabled"] is False

    def test_integer_value(self):
        block = "port: 6333"
        assert _parse_yaml_block(block)["port"] == 6333

    def test_empty_block(self):
        assert _parse_yaml_block("") == {}

    def test_missing_colon_line_ignored(self):
        block = "name: Test\njust a line without colon"
        result = _parse_yaml_block(block)
        assert "name" in result
        assert len(result) == 1


# ─────────────────────────────────────────────
# _clean_escaped_markdown
# ─────────────────────────────────────────────
class TestCleanEscapedMarkdown:
    def test_removes_hash_escape(self):
        assert _clean_escaped_markdown(r"\# Title") == "# Title"

    def test_removes_asterisk_escape(self):
        assert _clean_escaped_markdown(r"\*bold\*") == "*bold*"

    def test_leaves_normal_text_unchanged(self):
        text = "Hello world\nNo escapes here."
        assert _clean_escaped_markdown(text) == text


# ─────────────────────────────────────────────
# parse_skill_file (uses tmp_path fixture)
# ─────────────────────────────────────────────
class TestParseSkillFile:
    def _write_skill(self, tmp_path: Path, content: str) -> Path:
        p = tmp_path / "test_skill.md"
        p.write_text(content, encoding="utf-8")
        return p

    def test_valid_skill_parsed(self, tmp_path):
        content = textwrap.dedent("""\
            ---
            name: "Test Skill"
            description: "A test"
            version: "1.0.0"
            tools: ["terminal"]
            ---

            # Body
            This is the skill body.
        """)
        skill = parse_skill_file(self._write_skill(tmp_path, content))
        assert isinstance(skill, Skill)
        assert skill.name == "Test Skill"
        assert skill.version == "1.0.0"
        assert skill.tools == ["terminal"]
        assert "Body" in skill.body

    def test_no_frontmatter_returns_none(self, tmp_path):
        p = tmp_path / "no_meta.md"
        p.write_text("# Just a heading\nNo frontmatter.", encoding="utf-8")
        assert parse_skill_file(p) is None

    def test_missing_file_returns_none(self, tmp_path):
        assert parse_skill_file(tmp_path / "nonexistent.md") is None

    def test_escaped_markdown_cleaned(self, tmp_path):
        content = textwrap.dedent("""\
            ---
            name: "Escape Test"
            description: "desc"
            version: "1.0.0"
            tools: []
            ---

            \\# Escaped heading
        """)
        skill = parse_skill_file(self._write_skill(tmp_path, content))
        assert skill is not None
        assert "# Escaped heading" in skill.body


# ─────────────────────────────────────────────
# load_skills
# ─────────────────────────────────────────────
class TestLoadSkills:
    def _make_skill_file(self, directory: Path, name: str) -> Path:
        content = textwrap.dedent(f"""\
            ---
            name: "{name}"
            description: "Auto-generated test skill"
            version: "0.1.0"
            tools: ["test_tool"]
            ---

            Skill body for {name}.
        """)
        p = directory / f"{name.lower().replace(' ', '_')}.md"
        p.write_text(content, encoding="utf-8")
        return p

    def test_loads_multiple_skills(self, tmp_path):
        for i in range(3):
            self._make_skill_file(tmp_path, f"Skill {i}")
        skills = load_skills(tmp_path)
        assert len(skills) == 3

    def test_nonexistent_dir_returns_empty(self, tmp_path):
        skills = load_skills(tmp_path / "ghost")
        assert skills == []

    def test_skips_files_without_frontmatter(self, tmp_path):
        self._make_skill_file(tmp_path, "Valid Skill")
        (tmp_path / "invalid.md").write_text("no frontmatter", encoding="utf-8")
        skills = load_skills(tmp_path)
        assert len(skills) == 1


# ─────────────────────────────────────────────
# get_skill_by_name
# ─────────────────────────────────────────────
class TestGetSkillByName:
    def _make_skill(self, name: str) -> Skill:
        return Skill(name=name, description="", version="1.0",
                     tools=[], body="", source_path=Path("/dev/null"))

    def test_finds_existing(self):
        skills = [self._make_skill("Docker Orchestration"),
                  self._make_skill("OWASP Scanner")]
        result = get_skill_by_name(skills, "Docker Orchestration")
        assert result is not None
        assert result.name == "Docker Orchestration"

    def test_case_insensitive(self):
        skills = [self._make_skill("Docker Orchestration")]
        assert get_skill_by_name(skills, "docker orchestration") is not None

    def test_returns_none_for_missing(self):
        skills = [self._make_skill("Existing")]
        assert get_skill_by_name(skills, "Missing") is None

    def test_empty_list(self):
        assert get_skill_by_name([], "anything") is None
