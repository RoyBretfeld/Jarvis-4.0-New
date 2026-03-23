"""
Jarvis 4.0 – Heartbeat Monitor
AWP-005: Docker-Status & Ollama-Connectivity
AWP-047: Self-Healing – automatically restarts crashed containers
Python 3.12 | AsyncIO | RB-Protokoll: Transparenz (Glass-Box)
"""

import asyncio
import json
import logging
import os
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import aiohttp

# ─────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "heartbeat.log", encoding="utf-8"),
    ],
)
log = logging.getLogger("jarvis.heartbeat")

# ─────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────
OLLAMA_BASE_URL  = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
POLL_INTERVAL    = int(os.environ.get("HEARTBEAT_INTERVAL", "30"))
SELF_HEAL        = os.environ.get("HEARTBEAT_SELF_HEAL", "true").lower() == "true"
COMPOSE_FILE     = Path(__file__).parent.parent / "docker-compose.yml"
MAX_RESTART_PER_CYCLE = 2     # guard: don't restart more than N per poll

CONTAINERS = [
    "jarvis-core",
    "jarvis-rag",
    "jarvis-gateway",
    "jarvis-sandbox",
]

StatusType = Literal["healthy", "unhealthy", "unreachable", "unknown"]


# ─────────────────────────────────────────────
# Data models
# ─────────────────────────────────────────────
@dataclass
class ContainerStatus:
    name: str
    status: StatusType = "unknown"
    exit_code: int | None = None
    message: str = ""
    restarted: bool = False      # AWP-047: track self-heal actions


@dataclass
class OllamaStatus:
    reachable: bool = False
    url: str = ""
    models: list[str] = field(default_factory=list)
    message: str = ""


@dataclass
class HeartbeatReport:
    timestamp: str
    containers: list[ContainerStatus]
    ollama: OllamaStatus
    overall: StatusType = "unknown"
    self_heals: int = 0          # how many containers were auto-restarted


# ─────────────────────────────────────────────
# Docker checks
# ─────────────────────────────────────────────
async def check_container(name: str) -> ContainerStatus:
    """Check container status via `docker inspect` subprocess (Windows-compatible)."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "docker", "inspect", "--format",
            "{{.State.Running}}|{{.State.ExitCode}}|{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}",
            name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10)
        if proc.returncode != 0:
            err = stderr.decode(errors="replace").strip()
            if "No such container" in err:
                return ContainerStatus(name=name, status="unreachable",
                                       message="Container not found")
            return ContainerStatus(name=name, status="unreachable", message=err[:120])
        parts = stdout.decode(errors="replace").strip().split("|")
        running = parts[0] == "true"
        exit_code = int(parts[1]) if parts[1].lstrip("-").isdigit() else None
        health = parts[2] if len(parts) > 2 else "none"
        status: StatusType = (
            "healthy"    if running and health in ("healthy", "none", "starting")
            else "unhealthy" if running
            else "unreachable"
        )
        return ContainerStatus(
            name=name, status=status,
            exit_code=exit_code,
            message=f"running={running}, health={health}",
        )
    except (asyncio.TimeoutError, FileNotFoundError) as exc:
        return ContainerStatus(name=name, status="unreachable", message=str(exc))


async def check_all_containers() -> list[ContainerStatus]:
    return list(await asyncio.gather(
        *[check_container(n) for n in CONTAINERS]
    ))


# ─────────────────────────────────────────────
# AWP-047: Self-Healing
# ─────────────────────────────────────────────
async def _restart_container(name: str) -> bool:
    """Restart a container via docker compose. Returns True on success."""
    if not COMPOSE_FILE.exists():
        log.error("Self-heal skipped: compose file not found at %s", COMPOSE_FILE)
        return False
    try:
        proc = await asyncio.create_subprocess_exec(
            "docker", "compose",
            "-f", str(COMPOSE_FILE),
            "restart", name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=60)
        success = proc.returncode == 0
        log.warning(
            "Self-heal %s: restart exit=%d output=%s",
            name, proc.returncode,
            stdout.decode(errors="replace")[:200],
        )
        return success
    except (asyncio.TimeoutError, FileNotFoundError) as exc:
        log.error("Self-heal %s failed: %s", name, exc)
        return False


async def self_heal(
    statuses: list[ContainerStatus],
) -> int:
    """Restart unhealthy/unreachable containers. Returns count restarted."""
    if not SELF_HEAL:
        return 0
    # Exclude sandbox – it's intentionally non-persistent
    candidates = [
        s for s in statuses
        if s.status in ("unreachable", "unhealthy")
        and s.name != "jarvis-sandbox"
    ][:MAX_RESTART_PER_CYCLE]

    healed = 0
    for cs in candidates:
        log.warning("Self-heal: %s is %s – restarting…", cs.name, cs.status)
        ok = await _restart_container(cs.name)
        if ok:
            cs.restarted = True
            cs.status = "healthy"   # optimistic – next cycle will verify
            healed += 1
    return healed


# ─────────────────────────────────────────────
# Ollama check
# ─────────────────────────────────────────────
async def check_ollama(session: aiohttp.ClientSession) -> OllamaStatus:
    url = f"{OLLAMA_BASE_URL}/api/tags"
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status != 200:
                return OllamaStatus(reachable=False, url=OLLAMA_BASE_URL,
                                    message=f"HTTP {resp.status}")
            data = await resp.json()
            models = [m["name"] for m in data.get("models", [])]
            return OllamaStatus(reachable=True, url=OLLAMA_BASE_URL,
                                models=models,
                                message=f"{len(models)} model(s) available")
    except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
        return OllamaStatus(reachable=False, url=OLLAMA_BASE_URL, message=str(exc))


# ─────────────────────────────────────────────
# Report
# ─────────────────────────────────────────────
def compute_overall(
    containers: list[ContainerStatus], ollama: OllamaStatus
) -> StatusType:
    if not ollama.reachable:
        return "unhealthy"
    statuses = {c.status for c in containers if c.name != "jarvis-sandbox"}
    if "unhealthy" in statuses or "unreachable" in statuses:
        return "unhealthy"
    return "healthy"


def log_report(report: HeartbeatReport) -> None:
    icon = "✅" if report.overall == "healthy" else "❌"
    log.info("%s [%s] overall=%s heals=%d", icon, report.timestamp,
             report.overall, report.self_heals)
    for c in report.containers:
        heal_tag = " [RESTARTED]" if c.restarted else ""
        log.info("  %-22s status=%-12s %s%s", c.name, c.status, c.message, heal_tag)
    log.info("  Ollama %-26s reachable=%-5s %s",
             report.ollama.url, report.ollama.reachable, report.ollama.message)


def persist_report(report: HeartbeatReport) -> None:
    path = LOG_DIR / "heartbeat_latest.json"
    with path.open("w", encoding="utf-8") as fh:
        json.dump(asdict(report), fh, indent=2)


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
async def run_once() -> HeartbeatReport:
    async with aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(limit=10)
    ) as session:
        containers, ollama = await asyncio.gather(
            check_all_containers(),
            check_ollama(session),
        )
    heals = await self_heal(containers)
    report = HeartbeatReport(
        timestamp=datetime.now(tz=timezone.utc).isoformat(),
        containers=containers,
        ollama=ollama,
        overall=compute_overall(containers, ollama),
        self_heals=heals,
    )
    log_report(report)
    persist_report(report)
    return report


async def run_loop() -> None:
    log.info("Jarvis Heartbeat Monitor started (interval=%ds, self_heal=%s)",
             POLL_INTERVAL, SELF_HEAL)
    while True:
        try:
            await run_once()
        except Exception as exc:
            log.error("Heartbeat error: %s", exc, exc_info=True)
        await asyncio.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    if "--once" in sys.argv:
        report = asyncio.run(run_once())
        sys.exit(0 if report.overall == "healthy" else 1)
    else:
        asyncio.run(run_loop())
