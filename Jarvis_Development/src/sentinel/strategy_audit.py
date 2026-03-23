"""
AWP-087 – Strategy Audit Trail
Checksummen-Prüfung für strategy/*.md Dateien.
Bei unautorisierter Änderung: System-Lockdown.

Workflow:
  1. seal()      → Erstellt/aktualisiert data/strategy_checksums.json
  2. verify()    → Prüft aktuelle Dateien gegen gespeicherte Checksums
  3. lockdown()  → Wird bei Verletzung aufgerufen (setzt Lockdown-Flag)

Python 3.12
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

log = logging.getLogger("jarvis.sentinel.strategy_audit")

PROJECT_ROOT   = Path(__file__).parent.parent.parent
STRATEGY_DIR   = PROJECT_ROOT / "strategy"
CHECKSUMS_PATH = PROJECT_ROOT / "data" / "strategy_checksums.json"
LOCKDOWN_FLAG  = PROJECT_ROOT / "data" / ".strategy_lockdown"


@dataclass
class AuditResult:
    passed: bool
    checked: int
    violations: list[dict] = field(default_factory=list)
    new_files: list[str] = field(default_factory=list)
    missing_files: list[str] = field(default_factory=list)
    checked_at: str = ""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def seal(authorised_by: str = "operator") -> dict[str, Any]:
    """
    Record current checksums of all strategy/*.md files.
    Call this after intentional strategy updates.
    """
    data: dict[str, Any] = {
        "sealed_at": datetime.now(tz=timezone.utc).isoformat(),
        "sealed_by": authorised_by,
        "files": {},
    }
    for md in sorted(STRATEGY_DIR.glob("*.md")):
        data["files"][md.name] = {
            "sha256": _sha256(md),
            "size": md.stat().st_size,
        }

    CHECKSUMS_PATH.parent.mkdir(parents=True, exist_ok=True)
    CHECKSUMS_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    log.info("Strategy seal updated: %d files by %s", len(data["files"]), authorised_by)

    # Clear any existing lockdown
    if LOCKDOWN_FLAG.exists():
        LOCKDOWN_FLAG.unlink()
        log.info("Strategy lockdown cleared by seal()")

    return data


def verify() -> AuditResult:
    """
    Verify current strategy/*.md against stored checksums.
    Returns AuditResult with violations list.
    """
    result = AuditResult(
        passed=True,
        checked=0,
        checked_at=datetime.now(tz=timezone.utc).isoformat(),
    )

    if not CHECKSUMS_PATH.exists():
        log.warning("No strategy checksums found — run seal() first")
        result.passed = False
        result.violations.append({"file": "_meta", "reason": "No seal file found"})
        return result

    stored = json.loads(CHECKSUMS_PATH.read_text(encoding="utf-8"))
    stored_files: dict[str, dict] = stored.get("files", {})
    current_files = {f.name: f for f in STRATEGY_DIR.glob("*.md")}

    # Check all stored files
    for filename, expected in stored_files.items():
        result.checked += 1
        if filename not in current_files:
            result.missing_files.append(filename)
            result.violations.append({
                "file": filename,
                "reason": "File deleted or moved",
                "expected_sha256": expected["sha256"],
            })
            result.passed = False
            continue

        actual_sha = _sha256(current_files[filename])
        if actual_sha != expected["sha256"]:
            result.violations.append({
                "file": filename,
                "reason": "Content modified",
                "expected_sha256": expected["sha256"],
                "actual_sha256":   actual_sha,
            })
            result.passed = False

    # New files not in seal
    for fname in current_files:
        if fname not in stored_files:
            result.new_files.append(fname)

    if not result.passed:
        lockdown(result)

    log.info(
        "Strategy audit: %s (%d checked, %d violations)",
        "PASS" if result.passed else "FAIL",
        result.checked,
        len(result.violations),
    )
    return result


def lockdown(audit: AuditResult) -> None:
    """
    Activate system lockdown due to unauthorized strategy changes.
    Writes lockdown flag file + detailed report.
    """
    ts = datetime.now(tz=timezone.utc).isoformat()
    payload = {
        "lockdown_at": ts,
        "reason": "Unauthorized strategy file modification detected",
        "violations": audit.violations,
        "missing": audit.missing_files,
        "new_files": audit.new_files,
    }

    LOCKDOWN_FLAG.parent.mkdir(parents=True, exist_ok=True)
    LOCKDOWN_FLAG.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    # Write human-readable alert
    alert_path = PROJECT_ROOT / "logs" / "strategy_lockdown_alert.md"
    lines = [
        "# ⛔ STRATEGY LOCKDOWN ACTIVATED",
        f"**Time:** {ts}",
        f"**Reason:** Unauthorized modification of strategy files",
        "",
        "## Violations",
    ]
    for v in audit.violations:
        lines.append(f"- **{v['file']}**: {v['reason']}")
        if "expected_sha256" in v:
            lines.append(f"  - Expected: `{v['expected_sha256'][:16]}…`")
        if "actual_sha256" in v:
            lines.append(f"  - Actual:   `{v['actual_sha256'][:16]}…`")
    lines += [
        "",
        "## Resolution",
        "1. Identify who changed the files and why.",
        "2. If authorized: run `python src/sentinel/strategy_audit.py seal`",
        "3. If unauthorized: investigate security breach, restore from backup.",
        "",
        "_Auto-generated by Jarvis Strategy Audit Trail (AWP-087)_",
    ]
    alert_path.write_text("\n".join(lines), encoding="utf-8")

    log.critical(
        "STRATEGY LOCKDOWN: %d violations detected. Flag: %s",
        len(audit.violations), LOCKDOWN_FLAG,
    )

    # Attempt to notify
    try:
        from notifications import _notify_sync  # type: ignore
        _notify_sync(
            "⛔ JARVIS LOCKDOWN",
            f"{len(audit.violations)} strategy file(s) modified without authorization!",
        )
    except Exception:
        pass


def is_locked() -> bool:
    """Return True if the system is currently in strategy lockdown."""
    return LOCKDOWN_FLAG.exists()


def check_lockdown_gate() -> None:
    """
    Call this at system startup. Raises RuntimeError if lockdown is active.
    Prevents any agent writes until lockdown is cleared.
    """
    if is_locked():
        data = json.loads(LOCKDOWN_FLAG.read_text(encoding="utf-8"))
        raise RuntimeError(
            f"SYSTEM LOCKDOWN ACTIVE since {data.get('lockdown_at', '?')}. "
            f"Violations: {len(data.get('violations', []))}. "
            "Run seal() with operator authorization to clear."
        )


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)

    cmd = sys.argv[1] if len(sys.argv) > 1 else "verify"

    if cmd == "seal":
        by = sys.argv[2] if len(sys.argv) > 2 else "operator"
        result = seal(authorised_by=by)
        print(f"Sealed {len(result['files'])} files by {by}")

    elif cmd == "verify":
        audit = verify()
        if audit.passed:
            print(f"✅ All {audit.checked} strategy files intact.")
        else:
            print(f"❌ VIOLATIONS: {len(audit.violations)}")
            for v in audit.violations:
                print(f"  - {v['file']}: {v['reason']}")
        if audit.new_files:
            print(f"  ℹ New (unsealed) files: {audit.new_files}")

    elif cmd == "status":
        locked = is_locked()
        print(f"Lockdown: {'ACTIVE ⛔' if locked else 'CLEAR ✅'}")
        if locked:
            data = json.loads(LOCKDOWN_FLAG.read_text(encoding="utf-8"))
            print(f"Since: {data.get('lockdown_at')}")

    else:
        print(f"Usage: {sys.argv[0]} [seal|verify|status] [authorised_by]")
