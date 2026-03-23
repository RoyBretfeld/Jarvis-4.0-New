# System Facts

## Mission: Lokaler, souveräner KI-Assistent (Sovereign Local AI Stack)
<!-- JARVIS 4.0 ist ein vollständig lokales Multi-Agent-System auf Basis von Qwen2.5-Coder 14b,
     das als Control Center (3-Spalten-UI mit Monaco Editor + OpenShell-Sandbox) betrieben wird.
     RAG-System, Skill-Architektur und Docker-Isolation. Kein Daten-Abfluss. -->

## Tech Stack
- **Language:** Python 3.12+ | Docker | Qwen2.5-Coder 14b (via Ollama)
- **Platform:** Windows 11 Pro | AMD Ryzen 9 7950X (32 Threads) | Lokale SSD

## Agent-Rollen
- **@coder** – Lead Developer (implementiert AWPs)
- **@tester** – Sandbox-Validator (OpenShell)
- **@security** – Sentinel (RB-Compliance, Privacy Masking)
- **Orchestrator** – Claude Code (du), koordiniert alle Agenten

## Important Paths
- **Jarvis Root:** e:\_____1111____Projekte-Programmierung\Antigravity\___JARVIS-4.0\
- **Strategy Docs:** Jarvis_Development/strategy/  (21 Dokumente)
- **Skills (Jarvis):** Jarvis_Development/skills/
- **State File:** .jarvis/state.json
- **Error DB:** docs/_rb/03_ERROR_DB.md
- **Zentrale Error DB:** E:\_____1111____Projekte-Programmierung\Antigravity\03_ERROR_DB.md
- **RB Protocols:** .agent/skills/ und .agent/workflows/

## Critical Commands
- Start: `py -3.12 .agent/skills/rb_bootstrap/scripts/installer.py`
- Test: `py -3.12 .agent/skills/rb_police/scripts/pre_commit_police.py`
- Pack: `py -3.12 .agent/skills/rb_packer/scripts/packer.py`

## Masterplan-Referenz
- Execution Masterplan: Jarvis_Development/strategy/Jarvis_EXECUTION_MASTERPLAN_V1.md
- AWP-Standard: Jarvis_Development/strategy/Jarvis_Atomic_WorkPackage_Standard.md
- SEC-Protokoll: Jarvis_Development/strategy/Jarvis_Sequential_Execution_Control.md
