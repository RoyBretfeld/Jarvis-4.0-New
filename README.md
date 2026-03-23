# 🛡️ RB-Protokoll v3.1

> Das Agent-Betriebssystem für saubere, sichere und nachvollziehbare KI-gesteuerte Entwicklung.
> Neu in v3.1: §5 Plan Execution Autonomy für maximale Effizienz bei strukturierten Plänen.

---

## Quick-Start

| Befehl | Was passiert |
|---|---|
| `/check` | Security-Scan + Baseline-Tests |
| `/bootstrap` | Umgebung prüfen & reparieren |
| `/pack` | Context-Dump für LLM/Debugging |
| `/flow-close` | UX-Audit gegen die 4 Gesetze |
| `/learn` | Fehler strukturiert dokumentieren |
| `/sentinelcheck` | Komplett-Audit aller Systeme |

## Python 3.12+ (Requirement)

**RB-Protokoll v3.1+ erfordert Python 3.12 oder höher.**

```bash
# Setup mit pyenv (empfohlen)
pyenv install 3.12
pyenv local 3.12        # Setzt Python 3.12 für diesen Ordner

# Oder manuell (`.python-version` Datei existiert bereits)
python --version        # Sollte 3.12.x zeigen
```

---

## Architektur

```
.agent/
├── skills/           7 Core-Skills (Bootstrap, Police, Packer, UX Guardian, Error Learner, Content Protocol, Doc Standard)
└── workflows/        7 Slash-Commands

.claude/
├── skills/           2 Claude Code Skills (Architect-Planer, Security-Sentinel)

docs/_rb/
├── 01_PLAN_EXECUTION.md  §5 Plan Execution Autonomy
├── 02_SYSTEM_FACTS.md    Projektspezifischer Kontext
└── 03_ERROR_DB.md        Gelerntes Fehlerwissen
```

## Zusätzliche Claude Code Skills (.claude/)

Spezialisierte Skills für Claude Code CLI Integration:

- **architect-planer** – Strategische Planung & Architektur-Entwurf
  - Denke 3 Schritte voraus
  - Prüfe Edge-Cases (Skalierung, Fehlerhandling)
  - Beachte .gitignore und Anforderungen

- **security-sentinel** – Schutzwall & Policy-Enforcer
  - Scanne auf Secrets vor jedem Commit
  - Verweigere Aktionen ohne Transparenz-Log
  - Erfordere "BESTÄTIGEN" für Systemänderungen

## Die 5 Gesetze des RB-Protokolls

### 🎯 UX-Gesetze

1. **§1 Transparenz** – Keine Hintergrund-Magie ohne Feedback
2. **§2 Revidierbarkeit** – Jede Aktion muss rückgängig machbar sein
3. **§3 Progressive Offenlegung** – Clean UI, Details per Click
4. **§4 Menschliche Hoheit** – KI schlägt vor, Mensch entscheidet

### ⚙️ Agenten-Betriebsmodus

5. **§5 Plan Execution Autonomy** – Sobald ein Plan finalisiert ist:
   - Plan strikt in chronologischer Reihenfolge einhalten
   - Mit größtmöglicher Autonomie umsetzen
   - Nicht bei jedem Schritt nachfragen
   - Nur bei echten Blockern unterbrechen

## 🎨 Design System: Sovereign Glass

Das RB-Protokoll wird mit **zwei Ebenen** von Design-Spezifikationen ausgeliefert:

### Ebene 1: Visuelle Identität ([DESIGN_SYSTEM_v1.md](docs/DESIGN_SYSTEM_v1.md))
- **Farbpalette**: Dark-Mode mit leuchtenden Akzenten
- **Layout**: 3-Säulen-Grid (Agent-Orchestration | Chat-Stream | Context-Pane)
- **Effects**: Glassmorphism, Streaming-Indikatoren, Checkpoint-Cards

### Ebene 2: Technische Spezifikation ([ARCHITEKT_THEME.md](docs/ARCHITEKT_THEME.md))
- **Universelle KI-Semantik**: Farbpalette, Typografie, UI-Komponenten als CSS-Variablen
- **UX-Fundament**: Glass-Box, Undo-First, Progressive Disclosure, Menschliche Hoheit
- **RAG-Integration**: Source-Cards, Citation-Links, Vektor-Pulse
- **Implementierungs-Roadmap**: Für Entwickler jeder Plattform

👉 **Für Designer:** [DESIGN_SYSTEM_v1.md](docs/DESIGN_SYSTEM_v1.md)
👉 **Für KI-Agenten:** [ARCHITEKT_THEME.md](docs/ARCHITEKT_THEME.md)

---

## 📦 Context-Dump Automation

Das RB-Protokoll erstellt automatisch Projekt-Snapshots:

- **Trigger:** Meilensteine, Dokumentation, Session-Ende
- **Speicher:** Lokal (`_rb-dump/`) + Zentral (`E:\_____1111____Projekte-Programmierung\Antigravity\.rb_dumps`)
- **Cleanup:** Nur neuster Dump pro Projekt (alte auto-gelöscht)

👉 **Vollständige Doku:** [DUMP_AUTOMATION.md](docs/DUMP_AUTOMATION.md)

---

## Dokumentation

- [Benutzerhandbuch](docs/BENUTZERHANDBUCH_v3.md) – Vollständige Anleitung
- [Architekt Theme](docs/ARCHITEKT_THEME.md) – **Technische Spezifikation für KI-Agenten**
- [Design System](docs/DESIGN_SYSTEM_v1.md) – Visuelle Identität und UX
- [Migrations-Plan](docs/MIGRATION_PLAN_v3.md) – Von v2.x zu v3.0
- [Archiv](/_archive/) – Alte v2.x Dateien (nicht gelöscht)

## Lizenz

Closed Source – Antigravity Project
