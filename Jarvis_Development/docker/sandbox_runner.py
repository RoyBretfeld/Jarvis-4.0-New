"""
Jarvis Sandbox Runner
Läuft als Daemon im Sandbox-Container.
Empfängt Ausführungsaufträge von jarvis-core via /ws/terminal.
Führt Code isoliert aus, sendet Output zurück.
"""
import asyncio
import logging
import os
import signal
import sys

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [SANDBOX] %(message)s")
log = logging.getLogger("sandbox")


async def main() -> None:
    log.info("Sandbox runtime started (SANDBOX_MODE=%s)",
             os.environ.get("SANDBOX_MODE", "strict"))
    log.info("Workspace: /workspace  |  Threads: cpuset 8-15")

    # Keep alive — actual execution is triggered via docker exec
    # or via the /ws/terminal WebSocket in api_main.py
    stop = asyncio.Event()
    loop = asyncio.get_event_loop()

    def _shutdown(*_):
        log.info("Shutdown signal received.")
        stop.set()

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, _shutdown)

    log.info("Sandbox ready. Awaiting agent tasks.")
    await stop.wait()
    log.info("Sandbox stopped cleanly.")


if __name__ == "__main__":
    asyncio.run(main())
