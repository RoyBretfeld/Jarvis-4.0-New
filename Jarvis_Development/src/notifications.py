"""
AWP-055 – Desktop Notification System (Windows)
Sendet Windows-Toast-Benachrichtigungen wenn ein Overdrive-Batch abgeschlossen ist.

Backends:
  1. win10toast    (Windows, leichtgewichtig)
  2. plyer         (Cross-platform: Windows/macOS/Linux)
  3. PowerShell    (Fallback: native Windows-BurntToast oder Toast-API)
  4. Logging only  (wenn keine Notification-Library verfügbar)

Python 3.12 | AsyncIO
"""

from __future__ import annotations

import asyncio
import logging
import os
import platform
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

log = logging.getLogger("jarvis.notifications")

IS_WINDOWS = platform.system() == "Windows"
NOTIFY_ENABLED = os.environ.get("NOTIFY_ENABLED", "true").lower() == "true"
APP_NAME = "Jarvis 4.0"
ICON_PATH = str(Path(__file__).parent.parent / "config" / "jarvis_icon.ico")


# ─────────────────────────────────────────────
# Data model
# ─────────────────────────────────────────────

@dataclass
class Notification:
    title: str
    message: str
    urgency: Literal["info", "warning", "error"] = "info"
    duration: int = 8           # seconds (win10toast)
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(tz=timezone.utc).isoformat()


# ─────────────────────────────────────────────
# Backends
# ─────────────────────────────────────────────

def _notify_win10toast(n: Notification) -> bool:
    try:
        from win10toast import ToastNotifier  # type: ignore
        toaster = ToastNotifier()
        icon = ICON_PATH if Path(ICON_PATH).exists() else None
        toaster.show_toast(
            title=n.title,
            msg=n.message,
            icon_path=icon,
            duration=n.duration,
            threaded=True,
        )
        return True
    except Exception as exc:
        log.debug("win10toast failed: %s", exc)
        return False


def _notify_plyer(n: Notification) -> bool:
    try:
        from plyer import notification  # type: ignore
        notification.notify(
            title=n.title,
            message=n.message,
            app_name=APP_NAME,
            timeout=n.duration,
        )
        return True
    except Exception as exc:
        log.debug("plyer failed: %s", exc)
        return False


def _notify_powershell(n: Notification) -> bool:
    """Fallback: PowerShell BurntToast / Windows.UI.Notifications."""
    if not IS_WINDOWS:
        return False
    ps_script = f"""
Add-Type -AssemblyName System.Windows.Forms
$notify = New-Object System.Windows.Forms.NotifyIcon
$notify.Icon = [System.Drawing.SystemIcons]::Information
$notify.BalloonTipTitle = "{n.title.replace('"', "'")}"
$notify.BalloonTipText = "{n.message.replace('"', "'")}"
$notify.BalloonTipIcon = "Info"
$notify.Visible = $true
$notify.ShowBalloonTip({n.duration * 1000})
Start-Sleep -Milliseconds {n.duration * 1000 + 500}
$notify.Dispose()
""".strip()
    try:
        result = subprocess.run(
            ["powershell", "-NonInteractive", "-NoProfile",
             "-WindowStyle", "Hidden", "-Command", ps_script],
            timeout=n.duration + 5,
            capture_output=True,
        )
        return result.returncode == 0
    except Exception as exc:
        log.debug("PowerShell notify failed: %s", exc)
        return False


def _notify_sync(n: Notification) -> None:
    """Try each backend in priority order."""
    backends = [_notify_win10toast, _notify_plyer, _notify_powershell]
    for fn in backends:
        if fn(n):
            log.info("Notification sent [%s]: %s", fn.__name__, n.title)
            return
    log.info("Notification (log-only): [%s] %s", n.title, n.message)


# ─────────────────────────────────────────────
# Async public API
# ─────────────────────────────────────────────

async def notify(
    title: str,
    message: str,
    urgency: Literal["info", "warning", "error"] = "info",
    duration: int = 8,
) -> None:
    if not NOTIFY_ENABLED:
        log.debug("Notifications disabled: %s – %s", title, message)
        return
    n = Notification(title=title, message=message, urgency=urgency, duration=duration)
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _notify_sync, n)


# ─────────────────────────────────────────────
# Pre-built Jarvis events
# ─────────────────────────────────────────────

async def notify_batch_complete(batch_name: str, awp_count: int) -> None:
    await notify(
        title=f"Jarvis – {batch_name} Complete",
        message=f"{awp_count} work packages completed successfully.",
        urgency="info",
        duration=10,
    )


async def notify_pipeline_success(file: str) -> None:
    await notify(
        title="Jarvis – Pipeline ✅",
        message=f"{file} passed all gates.",
        urgency="info",
    )


async def notify_pipeline_failure(file: str, stage: str) -> None:
    await notify(
        title="Jarvis – Pipeline ❌",
        message=f"{file} failed at @{stage}. Human review required.",
        urgency="error",
        duration=15,
    )


async def notify_security_veto(file: str, findings: int) -> None:
    await notify(
        title="Jarvis – Security VETO 🔒",
        message=f"{findings} critical finding(s) in {file}. Change blocked.",
        urgency="error",
        duration=20,
    )


async def notify_container_restarted(name: str) -> None:
    await notify(
        title="Jarvis – Self-Heal",
        message=f"Container '{name}' was automatically restarted.",
        urgency="warning",
    )
