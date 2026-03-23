"""
AWP-038 – Agent Unit Tests
Tests für BaseAgent, CoderAgent, TesterAgent, SecurityAgent, Orchestrator.
Keine echten Dateisystem- oder Subprocess-Operationen – vollständig gemockt.
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from agents.base_agent import AgentResult, AgentRole
from agents.coder_agent import CoderAgent
from agents.security_agent import SecurityAgent, Finding
from agents.orchestrator import Orchestrator


# ─────────────────────────────────────────────
# AgentResult
# ─────────────────────────────────────────────
class TestAgentResult:
    def test_truthy_on_success(self):
        r = AgentResult(success=True, role=AgentRole.CODER, output="ok")
        assert bool(r) is True

    def test_falsy_on_failure(self):
        r = AgentResult(success=False, role=AgentRole.CODER, output="")
        assert bool(r) is False


# ─────────────────────────────────────────────
# CoderAgent
# ─────────────────────────────────────────────
class TestCoderAgent:
    @pytest.mark.asyncio
    async def test_write_creates_file(self, tmp_path):
        agent = CoderAgent()
        agent._project_root = tmp_path
        result = await agent.run(file="src/foo.py", content="x = 1", operation="write")
        assert result.success
        assert (tmp_path / "src" / "foo.py").read_text() == "x = 1"

    @pytest.mark.asyncio
    async def test_write_creates_backup_if_exists(self, tmp_path):
        agent = CoderAgent()
        agent._project_root = tmp_path
        # Create existing file
        src = tmp_path / "src"
        src.mkdir()
        (tmp_path / "logs" / "backups").mkdir(parents=True)
        (src / "foo.py").write_text("old content")
        result = await agent.run(file="src/foo.py", content="new content", operation="write")
        assert result.success
        assert result.metadata.get("backup") is not None

    @pytest.mark.asyncio
    async def test_create_refuses_overwrite(self, tmp_path):
        agent = CoderAgent()
        agent._project_root = tmp_path
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "existing.py").write_text("exists")
        result = await agent.run(file="src/existing.py", content="x", operation="create")
        assert not result.success
        assert "already exists" in result.errors[0]

    @pytest.mark.asyncio
    async def test_path_traversal_blocked(self, tmp_path):
        agent = CoderAgent()
        agent._project_root = tmp_path
        with pytest.raises(ValueError, match="traversal"):
            agent._safe_path("../../etc/passwd")

    @pytest.mark.asyncio
    async def test_no_file_returns_failure(self):
        agent = CoderAgent()
        result = await agent.run(file=None, content="x", operation="write")
        assert not result.success


# ─────────────────────────────────────────────
# SecurityAgent
# ─────────────────────────────────────────────
class TestSecurityAgent:
    @pytest.mark.asyncio
    async def test_clean_code_passes(self):
        agent = SecurityAgent()
        code = "def add(a, b):\n    return a + b\n"
        result = await agent.run(content=code)
        assert result.success
        assert result.metadata["critical"] == 0

    @pytest.mark.asyncio
    async def test_hardcoded_password_is_critical(self):
        agent = SecurityAgent()
        code = 'password = "super_secret_123"\n'
        result = await agent.run(content=code)
        assert not result.success
        assert result.metadata["critical"] >= 1

    @pytest.mark.asyncio
    async def test_shell_true_is_critical(self):
        agent = SecurityAgent()
        code = "import subprocess\nsubprocess.run(cmd, shell=True)\n"
        result = await agent.run(content=code)
        assert not result.success

    @pytest.mark.asyncio
    async def test_eval_is_critical(self):
        agent = SecurityAgent()
        result = await agent.run(content="result = eval(user_input)\n")
        assert not result.success

    @pytest.mark.asyncio
    async def test_md5_is_warning_not_critical(self):
        agent = SecurityAgent()
        code = "import hashlib\nhashlib.md5(data)\n"
        result = await agent.run(content=code)
        # MD5 is WARNING level → success=True (no critical), but warning exists
        assert result.success
        assert result.metadata["warnings"] >= 1

    @pytest.mark.asyncio
    async def test_no_content_returns_failure(self):
        agent = SecurityAgent()
        result = await agent.run(content=None, file=None)
        assert not result.success

    @pytest.mark.asyncio
    async def test_private_key_is_critical(self):
        agent = SecurityAgent()
        code = "-----BEGIN RSA PRIVATE KEY-----\nMIIE...\n"
        result = await agent.run(content=code)
        assert not result.success


# ─────────────────────────────────────────────
# Orchestrator – Handover Pipeline
# ─────────────────────────────────────────────
class TestOrchestrator:
    def _make_result(self, role, success, output="ok", backup=None):
        from agents.base_agent import AgentResult, AgentRole
        return AgentResult(
            success=success,
            role=role,
            output=output,
            metadata={"backup": backup},
        )

    @pytest.mark.asyncio
    async def test_full_pipeline_success(self):
        orch = Orchestrator()
        orch.coder.run    = AsyncMock(return_value=self._make_result(AgentRole.CODER, True, backup="/tmp/x.py"))
        orch.tester.run   = AsyncMock(return_value=self._make_result(AgentRole.TESTER, True))
        orch.security.run = AsyncMock(return_value=self._make_result(AgentRole.SECURITY, True))

        result = await orch.run_pipeline(file="src/foo.py", new_content="x=1")
        assert result.success
        assert result.stopped_at is None
        assert len(result.steps) == 3

    @pytest.mark.asyncio
    async def test_pipeline_stops_at_coder_failure(self):
        orch = Orchestrator()
        orch.coder.run  = AsyncMock(return_value=self._make_result(AgentRole.CODER, False))
        orch.tester.run = AsyncMock()

        result = await orch.run_pipeline(file="src/foo.py", new_content="x=1")
        assert not result.success
        assert result.stopped_at == "coder"
        orch.tester.run.assert_not_called()

    @pytest.mark.asyncio
    async def test_pipeline_rolls_back_on_test_failure(self, tmp_path):
        orch = Orchestrator()
        orch.coder.run    = AsyncMock(return_value=self._make_result(
            AgentRole.CODER, True, backup=str(tmp_path / "backup.py")))
        orch.tester.run   = AsyncMock(return_value=self._make_result(AgentRole.TESTER, False))
        orch.security.run = AsyncMock()

        result = await orch.run_pipeline(file="src/foo.py", new_content="x=1")
        assert not result.success
        assert result.stopped_at == "tester"
        orch.security.run.assert_not_called()

    @pytest.mark.asyncio
    async def test_pipeline_stops_at_security_veto(self, tmp_path):
        orch = Orchestrator()
        orch.coder.run    = AsyncMock(return_value=self._make_result(
            AgentRole.CODER, True, backup=str(tmp_path / "backup.py")))
        orch.tester.run   = AsyncMock(return_value=self._make_result(AgentRole.TESTER, True))
        orch.security.run = AsyncMock(return_value=self._make_result(
            AgentRole.SECURITY, False, output="VETO"))

        result = await orch.run_pipeline(file="src/foo.py", new_content="x=1")
        assert not result.success
        assert result.stopped_at == "security"
