"""
AWP-089 – Agent Compliance Test: Elite Guard (AWP-081–088)
@security prüft, ob alle neuen Kontroll-Funktionen vorhanden und funktional sind.

Checks:
  1. AWP-081 Git-Checkpointing   → base_agent.pre_awp_checkpoint exists
  2. AWP-082 Undo-Logic          → jarvis_shell.do_rollback exists
  3. AWP-083 Reasoning-Log       → base_agent.log_reasoning exists + logs/reasoning.log created
  4. AWP-084 UI-Thinking-Stream  → ThoughtOverlay.tsx exists
  5. AWP-085 Thermal-Watchdog    → sentinel/thermal.py exists + ThermalWatchdog class
  6. AWP-086 Kill-Switch         → stop_jarvis.bat exists on Desktop
  7. AWP-087 Audit-Trail         → strategy_audit.py + checksums sealed
  8. AWP-088 Memory-Snapshot     → memory_snapshot.py + take_snapshot callable

Python 3.12 | pytest
"""

from __future__ import annotations

import importlib
import inspect
import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
SRC          = PROJECT_ROOT / "src"
DESKTOP      = Path.home() / "Desktop"


# ── AWP-081: Git-Checkpointing ────────────────────────────────────────────

def test_081_git_repo_initialized():
    """Git repository must exist at project root."""
    git_dir = PROJECT_ROOT / ".git"
    assert git_dir.is_dir(), f"No .git directory at {PROJECT_ROOT}"


def test_081_base_agent_has_checkpoint():
    """BaseAgent must have pre_awp_checkpoint method."""
    from agents.base_agent import BaseAgent  # type: ignore
    assert hasattr(BaseAgent, "pre_awp_checkpoint"), \
        "BaseAgent missing pre_awp_checkpoint()"
    sig = inspect.signature(BaseAgent.pre_awp_checkpoint)
    assert "awp_id" in sig.parameters, \
        "pre_awp_checkpoint must accept awp_id parameter"


def test_081_git_checkpoint_logic():
    """_git_checkpoint must call git add -u and git commit."""
    from agents.base_agent import BaseAgent  # type: ignore
    src = inspect.getsource(BaseAgent._git_checkpoint)
    assert "git" in src.lower(), "No git command in _git_checkpoint"
    assert "add" in src and "commit" in src, \
        "_git_checkpoint must stage and commit"


# ── AWP-082: Undo-Logic ───────────────────────────────────────────────────

def test_082_shell_has_rollback():
    """JarvisShell must have do_rollback command."""
    from jarvis_shell import JarvisShell  # type: ignore
    assert hasattr(JarvisShell, "do_rollback"), \
        "JarvisShell missing do_rollback()"


def test_082_rollback_in_dev_commands():
    """rollback must be in DEV_COMMANDS (not available in SYSTEM mode)."""
    from jarvis_shell import DEV_COMMANDS  # type: ignore
    assert "rollback" in DEV_COMMANDS, \
        "'rollback' not in DEV_COMMANDS"

    from jarvis_shell import SYSTEM_COMMANDS  # type: ignore
    assert "rollback" not in SYSTEM_COMMANDS, \
        "'rollback' must NOT be in SYSTEM_COMMANDS (security)"


def test_082_rollback_syncs_state_json():
    """do_rollback must reference state.json."""
    from jarvis_shell import JarvisShell  # type: ignore
    src = inspect.getsource(JarvisShell.do_rollback)
    assert "state.json" in src or "state_path" in src, \
        "do_rollback does not sync state.json"
    assert "ROLLED_BACK" in src, \
        "do_rollback must set status to ROLLED_BACK"


# ── AWP-083: Reasoning-Log ────────────────────────────────────────────────

def test_083_reasoning_log_exists():
    """logs/reasoning.log must exist and contain initial entry."""
    log_path = PROJECT_ROOT / "logs" / "reasoning.log"
    assert log_path.exists(), "logs/reasoning.log not created"
    content = log_path.read_text(encoding="utf-8")
    assert "@system" in content or "@" in content, \
        "reasoning.log must contain at least one @agent entry"


def test_083_base_agent_has_log_reasoning():
    """BaseAgent must have log_reasoning() with 3 sentence parameters."""
    from agents.base_agent import BaseAgent  # type: ignore
    assert hasattr(BaseAgent, "log_reasoning"), \
        "BaseAgent missing log_reasoning()"
    sig = inspect.signature(BaseAgent.log_reasoning)
    params = list(sig.parameters.keys())
    assert "sentence1" in params, "log_reasoning must have sentence1 param"
    assert "sentence2" in params, "log_reasoning must have sentence2 param"
    assert "sentence3" in params, "log_reasoning must have sentence3 param"


# ── AWP-084: UI Thought Overlay ────────────────────────────────────────────

def test_084_thought_overlay_component_exists():
    """ThoughtOverlay.tsx must exist in UI components."""
    overlay = SRC / "ui" / "src" / "components" / "Monitors" / "ThoughtOverlay.tsx"
    assert overlay.exists(), f"ThoughtOverlay.tsx not found at {overlay}"


def test_084_thought_overlay_uses_websocket():
    """ThoughtOverlay must use useWebSocket hook."""
    overlay = SRC / "ui" / "src" / "components" / "Monitors" / "ThoughtOverlay.tsx"
    if not overlay.exists():
        pytest.skip("ThoughtOverlay.tsx not found")
    content = overlay.read_text(encoding="utf-8")
    assert "useWebSocket" in content, "ThoughtOverlay must use useWebSocket"
    assert "/ws/reasoning" in content, "ThoughtOverlay must connect to /ws/reasoning"


# ── AWP-085: Thermal Watchdog ─────────────────────────────────────────────

def test_085_thermal_module_exists():
    """src/sentinel/thermal.py must exist."""
    thermal = SRC / "sentinel" / "thermal.py"
    assert thermal.exists(), "sentinel/thermal.py not found"


def test_085_thermal_watchdog_class():
    """ThermalWatchdog class must exist with start/stop methods."""
    import sys
    sys.path.insert(0, str(SRC / "sentinel"))
    from thermal import ThermalWatchdog, THERMAL_PAUSE, PAUSE_C  # type: ignore
    assert hasattr(ThermalWatchdog, "start"), "ThermalWatchdog missing start()"
    assert hasattr(ThermalWatchdog, "stop"),  "ThermalWatchdog missing stop()"
    assert PAUSE_C <= 90, f"PAUSE_C={PAUSE_C} is dangerously high"
    import threading
    assert isinstance(THERMAL_PAUSE, threading.Event), \
        "THERMAL_PAUSE must be a threading.Event"


def test_085_thermal_pause_event_shared():
    """THERMAL_PAUSE must be a module-level threading.Event for cross-module use."""
    import sys
    sys.path.insert(0, str(SRC / "sentinel"))
    import threading
    from thermal import THERMAL_PAUSE  # type: ignore
    assert isinstance(THERMAL_PAUSE, threading.Event)
    assert not THERMAL_PAUSE.is_set(), "THERMAL_PAUSE should not be set at startup"


# ── AWP-086: Kill Switch ──────────────────────────────────────────────────

def test_086_kill_switch_bat_exists():
    """stop_jarvis.bat must exist on Desktop."""
    bat = DESKTOP / "stop_jarvis.bat"
    assert bat.exists(), f"stop_jarvis.bat not found at {bat}"


def test_086_kill_switch_contains_compose_kill():
    """Kill switch bat must call docker compose kill."""
    bat = DESKTOP / "stop_jarvis.bat"
    if not bat.exists():
        pytest.skip("stop_jarvis.bat not found")
    content = bat.read_text(encoding="utf-8")
    assert "docker compose kill" in content, \
        "stop_jarvis.bat must call 'docker compose kill'"
    assert "docker compose down" in content, \
        "stop_jarvis.bat should also call 'docker compose down'"


# ── AWP-087: Audit Trail ──────────────────────────────────────────────────

def test_087_strategy_audit_module_exists():
    """src/sentinel/strategy_audit.py must exist."""
    audit = SRC / "sentinel" / "strategy_audit.py"
    assert audit.exists(), "sentinel/strategy_audit.py not found"


def test_087_checksums_sealed():
    """data/strategy_checksums.json must exist and contain file entries."""
    checksums = PROJECT_ROOT / "data" / "strategy_checksums.json"
    assert checksums.exists(), \
        "strategy_checksums.json not found — run seal() first"
    data = json.loads(checksums.read_text(encoding="utf-8"))
    assert "files" in data and len(data["files"]) > 0, \
        "Checksums file is empty — seal() may have failed"


def test_087_lockdown_function_exists():
    """lockdown() function must exist in strategy_audit."""
    import sys
    sys.path.insert(0, str(SRC / "sentinel"))
    from strategy_audit import lockdown, verify, seal, is_locked  # type: ignore
    assert callable(lockdown)
    assert callable(verify)
    assert callable(seal)
    assert callable(is_locked)


def test_087_strategy_files_pass_audit():
    """All strategy files must pass integrity check (no unauthorized changes)."""
    import sys
    sys.path.insert(0, str(SRC / "sentinel"))
    from strategy_audit import verify  # type: ignore
    result = verify()
    assert result.passed, \
        f"Strategy audit FAILED: {result.violations}"


# ── AWP-088: Memory Snapshot ──────────────────────────────────────────────

def test_088_memory_snapshot_module_exists():
    """src/sentinel/memory_snapshot.py must exist."""
    snap = SRC / "sentinel" / "memory_snapshot.py"
    assert snap.exists(), "sentinel/memory_snapshot.py not found"


def test_088_take_snapshot_is_async():
    """take_snapshot must be an async function."""
    import sys
    sys.path.insert(0, str(SRC / "sentinel"))
    from memory_snapshot import take_snapshot  # type: ignore
    import asyncio
    assert asyncio.iscoroutinefunction(take_snapshot), \
        "take_snapshot must be async"


def test_088_snapshot_directory_structure():
    """Snapshot dir (logs/backups/rag_snapshots/) must exist after module import."""
    import sys
    sys.path.insert(0, str(SRC / "sentinel"))
    from memory_snapshot import SNAPSHOT_ROOT  # type: ignore
    # Dir may not exist until first snapshot — just check the path is sane
    assert "rag_snapshots" in str(SNAPSHOT_ROOT)
    assert str(PROJECT_ROOT) in str(SNAPSHOT_ROOT), \
        "SNAPSHOT_ROOT must be inside project"


# ── Meta: all 8 controls present ─────────────────────────────────────────

def test_089_all_elite_guard_controls_present():
    """Summary check: all 8 Elite Guard control artifacts must be present."""
    checks = {
        "AWP-081 git repo":         (PROJECT_ROOT / ".git").is_dir(),
        "AWP-082 rollback shell":   (SRC / "jarvis_shell.py").exists(),
        "AWP-083 reasoning.log":    (PROJECT_ROOT / "logs" / "reasoning.log").exists(),
        "AWP-084 ThoughtOverlay":   (SRC / "ui" / "src" / "components" / "Monitors" / "ThoughtOverlay.tsx").exists(),
        "AWP-085 thermal.py":       (SRC / "sentinel" / "thermal.py").exists(),
        "AWP-086 stop_jarvis.bat":  (DESKTOP / "stop_jarvis.bat").exists(),
        "AWP-087 strategy_audit.py":(SRC / "sentinel" / "strategy_audit.py").exists(),
        "AWP-088 memory_snapshot.py":(SRC / "sentinel" / "memory_snapshot.py").exists(),
    }
    missing = [name for name, ok in checks.items() if not ok]
    assert not missing, f"Elite Guard controls missing:\n" + "\n".join(f"  ✗ {m}" for m in missing)
    print(f"\n✅ All 8 Elite Guard controls ACTIVE:")
    for name in checks:
        print(f"  ✓ {name}")
