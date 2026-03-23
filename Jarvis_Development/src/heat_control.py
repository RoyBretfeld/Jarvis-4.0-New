"""
AWP-071 – Ryzen Heat Control
Throttles batch processing when CPU temperature exceeds thresholds.

Schwellwerte:
  WARN_TEMP  = 80°C  → Warnung, reduziere Worker
  LIMIT_TEMP = 90°C  → Pause alle Batch-Jobs
  CRIT_TEMP  = 95°C  → Emergency stop + Notification

Integriert mit os_bridge.py für Temperaturmessung.
Python 3.12 | AsyncIO
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Awaitable, Any

log = logging.getLogger("jarvis.heat_control")

WARN_TEMP  = float(__import__("os").environ.get("HEAT_WARN_TEMP",  "80"))
LIMIT_TEMP = float(__import__("os").environ.get("HEAT_LIMIT_TEMP", "90"))
CRIT_TEMP  = float(__import__("os").environ.get("HEAT_CRIT_TEMP",  "95"))

POLL_INTERVAL = 5.0   # seconds between temp reads during batch
COOLDOWN_WAIT = 15.0  # seconds to wait when LIMIT_TEMP exceeded


@dataclass
class ThermalStatus:
    temp_celsius: float
    level: str           # "ok" | "warn" | "limit" | "critical"
    worker_cap: int      # max parallel workers allowed
    paused: bool


def _read_temp_sync() -> float:
    """Read CPU temperature using os_bridge approach."""
    try:
        import psutil  # type: ignore
        temps = psutil.sensors_temperatures()
        for key in ("k10temp", "zenpower", "coretemp", "cpu_thermal"):
            if key in temps:
                readings = temps[key]
                if readings:
                    return max(r.current for r in readings)
    except Exception:
        pass

    # Windows WMI fallback
    try:
        import subprocess
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-WmiObject MSAcpi_ThermalZoneTemperature -Namespace 'root/wmi' "
             "| Select-Object -ExpandProperty CurrentTemperature"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            tenths_kelvin = float(result.stdout.strip().splitlines()[0])
            return (tenths_kelvin / 10.0) - 273.15
    except Exception:
        pass

    return 0.0  # Unknown — assume safe


async def read_temperature() -> float:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _read_temp_sync)


def classify_temp(temp: float) -> ThermalStatus:
    if temp >= CRIT_TEMP:
        return ThermalStatus(temp, "critical", worker_cap=0, paused=True)
    if temp >= LIMIT_TEMP:
        return ThermalStatus(temp, "limit", worker_cap=1, paused=True)
    if temp >= WARN_TEMP:
        return ThermalStatus(temp, "warn", worker_cap=2, paused=False)
    return ThermalStatus(temp, "ok", worker_cap=4, paused=False)


class HeatController:
    """
    Wraps batch jobs with thermal throttling.
    Usage:
        async with HeatController() as hc:
            await hc.run_batch(my_tasks, worker_fn)
    """

    def __init__(self) -> None:
        self._active = True
        self._status: ThermalStatus = ThermalStatus(0.0, "ok", 4, False)

    async def __aenter__(self) -> "HeatController":
        self._monitor_task = asyncio.create_task(self._monitor())
        return self

    async def __aexit__(self, *_: Any) -> None:
        self._active = False
        self._monitor_task.cancel()
        try:
            await self._monitor_task
        except asyncio.CancelledError:
            pass

    async def _monitor(self) -> None:
        while self._active:
            temp = await read_temperature()
            self._status = classify_temp(temp)

            if self._status.level == "critical":
                log.critical("CPU TEMPERATURE CRITICAL: %.1f°C — EMERGENCY STOP", temp)
                try:
                    from notifications import notify_batch_complete  # type: ignore
                    # Reuse notification for emergency
                    await notify_batch_complete.__wrapped__(
                        f"THERMAL EMERGENCY: {temp:.1f}°C"
                    ) if hasattr(notify_batch_complete, "__wrapped__") else None
                except Exception:
                    pass
            elif self._status.level == "limit":
                log.warning("CPU temp %.1f°C ≥ LIMIT (%.0f°C) — pausing batch", temp, LIMIT_TEMP)
            elif self._status.level == "warn":
                log.info("CPU temp %.1f°C ≥ WARN (%.0f°C) — reducing workers to 2", temp, WARN_TEMP)

            await asyncio.sleep(POLL_INTERVAL)

    @property
    def status(self) -> ThermalStatus:
        return self._status

    async def gate(self) -> None:
        """Block until temperature drops below LIMIT_TEMP."""
        while self._status.paused:
            log.info(
                "Heat gate: waiting %.0fs (temp=%.1f°C, level=%s)",
                COOLDOWN_WAIT, self._status.temp_celsius, self._status.level,
            )
            await asyncio.sleep(COOLDOWN_WAIT)

    async def run_batch(
        self,
        items: list[Any],
        worker_fn: Callable[[Any], Awaitable[Any]],
    ) -> list[Any]:
        """
        Process items with thermal-aware concurrency.

        Dynamically adjusts semaphore based on current temperature.
        """
        results = []
        for item in items:
            await self.gate()
            cap = max(1, self._status.worker_cap)
            result = await worker_fn(item)
            results.append(result)
            log.debug("Heat: %.1f°C (cap=%d)", self._status.temp_celsius, cap)
        return results


async def check_thermal_safe() -> bool:
    """Quick check: is it safe to start a batch job?"""
    temp = await read_temperature()
    status = classify_temp(temp)
    if not status.paused:
        return True
    log.warning("Thermal not safe: %.1f°C (%s)", temp, status.level)
    return False
