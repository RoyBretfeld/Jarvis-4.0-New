"""
AWP-044 – Windows OS Bridge
Streamt CPU-Last (alle 32 Threads), Temperatur und SSD-Belegung
des Ryzen 9 7950X direkt in das UI-Widget.

Backends:
  - psutil       → CPU %, RAM %, Disk %
  - wmi (Windows) → CPU-Temperatur via MSAcpi_ThermalZoneTemperature
  - Fallback      → Keine Exception, nur None-Werte

Python 3.12 | AsyncIO
"""

from __future__ import annotations

import asyncio
import logging
import os
import platform
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

log = logging.getLogger("jarvis.os_bridge")

IS_WINDOWS = platform.system() == "Windows"
SSD1_PATH = os.environ.get("SSD1_MOUNT", "C:/")
SSD2_PATH = os.environ.get("SSD2_MOUNT", "E:/")


# ─────────────────────────────────────────────
# Data models
# ─────────────────────────────────────────────

@dataclass
class ThreadSample:
    threads: list[float]        # per-thread % (up to 32)
    avg_pct: float
    max_pct: float
    timestamp: str


@dataclass
class DiskInfo:
    path: str
    total_gb: float
    used_gb: float
    free_gb: float
    pct: float


@dataclass
class SystemSnapshot:
    cpu_threads: list[float]
    cpu_avg_pct: float
    cpu_max_pct: float
    ram_total_gb: float
    ram_used_gb: float
    ram_pct: float
    temp_celsius: float | None
    disks: list[DiskInfo]
    timestamp: str


# ─────────────────────────────────────────────
# CPU / RAM (psutil)
# ─────────────────────────────────────────────

def _get_cpu_threads() -> list[float]:
    try:
        import psutil  # type: ignore
        pct = psutil.cpu_percent(percpu=True, interval=0.1)
        # Pad / trim to 32 (Ryzen 9 7950X)
        while len(pct) < 32:
            pct.append(0.0)
        return pct[:32]
    except Exception as exc:
        log.debug("psutil cpu_percent failed: %s", exc)
        return [0.0] * 32


def _get_ram() -> tuple[float, float, float]:
    """Returns (total_gb, used_gb, pct)."""
    try:
        import psutil  # type: ignore
        vm = psutil.virtual_memory()
        return round(vm.total / 1e9, 1), round(vm.used / 1e9, 1), vm.percent
    except Exception:
        return 0.0, 0.0, 0.0


def _get_disk(path: str) -> DiskInfo | None:
    try:
        import psutil  # type: ignore
        usage = psutil.disk_usage(path)
        return DiskInfo(
            path=path,
            total_gb=round(usage.total / 1e9, 1),
            used_gb=round(usage.used / 1e9, 1),
            free_gb=round(usage.free / 1e9, 1),
            pct=usage.percent,
        )
    except Exception as exc:
        log.debug("disk_usage %s failed: %s", path, exc)
        return None


# ─────────────────────────────────────────────
# Temperature (Windows WMI)
# ─────────────────────────────────────────────

def _get_cpu_temp_windows() -> float | None:
    """Read CPU temperature via WMI on Windows."""
    if not IS_WINDOWS:
        return None
    try:
        import wmi  # type: ignore
        w = wmi.WMI(namespace="root/wmi")
        sensors = w.MSAcpi_ThermalZoneTemperature()
        if sensors:
            # WMI returns temperature in tenths of Kelvin
            temp_k = sensors[0].CurrentTemperature / 10.0
            return round(temp_k - 273.15, 1)
        return None
    except Exception as exc:
        log.debug("WMI temperature read failed: %s", exc)
        return None


def _get_cpu_temp_linux() -> float | None:
    """Read CPU temperature on Linux via psutil sensors."""
    try:
        import psutil  # type: ignore
        temps = psutil.sensors_temperatures()
        for key in ("coretemp", "k10temp", "zenpower"):
            if key in temps:
                current = temps[key][0].current
                return round(current, 1)
        return None
    except Exception:
        return None


def get_cpu_temperature() -> float | None:
    if IS_WINDOWS:
        return _get_cpu_temp_windows()
    return _get_cpu_temp_linux()


# ─────────────────────────────────────────────
# Snapshot aggregator
# ─────────────────────────────────────────────

def get_snapshot() -> SystemSnapshot:
    """Blocking – call via run_in_executor for async use."""
    threads = _get_cpu_threads()
    avg = round(sum(threads) / len(threads), 1) if threads else 0.0
    max_ = round(max(threads), 1) if threads else 0.0
    ram_total, ram_used, ram_pct = _get_ram()
    temp = get_cpu_temperature()
    disks = [d for d in [_get_disk(SSD1_PATH), _get_disk(SSD2_PATH)] if d]
    return SystemSnapshot(
        cpu_threads=threads,
        cpu_avg_pct=avg,
        cpu_max_pct=max_,
        ram_total_gb=ram_total,
        ram_used_gb=ram_used,
        ram_pct=ram_pct,
        temp_celsius=temp,
        disks=disks,
        timestamp=datetime.now(tz=timezone.utc).isoformat(),
    )


async def get_snapshot_async() -> SystemSnapshot:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, get_snapshot)


# ─────────────────────────────────────────────
# Streaming generator (for WebSocket push)
# ─────────────────────────────────────────────

async def stream_snapshots(interval: float = 1.0):
    """Async generator: yields SystemSnapshot every `interval` seconds."""
    log.info("OS Bridge streaming started (interval=%.1fs)", interval)
    while True:
        try:
            yield await get_snapshot_async()
        except Exception as exc:
            log.error("OS Bridge snapshot error: %s", exc)
        await asyncio.sleep(interval)


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import json, asyncio as _asyncio
    logging.basicConfig(level=logging.INFO)

    async def _demo() -> None:
        async for snap in stream_snapshots(interval=2.0):
            print(json.dumps({
                "avg_cpu": snap.cpu_avg_pct,
                "max_cpu": snap.cpu_max_pct,
                "ram_pct": snap.ram_pct,
                "temp":    snap.temp_celsius,
                "disks":   [{d.path: d.pct} for d in snap.disks],
            }, indent=2))

    _asyncio.run(_demo())
