"""
JARVIS 4.0 – Heartbeat Monitor
Prüft Erreichbarkeit aller Docker-Services und des Ollama-Backends.
Ryzen 9 7950X: Parallele Checks via ThreadPoolExecutor (32 Threads).
"""

import asyncio
import concurrent.futures
import json
import os
import urllib.request
import urllib.error
from datetime import datetime

SERVICES = {
    "jarvis-core":    "http://localhost:8765/health",
    "jarvis-rag":     "http://localhost:8766/health",
    "jarvis-gateway": "http://localhost:8767/health",
    "ollama":         f"{os.getenv('OLLAMA_HOST', 'http://localhost:11434')}/api/tags",
}

TIMEOUT = 5  # Sekunden


def check_service(name: str, url: str) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as resp:
            return {"service": name, "status": "UP", "code": resp.status, "url": url}
    except urllib.error.HTTPError as e:
        return {"service": name, "status": "DEGRADED", "code": e.code, "url": url}
    except Exception as e:
        return {"service": name, "status": "DOWN", "error": str(e), "url": url}


def run_heartbeat() -> list[dict]:
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(SERVICES)) as executor:
        futures = {
            executor.submit(check_service, name, url): name
            for name, url in SERVICES.items()
        }
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    return sorted(results, key=lambda x: x["service"])


def main():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n[{timestamp}] JARVIS Heartbeat Check")
    print("=" * 50)

    results = run_heartbeat()

    all_up = True
    for r in results:
        icon = "✅" if r["status"] == "UP" else ("⚠️" if r["status"] == "DEGRADED" else "❌")
        print(f"  {icon}  {r['service']:<20} {r['status']}")
        if r["status"] != "UP":
            all_up = False

    print("=" * 50)
    overall = "HEALTHY" if all_up else "DEGRADED"
    print(f"  Overall: {overall}\n")

    # State in .jarvis/state.json aktualisieren
    state_path = os.path.join(os.path.dirname(__file__), "..", ".jarvis", "state.json")
    state_path = os.path.normpath(state_path)
    if os.path.exists(state_path):
        with open(state_path, "r", encoding="utf-8") as f:
            state = json.load(f)
        state["last_heartbeat"] = timestamp
        state["heartbeat_status"] = overall
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

    return 0 if all_up else 1


if __name__ == "__main__":
    exit(main())
