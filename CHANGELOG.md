# CHANGELOG

Alle wichtigen Änderungen am RB-Framework werden hier dokumentiert.

Format basiert auf [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [3.1.0] - 2026-03-18 – "Plan Execution Autonomy + Python 3.12 + Claude Code Integration"

### 🚀 Neue Regel: §5 Plan Execution Autonomy

- **NEU**: §5 Plan Execution Autonomy – Sobald ein Plan finalisiert ist, mit maximaler Autonomie in chronologischer Reihenfolge ausführen
- **NEU**: Detaillierte Dokumentation in `docs/_rb/01_PLAN_EXECUTION.md`
- **Update**: README.md zeigt nun alle 5 Gesetze (4 UX-Gesetze + §5 Betriebsmodus)
- **Update**: Benutzerhandbuch erweitert mit §5 Erklärung und Beispiel
- **Update**: CONTENT_PROTOCOL.md integriert §5-Modus für strukturierte Content-Erstellung
- **Update**: .cursorrules in beiden Versionen (Hauptordner + Export) mit §5 aktualisiert
- **Integration**: Export-rb-Protokoll/start.md zeigt §5 als zentrale neue Regel

### 🐍 Python 3.12 ist jetzt Standard

- **BREAKING**: Minimum Python Version erhöht von 3.11+ auf 3.12+
- **NEU**: `.python-version` Datei in Hauptordner + Export (für pyenv)
- **Update**: Alle Skills + CI/CD auf Python 3.12 aktualisiert
- **Update**: `.github/workflows/ci.yml` läuft jetzt auf Python 3.12
- **Update**: Error-DB Eintrag ERR-20251220-PY-VERSION aktualisiert

**Gründe für 3.12:**
- Match-case Statements für intelligente Plan-Ausführung
- Async/Await Verbesserungen für Event-basierte Workflows
- Performance: 5-10% schneller bei KI-Context-Processing

### 🛠️ Claude Code Integration (.claude/)

- **NEU**: 2 spezialisierte Claude Code Skills hinzugefügt:
  - `architect-planer` – Strategische Planung & Architektur-Entwurf (3 Schritte voraus)
  - `security-sentinel` – Schutzwall & Policy-Enforcer (Secrets-Scan, Transparenz-Log)
- **Update**: Alle .claude/skills in Export-Ordner integriert
- **Update**: .cursorrules dokumentiert beide Skill-Systeme (.agent/ und .claude/)
- **Update**: start.md Kopier-Befehle erweitert für .claude/

### 🎨 Design System: Sovereign Glass (IN PROGRESS)

- **NEU**: Vollständiges Design-System mit Spezifikation (DESIGN_SYSTEM_v1.md)
- **Farbpalette**: Dark-Mode mit funktionalen Leuchtfarben
- **Layout**: 3-Säulen-Raster (Agent-Orchestration | Chat-Stream | Context-Pane)
- **Effects**: Glassmorphism, Streaming-Animationen, Checkpoint-Cards
- **Update**: In beiden Versionen (Hauptordner + Export) integriert

### 📊 Impact

- Effizientere Plan-Ausführung ohne unnötige Unterbrechungen
- Maximale Autonomie bei strukturierten Ablaufplänen
- Nur echte Blocker triggerern Eskalation
- Alle 5 Gesetze sind jetzt als RB-Kernregeln dokumentiert
- Höhere Performance für KI-Integration und Context-Management
- Erweiterte Unterstützung für Claude Code CLI mit spezialiserten Skills

---

## [3.0.0] - 2026-02-19 – "Metamorphose"

### 🧠 Architektur-Migration (Skills-Native)

- **NEU**: 5 Core-Skills in `.agent/skills/` (Bootstrap, Police, Packer, UX Guardian, Error Learner)
- **NEU**: 6 Workflows als Slash-Commands (check, bootstrap, pack, flow-close, learn, sentinelcheck)
- **NEU**: Benutzerhandbuch `docs/BENUTZERHANDBUCH_v3.md`
- **NEU**: Globaler LLM-Packer Skill in `GLOBALE_SKILLS/llm_packer/`
- **MIGRATION**: Alle Python-Skripte in Skill-Ordner eingebettet (Kontext + Code = 1 Paket)
- **MIGRATION**: Passive Docs → aktive Skills (Agent kann ausführen, nicht nur lesen)
- **AUFGERÄUMT**: Duplikat `04_STANDARDS.md` / `04_UX_LAWS.md` in einen Skill vereint
- **AUFGERÄUMT**: Platzhalter-Dateien `05_SECURITY.md`, `06_TEST_MATRIX.md` in Skills integriert
- **ARCHIVIERT**: Alle v2.x Dateien in `_archive/` (nichts gelöscht, §2 Revidierbarkeit)

### 📊 Metriken

- Aktive Dateien: 16+ → 5 Skills + 6 Workflows
- Duplikate: 3 → 0
- Agent-Integration: Passiv → Nativ
- Slash-Commands: 0 → 6

---

## [2.0.0] - 2025-12-29

### ⚡ Performance

- **Police**: Git diff optimization - scannt nur geänderte Dateien (10-100x schneller)
- **Packer**: Effizienteres File Walking mit pathlib

### 🪟 Cross-Platform

- **Police**: Vollständige Windows/Linux/Mac Kompatibilität via pathlib
- **Packer**: Platform-agnostic directory handling
- **RB CLI**: Pfad-Validierung für alle Betriebssysteme

### 🎯 Features

- **Police**: Context-aware Secret Detection (ignoriert Kommentare/Platzhalter)
- **Police**: Konfigurierbarer Scan via `RB_POLICE_FULL_SCAN=true`
- **RB CLI**: Neuer `rb init` Command zur Setup-Validierung
- **RB CLI**: Placeholder-Validierung mit hilfreichen Fehlermeldungen
- **Packer**: Smart Directory Detection (findet `backend/`, `frontend/`, etc.)
- **Packer**: Konfigurierbar via `RB_PACK_INCLUDE=dir1,dir2`

### 📚 Documentation

- **SYSTEM_FACTS**: Beispiele für alle Platzhalter in HTML-Kommentaren
- **IMPROVEMENTS.md**: Detaillierte Dokumentation aller v2.0 Änderungen

### 🛡️ Security

- **Police**: Strengere Bearer Token Pattern
- **Police**: Secrets benötigen Quotes + Min-Length (weniger False Positives)

### 💬 UX

- Emoji-basierte Ausgaben für bessere Lesbarkeit
- Hilfreiche Error Messages mit konkreten Lösungsvorschlägen
- Progress-Feedback bei allen Scripts

---

## [1.0.0] - 2025-12-29

### Added

- Initial RB-Framework Setup
- Normative Docs (`docs/_rb/00-06`)
- Scripts: `rb.py`, `pre_commit_police.py`, `packer.py`
- GitHub Actions CI Workflow
- EditorConfig + GitIgnore
- README, RUNBOOK, LICENSE Templates
