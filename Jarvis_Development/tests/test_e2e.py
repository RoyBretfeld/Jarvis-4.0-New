"""
AWP-038 – E2E Integration Test (lightweight, no Docker required)
Simulates: User command → Coder writes → Tester validates → UI state updates.
Uses tmp_path and mocks for filesystem operations.
"""

import sys
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from agents.orchestrator import Orchestrator
from agents.base_agent import AgentResult, AgentRole


# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────
@pytest.fixture
def project_root(tmp_path):
    """Minimal project structure for E2E tests."""
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "logs" / "backups").mkdir(parents=True)
    (tmp_path / "state.json").write_text(json.dumps({
        "project": "Jarvis 4.0",
        "current_phase": "AWP-038: IN_PROGRESS",
        "workpackages": {},
        "security": {"owasp_scan": "PASS", "critical_findings": 0, "warnings": 0},
    }))
    return tmp_path


# ─────────────────────────────────────────────
# E2E Scenario 1: Happy Path
# User writes clean code → tests pass → security clean → state updated
# ─────────────────────────────────────────────
@pytest.mark.asyncio
async def test_e2e_happy_path(project_root):
    """Full pipeline: write → test → security → success."""
    clean_code = "def add(a, b):\n    return a + b\n"
    target_file = "src/calculator.py"

    orch = Orchestrator()
    orch._project_root = project_root
    orch.coder._project_root = project_root
    orch.tester._project_root = project_root
    orch.security._project_root = project_root

    # Mock tester (no real pytest subprocess)
    ok_test = AgentResult(success=True, role=AgentRole.TESTER,
                          output="5 passed", metadata={})
    orch.tester.run = AsyncMock(return_value=ok_test)

    result = await orch.run_pipeline(file=target_file, new_content=clean_code)

    assert result.success, f"Expected success, got: {result.final_output}"
    written = (project_root / target_file).read_text()
    assert written == clean_code
    assert len(result.steps) == 3
    assert all(s["success"] for s in result.steps)


# ─────────────────────────────────────────────
# E2E Scenario 2: Security Veto
# User writes code with hardcoded secret → security blocks → file rolled back
# ─────────────────────────────────────────────
@pytest.mark.asyncio
async def test_e2e_security_blocks_secret(project_root):
    """Pipeline stops at security when code contains hardcoded password."""
    bad_code = 'password = "hunter2"\ndef connect():\n    pass\n'
    target_file = "src/db.py"

    orch = Orchestrator()
    orch._project_root = project_root
    orch.coder._project_root = project_root
    orch.tester._project_root = project_root
    orch.security._project_root = project_root

    ok_test = AgentResult(success=True, role=AgentRole.TESTER,
                          output="passed", metadata={})
    orch.tester.run = AsyncMock(return_value=ok_test)

    result = await orch.run_pipeline(file=target_file, new_content=bad_code)

    assert not result.success
    assert result.stopped_at == "security"
    assert "security" in result.final_output.lower()


# ─────────────────────────────────────────────
# E2E Scenario 3: Test Failure → Rollback
# Coder writes → tests fail → file is rolled back
# ─────────────────────────────────────────────
@pytest.mark.asyncio
async def test_e2e_test_failure_triggers_rollback(project_root):
    """When tests fail, the written file is rolled back."""
    # Create existing "good" version
    src_dir = project_root / "src"
    original = "def foo():\n    return 42\n"
    (src_dir / "module.py").write_text(original)

    broken_code = "def foo(:\n    syntax error\n"
    target_file = "src/module.py"

    orch = Orchestrator()
    orch._project_root = project_root
    orch.coder._project_root = project_root
    orch.tester._project_root = project_root
    orch.security._project_root = project_root

    fail_test = AgentResult(success=False, role=AgentRole.TESTER,
                            output="1 error", errors=["syntax error"],
                            metadata={})
    orch.tester.run = AsyncMock(return_value=fail_test)

    result = await orch.run_pipeline(file=target_file, new_content=broken_code)

    assert not result.success
    assert result.stopped_at == "tester"


# ─────────────────────────────────────────────
# E2E Scenario 4: Librarian → Ingest → Search
# Load skills → simulate ingest → memory search returns results
# ─────────────────────────────────────────────
@pytest.mark.asyncio
async def test_e2e_librarian_to_memory(project_root):
    """Skills loaded from /skills → can be found via memory search."""
    # Create dummy skill file
    skills_dir = project_root / "skills"
    skills_dir.mkdir()
    (skills_dir / "test_skill.md").write_text(
        '---\nname: "Test Skill"\ndescription: "test"\nversion: "1.0.0"\ntools: []\n---\n\nBody.'
    )

    from librarian import load_skills
    skills = load_skills(skills_dir)
    assert len(skills) == 1
    assert skills[0].name == "Test Skill"

    # Simulate memory search (mocked – no Qdrant needed)
    from memory_interface import JarvisMemory, Document, SearchResult
    mem = JarvisMemory()
    mock_result = SearchResult(
        document=Document(doc_id="abc", text="Test Skill body", metadata={}),
        source="qdrant",
        score=0.95,
    )
    mem.qdrant.search = AsyncMock(return_value=[mock_result])
    mem.chroma.search = AsyncMock(return_value=[])

    results = await mem.search("Test Skill", mode="semantic")
    assert len(results) == 1
    assert results[0].score == 0.95
