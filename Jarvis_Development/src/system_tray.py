"""
AWP-074 – Windows System Tray Icon
Zeigt den aktuellen Aura-Status als farbiges Tray-Icon.

Dependencies (optional, graceful fallback):
  - pystray       (pip install pystray)
  - Pillow        (pip install Pillow)
  - httpx         (already in requirements)

Aura-Farben:
  idle       → Blue  (#1E90FF)
  processing → Violet (#8A2BE2)
  alert      → Red   (#FF4444)
  success    → Green (#00FF88)

Python 3.12 | Threading (pystray is synchronous)
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any

import httpx

log = logging.getLogger("jarvis.system_tray")

API_BASE    = "http://localhost:8000"
POLL_SECS   = 3

AURA_COLORS: dict[str, tuple[int, int, int]] = {
    "idle":       (30,  144, 255),   # Dodger Blue
    "processing": (138,  43, 226),   # Blue Violet
    "alert":      (255,  68,  68),   # Red
    "success":    (  0, 255, 136),   # Spring Green
}
DEFAULT_COLOR = AURA_COLORS["idle"]


def _make_icon_image(color: tuple[int, int, int], size: int = 64) -> Any:
    """Create a simple filled circle image for the tray icon."""
    try:
        from PIL import Image, ImageDraw  # type: ignore
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse([4, 4, size - 4, size - 4], fill=(*color, 255))
        return img
    except ImportError:
        return None


def _fetch_aura() -> str:
    """Poll /api/status for current aura state."""
    try:
        resp = httpx.get(f"{API_BASE}/status", timeout=2)
        data = resp.json()
        return data.get("aura", "idle")
    except Exception:
        return "idle"


class JarvisTray:
    """Manages the Windows system tray icon for Jarvis."""

    def __init__(self) -> None:
        self._icon: Any = None
        self._current_aura = "idle"
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self) -> bool:
        """Start the tray icon in a background thread. Returns False if unavailable."""
        try:
            import pystray  # type: ignore
        except ImportError:
            log.warning("pystray not installed — system tray disabled")
            return False

        try:
            from PIL import Image  # type: ignore
        except ImportError:
            log.warning("Pillow not installed — system tray disabled")
            return False

        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True, name="jarvis-tray")
        self._thread.start()
        log.info("System tray started")
        return True

    def stop(self) -> None:
        self._running = False
        if self._icon:
            try:
                self._icon.stop()
            except Exception:
                pass

    def _run(self) -> None:
        import pystray  # type: ignore

        img = _make_icon_image(DEFAULT_COLOR)
        if img is None:
            return

        menu = pystray.Menu(
            pystray.MenuItem("Jarvis 4.0", lambda: None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Open Dashboard", self._open_dashboard),
            pystray.MenuItem("Stop Tray", self._stop_from_menu),
        )

        self._icon = pystray.Icon(
            "Jarvis",
            img,
            "Jarvis 4.0 — idle",
            menu,
        )

        # Poll loop in separate thread
        poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        poll_thread.start()

        self._icon.run()

    def _poll_loop(self) -> None:
        while self._running:
            aura = _fetch_aura()
            if aura != self._current_aura:
                self._current_aura = aura
                self._update_icon(aura)
            time.sleep(POLL_SECS)

    def _update_icon(self, aura: str) -> None:
        if self._icon is None:
            return
        color = AURA_COLORS.get(aura, DEFAULT_COLOR)
        img = _make_icon_image(color)
        if img:
            self._icon.icon = img
        self._icon.title = f"Jarvis 4.0 — {aura}"
        log.debug("Tray icon updated: %s", aura)

    def _open_dashboard(self) -> None:
        import subprocess
        subprocess.Popen(
            ["start", f"{API_BASE.replace(':8000', ':3000')}"],
            shell=True,
        )

    def _stop_from_menu(self) -> None:
        self.stop()


# Module-level singleton
_tray: JarvisTray | None = None


def start_tray() -> bool:
    """Start the global tray instance."""
    global _tray
    if _tray is not None:
        return True
    _tray = JarvisTray()
    return _tray.start()


def stop_tray() -> None:
    global _tray
    if _tray:
        _tray.stop()
        _tray = None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ok = start_tray()
    if ok:
        print("Tray running. Press Ctrl+C to stop.")
        try:
            import time as _time
            while True:
                _time.sleep(1)
        except KeyboardInterrupt:
            stop_tray()
    else:
        print("Tray unavailable (install pystray + Pillow)")
