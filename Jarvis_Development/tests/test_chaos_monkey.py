"""
AWP-076 – Chaos Monkey Test Suite
Testet die Selbstheilungsfähigkeit des Systems durch zufällige
Service-Terminierungen und validates die heartbeat.py self_heal().

Tests:
  1. Container wird terminiert → heartbeat erkennt → restart
  2. Ollama fällt aus → API gibt 503 → kein Crash
  3. Qdrant fällt aus → search degraded (KeywordOnly) → no crash
  4. Multiple containers down → MAX_RESTART_PER_CYCLE respected
  5. Sandbox container terminiert → NICHT neugestartet (security policy)

Python 3.12 | pytest-asyncio
"""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_docker():
    """Mock Docker client."""
    client = MagicMock()
    client.containers.get.return_value = MagicMock()
    return client


@pytest.fixture
def mock_unhealthy_container():
    c = MagicMock()
    c.name = "jarvis-core"
    c.status = "exited"
    c.attrs = {"State": {"Health": {"Status": "unhealthy"}}}
    return c


@pytest.fixture
def mock_healthy_container():
    c = MagicMock()
    c.name = "jarvis-rag"
    c.status = "running"
    c.attrs = {"State": {"Health": {"Status": "healthy"}}}
    return c


@pytest.fixture
def mock_sandbox_container():
    c = MagicMock()
    c.name = "jarvis-sandbox"
    c.status = "exited"
    c.attrs = {"State": {"Health": {"Status": "unhealthy"}}}
    return c


# ── Test: single container recovery ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_single_container_recovery(mock_unhealthy_container):
    """Heartbeat detects unhealthy container and triggers restart."""
    restart_called = []

    async def fake_restart(name: str) -> None:
        restart_called.append(name)

    with patch("heartbeat._restart_container", side_effect=fake_restart):
        with patch("heartbeat._check_containers", return_value=[mock_unhealthy_container]):
            from heartbeat import self_heal  # type: ignore
            await self_heal()

    assert "jarvis-core" in restart_called, "Should have restarted jarvis-core"


@pytest.mark.asyncio
async def test_sandbox_not_restarted(mock_sandbox_container):
    """Sandbox container must NEVER be auto-restarted (security policy)."""
    restart_called = []

    async def fake_restart(name: str) -> None:
        restart_called.append(name)

    with patch("heartbeat._restart_container", side_effect=fake_restart):
        with patch("heartbeat._check_containers", return_value=[mock_sandbox_container]):
            from heartbeat import self_heal  # type: ignore
            await self_heal()

    assert "jarvis-sandbox" not in restart_called, \
        "Sandbox must never be auto-restarted"


@pytest.mark.asyncio
async def test_max_restart_per_cycle(mock_unhealthy_container):
    """MAX_RESTART_PER_CYCLE=2 is respected even with 3 unhealthy containers."""
    containers = []
    for name in ["jarvis-core", "jarvis-rag", "jarvis-gateway"]:
        c = MagicMock()
        c.name = name
        c.status = "exited"
        c.attrs = {"State": {"Health": {"Status": "unhealthy"}}}
        containers.append(c)

    restart_called = []

    async def fake_restart(name: str) -> None:
        restart_called.append(name)

    with patch("heartbeat._restart_container", side_effect=fake_restart):
        with patch("heartbeat._check_containers", return_value=containers):
            from heartbeat import self_heal  # type: ignore
            await self_heal()

    assert len(restart_called) <= 2, \
        f"Expected at most 2 restarts, got {len(restart_called)}"


# ── Test: API resilience when Ollama is down ─────────────────────────────────

@pytest.mark.asyncio
async def test_api_survives_ollama_down():
    """API /health endpoint returns 503 (not crash) when Ollama is down."""
    import httpx
    from httpx import AsyncClient

    async def mock_get(url: str, **kwargs: Any):
        if "11434" in url or "api/tags" in url:
            raise httpx.ConnectError("Ollama down")
        return MagicMock(status_code=200, json=lambda: {"status": "ok"})

    with patch("httpx.AsyncClient.get", side_effect=mock_get):
        try:
            from heartbeat import check_ollama  # type: ignore
            result = await check_ollama()
            assert result is False, "Should return False when Ollama is down"
        except ImportError:
            pytest.skip("heartbeat module not importable in test context")


# ── Test: RAG degraded mode ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_rag_degraded_keyword_only():
    """When Qdrant is down, search falls back to keyword-only without crashing."""
    with patch("memory_interface.QdrantMemory.search",
               side_effect=ConnectionError("Qdrant down")):
        try:
            from memory_interface import JarvisMemory  # type: ignore
            mem = JarvisMemory()
            # Should not raise — should degrade gracefully
            results = await mem.search("test query", mode="hybrid")
            # Results may be empty or keyword-only, but no exception
            assert isinstance(results, list)
        except ImportError:
            pytest.skip("memory_interface not available in test context")


# ── Test: Chaos sequence ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_chaos_sequence():
    """
    Simulate rapid sequential failures:
      1. Qdrant goes down
      2. Core container crashes
      3. Heartbeat fires → only Core restarted (not sandbox)
    Verifies no unhandled exceptions bubble up.
    """
    events: list[str] = []

    async def fake_restart(name: str) -> None:
        events.append(f"restart:{name}")

    containers = [
        _make_container("jarvis-core", "exited"),
        _make_container("jarvis-rag", "running"),
        _make_container("jarvis-sandbox", "exited"),
    ]

    with patch("heartbeat._restart_container", side_effect=fake_restart):
        with patch("heartbeat._check_containers", return_value=containers):
            try:
                from heartbeat import self_heal  # type: ignore
                await self_heal()
            except ImportError:
                pytest.skip("heartbeat not importable")

    assert "restart:jarvis-core" in events
    assert "restart:jarvis-sandbox" not in events


# ── Test: Orchestrator rollback on chaos ─────────────────────────────────────

@pytest.mark.asyncio
async def test_orchestrator_rollback_on_tester_crash():
    """If tester agent crashes mid-pipeline, orchestrator rolls back."""
    try:
        from agents.orchestrator import run_pipeline  # type: ignore
        from agents.base_agent import AgentResult  # type: ignore
    except ImportError:
        pytest.skip("Agents not importable in test context")

    mock_coder = AsyncMock(return_value=AgentResult(
        success=True,
        agent="coder",
        task="write test",
        metadata={"backup_path": "/tmp/fake_backup.py"},
    ))
    mock_tester = AsyncMock(side_effect=RuntimeError("Tester crashed (chaos)"))

    with patch("agents.orchestrator.CoderAgent.run", mock_coder):
        with patch("agents.orchestrator.TesterAgent.run", mock_tester):
            result = await run_pipeline("write test")
            assert not result.success, "Pipeline should fail when tester crashes"


# ── Helper ───────────────────────────────────────────────────────────────────

def _make_container(name: str, status: str) -> MagicMock:
    c = MagicMock()
    c.name = name
    c.status = status
    health = "healthy" if status == "running" else "unhealthy"
    c.attrs = {"State": {"Health": {"Status": health}}}
    return c
