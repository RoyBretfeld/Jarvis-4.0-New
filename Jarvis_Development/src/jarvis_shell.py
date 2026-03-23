"""
Jarvis 4.0 – Kommando-Schnittstelle
Unterscheidet zwischen DEVELOPER-Modus und SYSTEM-Modus.

DEVELOPER-Modus: Voller Zugriff (Ingest, Search, Status, Librarian)
SYSTEM-Modus:    Eingeschränkt (nur Status + Search – kein Schreiben)

RB-Protokoll: Menschliche Hoheit – jede kritische Aktion zeigt Diff + wartet auf [Enter].
Python 3.12
"""

from __future__ import annotations

import asyncio
import cmd
import logging
import os
import sys
from pathlib import Path

# Add src/ to path for sibling imports
sys.path.insert(0, str(Path(__file__).parent))

log = logging.getLogger("jarvis.shell")

BANNER = """
╔══════════════════════════════════════════╗
║          JARVIS 4.0 – Shell v1.0         ║
║  RB-Protokoll: Transparenz | Revidierbar ║
╚══════════════════════════════════════════╝
Modus: {mode}
Tippe 'help' für verfügbare Befehle.
"""

# ─────────────────────────────────────────────
# Mode definitions
# ─────────────────────────────────────────────
DEV_COMMANDS = {"ingest", "search", "status", "skills", "health", "mode", "rollback", "exit", "quit"}
SYSTEM_COMMANDS = {"search", "status", "health", "mode", "exit", "quit"}


# ─────────────────────────────────────────────
# Shell
# ─────────────────────────────────────────────
class JarvisShell(cmd.Cmd):
    intro = ""
    prompt = "jarvis> "

    def __init__(self, mode: str = "system") -> None:
        super().__init__()
        self.mode = mode.lower()
        if self.mode not in ("developer", "system"):
            raise ValueError(f"Unknown mode: {mode!r}. Use 'developer' or 'system'.")
        self.prompt = f"jarvis[{self.mode[:3]}]> "

    # ─────────────────────────────────────────
    # Permission guard
    # ─────────────────────────────────────────
    def _allowed(self, cmd_name: str) -> bool:
        allowed = DEV_COMMANDS if self.mode == "developer" else SYSTEM_COMMANDS
        if cmd_name not in allowed:
            print(f"[DENIED] '{cmd_name}' ist im {self.mode.upper()}-Modus nicht erlaubt.")
            return False
        return True

    # ─────────────────────────────────────────
    # Commands
    # ─────────────────────────────────────────
    def do_mode(self, arg: str) -> None:
        """mode [developer|system]  – Modus wechseln."""
        new_mode = arg.strip().lower()
        if new_mode not in ("developer", "system"):
            print("Gültige Modi: developer, system")
            return
        if new_mode == "developer" and self.mode != "developer":
            confirm = input("Entwickler-Modus aktivieren? [j/N] ").strip().lower()
            if confirm != "j":
                print("Abgebrochen.")
                return
        self.mode = new_mode
        self.prompt = f"jarvis[{self.mode[:3]}]> "
        print(f"[OK] Modus gewechselt zu: {self.mode.upper()}")

    def do_status(self, _: str) -> None:
        """status  – Zeigt state.json und Heartbeat-Status."""
        if not self._allowed("status"):
            return
        state_path = Path(__file__).parent.parent / "state.json"
        if state_path.exists():
            import json
            state = json.loads(state_path.read_text(encoding="utf-8"))
            print(f"  Projekt:  {state.get('project', '?')}")
            print(f"  Phase:    {state.get('current_phase', '?')}")
            print(f"  Version:  {state.get('version', '?')}")
        else:
            print("  state.json nicht gefunden.")

        hb_path = Path(__file__).parent.parent / "logs" / "heartbeat_latest.json"
        if hb_path.exists():
            import json
            hb = json.loads(hb_path.read_text(encoding="utf-8"))
            icon = "✅" if hb.get("overall") == "healthy" else "❌"
            print(f"  Heartbeat: {icon} {hb.get('overall')} @ {hb.get('timestamp', '?')}")
        else:
            print("  Heartbeat: kein Log gefunden (heartbeat.py noch nicht ausgeführt).")

    def do_health(self, _: str) -> None:
        """health  – Prüft RAG-Backend-Verbindungen."""
        if not self._allowed("health"):
            return
        try:
            from memory_interface import get_memory  # type: ignore
            mem = get_memory()
            result = mem.health()
            for backend, ok in result.items():
                icon = "✅" if ok else "❌"
                print(f"  {icon} {backend}")
        except Exception as exc:
            print(f"  [ERROR] {exc}")

    def do_skills(self, _: str) -> None:
        """skills  – Listet alle geladenen Skills auf."""
        if not self._allowed("skills"):
            return
        try:
            from librarian import load_skills  # type: ignore
            skills_dir = Path(__file__).parent.parent / "skills"
            skills = load_skills(skills_dir)
            if not skills:
                print("  Keine Skills gefunden.")
                return
            for s in skills:
                print(f"  [{s.version}] {s.name:<30} {s.description[:60]}")
        except Exception as exc:
            print(f"  [ERROR] {exc}")

    def do_search(self, query: str) -> None:
        """search <query>  – Semantische Suche im RAG-Gedächtnis."""
        if not self._allowed("search"):
            return
        if not query.strip():
            print("Verwendung: search <Suchbegriff>")
            return
        try:
            results = asyncio.run(self._search_async(query.strip()))
            if not results:
                print("  Keine Treffer.")
                return
            print(f"  🔍 {len(results)} Treffer gefunden:\n")
            for i, r in enumerate(results, 1):
                src = r.document.metadata.get("source", "?")
                snippet = r.document.text[:120].replace("\n", " ")
                print(f"  [{i}] score={r.score:.3f} | {Path(src).name}")
                print(f"       {snippet}…\n")
        except Exception as exc:
            print(f"  [ERROR] {exc}")

    async def _search_async(self, query: str) -> list:
        from memory_interface import get_memory  # type: ignore
        return await get_memory().search(query, top_k=5)

    def do_ingest(self, path: str) -> None:
        """ingest [path]  – Lädt .md-Dateien in die Vektor-DB (nur DEV)."""
        if not self._allowed("ingest"):
            return
        target = Path(path.strip()) if path.strip() else (
            Path(__file__).parent.parent / "strategy"
        )
        print(f"  Starte Ingestion: {target}")
        print("  [RB] Schreibaktion – Bestätigen? [j/N] ", end="")
        confirm = input().strip().lower()
        if confirm != "j":
            print("  Abgebrochen.")
            return
        try:
            from ingest_docs import IngestionPipeline  # type: ignore
            pipeline = IngestionPipeline(docs_dir=target)
            totals = asyncio.run(pipeline.run())
            print(f"  ✅ Ingestion abgeschlossen: {totals}")
        except Exception as exc:
            print(f"  [ERROR] {exc}")

    # ── AWP-082: /rollback ────────────────────────────────────────────────
    def do_rollback(self, arg: str) -> None:
        """rollback [n]  – Macht den letzten (oder n-ten) Git-Commit rückgängig + state.json sync."""
        if not self._allowed("rollback"):
            return
        import subprocess, json

        repo = Path(__file__).parent.parent
        # Show what will be rolled back
        log_result = subprocess.run(
            ["git", "log", "--oneline", "-5"],
            cwd=str(repo), capture_output=True, text=True,
        )
        print("\n  Letzte Commits:")
        for line in log_result.stdout.strip().splitlines():
            print(f"    {line}")

        n = arg.strip() or "1"
        print(f"\n  [RB-Protokoll] Letzten {n} Commit(s) zurückrollen? [j/N] ", end="")
        confirm = input().strip().lower()
        if confirm != "j":
            print("  Abgebrochen.")
            return

        # Soft reset: keeps working tree, unstages commit
        result = subprocess.run(
            ["git", "reset", "--soft", f"HEAD~{n}"],
            cwd=str(repo), capture_output=True, text=True,
        )
        if result.returncode != 0:
            print(f"  [ERROR] git reset failed: {result.stderr.strip()}")
            return

        print(f"  ✅ Git-Rollback ({n} Commit(s)) erfolgreich.")

        # Sync state.json: decrement AWP count or mark last AWP as ROLLED_BACK
        state_path = repo / "state.json"
        if state_path.exists():
            try:
                state = json.loads(state_path.read_text(encoding="utf-8"))
                wps = state.get("workpackages", {})
                # Find last completed AWP and mark it rolled back
                completed = [k for k, v in wps.items() if v.get("status") == "COMPLETED"]
                if completed:
                    last_awp = sorted(completed)[-1]
                    wps[last_awp]["status"] = "ROLLED_BACK"
                    state["last_rollback"] = {
                        "awp": last_awp,
                        "rolled_back_at": __import__("datetime").datetime.utcnow().isoformat(),
                        "commits": int(n),
                    }
                    state_path.write_text(
                        json.dumps(state, indent=2), encoding="utf-8"
                    )
                    print(f"  ✅ state.json: {last_awp} → ROLLED_BACK")
            except Exception as exc:
                print(f"  [WARN] state.json sync failed: {exc}")

    def do_exit(self, _: str) -> bool:
        """exit  – Shell beenden."""
        print("Auf Wiedersehen.")
        return True

    def do_quit(self, arg: str) -> bool:
        """quit  – Shell beenden."""
        return self.do_exit(arg)

    def default(self, line: str) -> None:
        print(f"  Unbekannter Befehl: '{line}'. Tippe 'help'.")


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────
def main() -> None:
    logging.basicConfig(level=logging.WARNING,
                        format="%(asctime)s [%(levelname)s] %(message)s")

    mode = "system"
    for arg in sys.argv[1:]:
        if arg in ("--dev", "--developer"):
            mode = "developer"
        elif arg in ("--system",):
            mode = "system"

    shell = JarvisShell(mode=mode)
    print(BANNER.format(mode=shell.mode.upper()))
    try:
        shell.cmdloop()
    except KeyboardInterrupt:
        print("\nUnterbrochen.")


if __name__ == "__main__":
    main()
