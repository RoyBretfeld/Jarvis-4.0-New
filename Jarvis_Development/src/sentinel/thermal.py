"""
AWP-085 – Thermal Watchdog (src/sentinel/thermal.py)
Überwacht Ryzen 9 7950X Temperaturen kontinuierlich.

Schwellwerte:
  WARN  = 80°C  → Log-Warnung
  PAUSE = 85°C  → Pausiert alle Batch-Prozesse (setzt THERMAL_PAUSE event)
  CRIT  = 92°C  → Emergency-Notification + forcierter GC

Liest via psutil (k10temp/zenpower) oder WMI (Windows).
Kann als Standalone-Prozess oder als importiertes Modul verwendet werden.

Python 3.12 | AsyncIO | threading.Event für prozessweite Pause
"""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

log = logging.getLogger("jarvis.sentinel.thermal")

# ── Thresholds ─────────────────────────────────────────────────────────────
WARN_C  = float(__import__("os").environ.get("THERMAL_WARN",  "80"))
PAUSE_C = float(__import__("os").environ.get("THERMAL_PAUSE", "85"))
CRIT_C  = float(__import__("os").environ.get("THERMAL_CRIT",  "92"))

POLL_INTERVAL_S = 3.0    # polling interval
LOG_PATH = Path(__file__).parent.parent.parent / "logs" / "thermal.log"

# ── Prozessweites Pause-Event ───────────────────────────────────────────────
# Other modules can call: thermal.THERMAL_PAUSE.wait() to block when hot.
THERMAL_PAUSE: threading.Event = threading.Event()


@dataclass
class ThermalReading:
    celsius: float
    level: str          # "ok" | "warn" | "pause" | "critical"
    source: str
    timestamp: str


# ── Temperature readers ─────────────────────────────────────────────────────

def _read_psutil() -> tuple[float, str] | None:
    try:
        import psutil  # type: ignore
        temps = psutil.sensors_temperatures()
        for key in ("k10temp", "zenpower", "coretemp", "cpu_thermal"):
            if key in temps and temps[key]:
                t = max(r.current for r in temps[key])
                return t, key
    except Exception:
        pass
    return None


def _read_wmi() -> tuple[float, str] | None:
    """Windows WMI fallback — reads ACPI thermal zone."""
    try:
        import subprocess
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-WmiObject MSAcpi_ThermalZoneTemperature -Namespace root/wmi "
             "| Select-Object -ExpandProperty CurrentTemperature"],
            capture_output=True, text=True, timeout=4,
        )
        if r.returncode == 0 and r.stdout.strip():
            tenths_k = float(r.stdout.strip().splitlines()[0])
            celsius = (tenths_k / 10.0) - 273.15
            return celsius, "wmi"
    except Exception:
        pass
    return None


def read_cpu_temp() -> ThermalReading:
    """Read current CPU temperature, best available source."""
    ts = datetime.now(tz=timezone.utc).isoformat()
    for reader in (_read_psutil, _read_wmi):
        result = reader()
        if result is not None:
            celsius, source = result
            level = "ok"
            if celsius >= CRIT_C:
                level = "critical"
            elif celsius >= PAUSE_C:
                level = "pause"
            elif celsius >= WARN_C:
                level = "warn"
            return ThermalReading(celsius=celsius, level=level,
                                  source=source, timestamp=ts)
    # No sensor found — return unknown-safe reading
    return ThermalReading(celsius=0.0, level="ok", source="unknown", timestamp=ts)


# ── Log writer ──────────────────────────────────────────────────────────────

def _log_reading(r: ThermalReading) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    prefix = {
        "ok": "  ",
        "warn": "⚠ ",
        "pause": "🔴",
        "critical": "🚨",
    }.get(r.level, "  ")
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(f"[{r.timestamp}] {prefix} {r.celsius:.1f}°C ({r.source}) [{r.level}]\n")


# ── Async watchdog ──────────────────────────────────────────────────────────

class ThermalWatchdog:
    """
    Async watchdog: runs in background, manages THERMAL_PAUSE event.

    Usage:
        watchdog = ThermalWatchdog()
        await watchdog.start()
        # Elsewhere: thermal.THERMAL_PAUSE.wait() blocks when temp >= PAUSE_C
        await watchdog.stop()
    """

    def __init__(
        self,
        on_pause: Callable[[float], None] | None = None,
        on_resume: Callable[[float], None] | None = None,
        on_critical: Callable[[float], None] | None = None,
    ) -> None:
        self._running = False
        self._task: asyncio.Task | None = None
        self._paused = False
        self.on_pause = on_pause
        self.on_resume = on_resume
        self.on_critical = on_critical

    async def start(self) -> None:
        self._running = True
        self._task = asyncio.create_task(self._loop(), name="thermal-watchdog")
        log.info(
            "Thermal watchdog started (warn=%.0f pause=%.0f crit=%.0f)",
            WARN_C, PAUSE_C, CRIT_C,
        )

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        THERMAL_PAUSE.clear()

    async def _loop(self) -> None:
        loop = asyncio.get_event_loop()
        while self._running:
            reading = await loop.run_in_executor(None, read_cpu_temp)

            # Log every reading (only anomalies to avoid log spam)
            if reading.level != "ok":
                await loop.run_in_executor(None, _log_reading, reading)

            if reading.level in ("pause", "critical"):
                if not self._paused:
                    self._paused = True
                    THERMAL_PAUSE.set()   # signal all batch workers to pause
                    log.warning(
                        "THERMAL PAUSE: %.1f°C ≥ %.0f°C — all batch workers paused",
                        reading.celsius, PAUSE_C,
                    )
                    if self.on_pause:
                        self.on_pause(reading.celsius)

                if reading.level == "critical":
                    log.critical("THERMAL CRITICAL: %.1f°C", reading.celsius)
                    if self.on_critical:
                        self.on_critical(reading.celsius)
                    import gc; gc.collect()

            else:
                if self._paused:
                    self._paused = False
                    THERMAL_PAUSE.clear()  # resume batch workers
                    log.info(
                        "Thermal OK: %.1f°C — batch workers resumed",
                        reading.celsius,
                    )
                    if self.on_resume:
                        self.on_resume(reading.celsius)

                if reading.level == "warn":
                    log.warning("Thermal warn: %.1f°C ≥ %.0f°C", reading.celsius, WARN_C)

            await asyncio.sleep(POLL_INTERVAL_S)


# ── Convenience: check before starting any heavy work ──────────────────────

def is_thermal_safe() -> bool:
    """Non-async quick check. Returns False when temp >= PAUSE_C."""
    return not THERMAL_PAUSE.is_set()


def wait_for_cooldown(timeout: float = 120.0) -> bool:
    """Block the calling thread until temp drops below PAUSE_C. Returns True if cooled."""
    if not THERMAL_PAUSE.is_set():
        return True
    log.info("Waiting for thermal cooldown (max %.0fs)…", timeout)
    # THERMAL_PAUSE.wait blocks while SET; we want to wait until CLEARED
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not THERMAL_PAUSE.is_set():
            return True
        time.sleep(2)
    return False


# ── Standalone run ──────────────────────────────────────────────────────────

async def _main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    def on_pause(t: float) -> None:
        print(f"\n🔴 PAUSE at {t:.1f}°C — all Jarvis batch processes halted")

    def on_resume(t: float) -> None:
        print(f"\n✅ RESUME at {t:.1f}°C — batch processes can continue")

    def on_crit(t: float) -> None:
        print(f"\n🚨 CRITICAL {t:.1f}°C — check cooling immediately!")

    wd = ThermalWatchdog(on_pause=on_pause, on_resume=on_resume, on_critical=on_crit)
    await wd.start()

    print(f"Thermal watchdog running (pause={PAUSE_C}°C). Ctrl+C to stop.")
    print("Logging to:", LOG_PATH)

    try:
        while True:
            r = read_cpu_temp()
            print(f"\r  CPU: {r.celsius:.1f}°C [{r.level}] ({r.source})     ", end="", flush=True)
            await asyncio.sleep(POLL_INTERVAL_S)
    except asyncio.CancelledError:
        pass
    finally:
        await wd.stop()


if __name__ == "__main__":
    asyncio.run(_main())
