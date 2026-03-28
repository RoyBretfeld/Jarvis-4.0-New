import os
import platform
from typing import Any, List
from pathlib import Path
import logging
import aiohttp
import asyncio
from datetime import datetime, timezone

# ... (rest of the file content)

log = logging.getLogger(__name__)

def get_compose_file_path() -> Path:
    """Determine the path to the docker-compose.yml file."""
    compose_file = Path(__file__).parent.parent / "docker-compose.yml"
    if not compose_file.exists():
        log.error("docker-compose.yml not found at %s", compose_file)
        raise FileNotFoundError(f"docker-compose.yml not found at {compose_file}")
    return compose_file

# ... (rest of the file content)

async def run_once() -> HeartbeatReport:
    COMPOSE_FILE = get_compose_file_path()
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

# ... (rest of the file content)
