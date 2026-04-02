# 🛡️ RB-Protokoll v3.1 – Das Agent-Betriebssystem

> **Die Mission:** Ein standardisierter, sicherer und hochgradig effizienter Workflow für die KI-gestützte Softwareentwicklung.

### 🎯 Die Absicht (Intent)
Das RB-Protokoll löst das Problem von "wild arbeitenden" KIs. Es transformiert einen Agenten von einem reinen Code-Generator zu einem verantwortungsvollen **Senior Engineer**, der:
- **Fehler niemals zweimal macht** (durch die Error-DB).
- **Security & Compliance** aktiv überwacht (durch die Police).
- **Software für Menschen baut** (durch die 5 Gesetze: 4 UX-Gesetze + §5 Plan Execution Autonomy).
- **Strukturierte Dokumentation** hinterlässt (durch den Doc-Standard).
- **SEO & KI-Sichtbarkeit** von Anfang an mitdenkt (durch das Content-Protokoll).

### 🛠️ Was es macht (Function)
Es fungiert als **Zwischenschicht** zwischen dir (Mensch) und der KI (Agent). Es liefert:
1.  **Skills (Fähigkeiten)**: Vordefinierte Regelwerke für Spezialaufgaben (Sicherheit, UX, Lernen).
2.  **Workflows (Prozesse)**: Standardisierte Slash-Commands (`/check`, `/bootstrap`), die sicherstellen, dass Qualitäts-Gates eingehalten werden.
3.  **Gedächtnis**: Eine projektübergreifende Datenbank für gelöste Probleme, damit Wissen kumulativ wächst.
4.  **Transparenz**: Jede Aktion der KI wird nachvollziehbar und revidierbar (§2 Gesetz).

---

## ⚙️ System-Anforderungen

**Python 3.12 oder höher (erforderlich)**

```bash
# Überprüfung
python --version

# Falls falsch, mit pyenv umschalten
pyenv install 3.12
pyenv local 3.12        # .python-version wird automatisch erstellt
```

Warum 3.12? Match-case Statements für §5 Plan Execution, Async-Verbesserungen, bessere Performance für KI-Context-Processing.

---

# 🚀 START – RB-Protokoll in ein neues Projekt integrieren

## 📦 Was steckt in diesem Paket?

```
Export-rb-Protokoll/
├── start.md                    ← DU BIST HIER
├── .cursorrules                ← Editor-Config (Cursor/Windsurf)
├── .agent/
│   ├── skills/                 ← 7 Skills (Agent-Fähigkeiten)
│   │   ├── rb_bootstrap/       Boot + Selbstheilung
│   │   ├── rb_police/          Security-Scanner
│   │   ├── rb_packer/          Context-Dump Generator
│   │   ├── ux_guardian/        Die 4 UX-Gesetze
│   │   ├── error_learner/      Fehlerwissen-Management
│   │   ├── content_protocol/   SEO + KI Content-Leitfaden
│   │   └── doc_standard/       Dokumentations-Standard
│   └── workflows/              ← 7 Slash-Commands
│       ├── bootstrap.md        /bootstrap
│       ├── check.md            /check
│       ├── pack.md             /pack
│       ├── flow-close.md       /flow-close
│       ├── learn.md            /learn
│       ├── sentinelcheck.md    /sentinelcheck
│       └── content.md          /content
├── .claude/
│   └── skills/                 ← 2 Claude Code Skills
│       ├── architect-planer/   Strategische Planung & Architektur
│       └── security-sentinel/  Schutzwall & Policy-Enforcer
└── docs/
    ├── DESIGN_SYSTEM_v1.md     ← Sovereign Glass UI/UX System
    └── _rb/
        ├── 00_BOOT_PROTOCOL.md  ← Verfassung (DoD, Guardrails, Agent-Regeln)
        ├── 01_AGENT_LOOP.md     ← 9-Schritt Arbeitsschleife
        ├── 01_MISSION_PROMPT.md ← GSD-Phasen (MAP/SPEC/PLAN/EXEC/VERIFY)
        ├── 01_PLAN_EXECUTION.md ← §5 Plan Execution Autonomy
        ├── 02_SYSTEM_FACTS.md   ← Template (muss ausgefüllt werden)
        ├── 03_ERROR_DB.md       ← Template (wächst mit der Zeit)
        ├── 04_STANDARDS.md      ← Code- & Architektur-Regeln
        ├── 04_UX_LAWS.md        ← Die 4 UX-Gesetze
        ├── 05_SECURITY.md       ← Security-Regeln (Secrets, Auth, DSGVO)
        ├── 06_TEST_MATRIX.md    ← Testmatrix-Template
        └── BOOTSTRAP_PROMPT.md  ← Onboarding-Prompt für neue Projekte
```

---

## 🔧 SCHRITT 1: Dateien ins Zielprojekt kopieren

### Was du brauchst
- Einen Projektordner (z.B. `E:\MeinProjekt\`)
- PowerShell oder Terminal

### Kopier-Befehle

```powershell
# ══════════════════════════════════════════════════════════════
# Passe diese Variable an dein Zielprojekt an:
$ZIEL = "E:\Pfad\zu\deinem\Projekt"
# ══════════════════════════════════════════════════════════════

# Quelle (dieser Ordner)
$QUELLE = "E:\_____1111____Projekte-Programmierung\Antigravity\_rb-Protokoll\Export-rb-Protokoll"

# 1. Skills + Workflows kopieren (Für Antigravity / Gemini)
Copy-Item -Path "$QUELLE\.agent" -Destination "$ZIEL\.agent" -Recurse -Force

# 2. Claude Code Skills kopieren (Für Cursor / Claude Code CLI)
Copy-Item -Path "$QUELLE\.claude" -Destination "$ZIEL\.claude" -Recurse -Force

# 3. Docs-Templates kopieren (Zentrale Doku)
Copy-Item -Path "$QUELLE\docs" -Destination "$ZIEL\docs" -Recurse -Force

# 4. Editor-Config kopieren (Für Cursor / Windsurf)
Copy-Item -Path "$QUELLE\.cursorrules" -Destination "$ZIEL\.cursorrules" -Force
```

### Ergebnis prüfen

Egal welchen Editor du nutzt, dein Projekt sollte immer beide Pfade haben:

```
MeinProjekt/
├── .agent/              ← Wichtig für Antigravity/Gemini
│   ├── skills/          
│   └── workflows/       
├── .cursorrules         ← Wichtig für Cursor/Windsurf
├── docs/                ← Projekt-Identität
│   └── _rb/
└── ...
```

---

## 🔧 SCHRITT 1b: BOOTSTRAP_PROMPT ausführen (empfohlen)

Nach dem Kopieren startest du einmalig den **Bootstrap-Prozess**, der das Framework auf dein Projekt zuschneidet:

```
Öffne eine neue Agent-Session und sende den Inhalt von:
docs/_rb/BOOTSTRAP_PROMPT.md
```

Der Agent passt dann automatisch `02_SYSTEM_FACTS.md`, `06_TEST_MATRIX.md`, `scripts/pre_commit_police.py` und `scripts/packer.py` auf deinen konkreten Stack an.

---

## 🔧 SCHRITT 2: SYSTEM_FACTS ausfüllen

Öffne `docs/_rb/02_SYSTEM_FACTS.md` und ersetze **alle Platzhalter**:

```markdown
# System Facts

## Mission: {{PROJECT_MISSION}}
<!-- Was baut dieses Projekt? In 1-2 Sätzen. -->
<!-- Beispiel: "E-Commerce SaaS für Holzverarbeitung" -->

## Tech Stack
- **Language:** {{LANG_FRAMEWORK}}
- **Platform:** {{PLATFORM}}

## Important Paths
- **Error DB:** docs/_rb/03_ERROR_DB.md
- **Zentrale Error DB:** E:\_____1111____Projekte-Programmierung\Antigravity\03_ERROR_DB.md
- **RB Protocols:** .agent/skills/ und .agent/workflows/

## Critical Commands
- Start: {{START_CMD}}
- Test: {{TEST_CMD}}
```

> ⚠️ **Keine Platzhalter `{{...}}` stehen lassen!** Der Agent warnt bei unfilled Placeholders.

---

## 🔧 SCHRITT 3: Editor-spezifische Konfiguration

### Für Cursor / Windsurf
Die `.cursorrules` ist bereits kopiert. Sie definiert die Skills in `.agent/skills/` als **verbindliche Instruktionen**. Cursor wird diese Dateien bei jedem Task als Basis für sein Handeln nutzen (ähnlich wie System-Prompts).

### Für Antigravity / Gemini Code Assist
Antigravity nutzt primär den `.agent/` Ordner. 
Stelle sicher, dass in den Gemini-Einstellungen der Pfad zu den Workflows hinterlegt ist (meist automatisch durch `.agent/workflows`).
Ergänzend kannst du eine `.gemini/settings.json` anlegen (optional):
```json
{
  "agent": {
    "skillDirs": [".agent/skills"],
    "workflowDirs": [".agent/workflows"]
  }
}
```

### Für GitHub Copilot
Erstelle `.github/copilot-instructions.md` und kopiere den Inhalt der `.cursorrules` hinein.

---

## 🔧 SCHRITT 4: .gitignore erweitern

Füge diese Zeilen zur `.gitignore` deines Projekts hinzu:

```gitignore
# RB-Protokoll
.rb_dumps/
*.db
*.sqlite
*.db-journal
.env
client_secrets.json
credentials.json
token.json
*.pem
*.key
```

---

## 🔧 SCHRITT 5: Validierung – Alles korrekt?

Starte eine neue Agent-Session und sage:

```
/bootstrap
```

Der Agent prüft dann automatisch:
- ✅ Alle 7 Skills vorhanden?
- ✅ Alle 7 Workflows vorhanden?
- ✅ `02_SYSTEM_FACTS.md` ohne Platzhalter?
- ✅ `03_ERROR_DB.md` existiert?
- ✅ Python verfügbar?

**Erwartetes Ergebnis:**
```
🔍 RB-Bootstrap Report
═══════════════════════
Skills:     7/7 vorhanden
Workflows:  7/7 vorhanden
Error-DB:   ✅
Sys-Facts:  ✅ (0 Platzhalter)
Python:     ✅ 3.x.x
═══════════════════════
Ergebnis:   BEREIT
```

---

## 📋 REFERENZ: Alle Slash-Commands

| Command | Was passiert | Wann nutzen |
|---|---|---|
| `/bootstrap` | Umgebung prüfen + reparieren | Session-Start, nach Problemen |
| `/check` | Security-Scan + Tests | Vor jedem Commit |
| `/pack` | Context-Dump erzeugen | Debugging, Agent-Wechsel |
| `/flow-close` | UX-Audit (4 Gesetze) | Feature fertig, vor Release |
| `/learn` | Fehler in Error-DB dokumentieren | Nach gelöstem Bug |
| `/sentinelcheck` | ALLES prüfen (Komplett-Audit) | Vor Release, bei Unsicherheit |
| `/content` | Content nach SEO+KI Protokoll | Artikel/Blog/Doku erstellen |

---

## 📋 REFERENZ: Die 7 Skills

### 1. RB Bootstrap (`rb_bootstrap`)
**Zweck:** Prüft ob die RB-Umgebung vollständig ist. Repariert fehlende Dateien.
**Datei:** `.agent/skills/rb_bootstrap/SKILL.md`
**Enthält:** Boot-Sequenz, Verzeichnis-Soll, Selbstheilung, Agent-Arbeitsschleife

### 2. RB Police (`rb_police`)
**Zweck:** Security-Scanner. Findet Secrets, verbotene Dateien, Protokoll-Verstöße.
**Datei:** `.agent/skills/rb_police/SKILL.md`
**Script:** `.agent/skills/rb_police/scripts/pre_commit_police.py`
**Enthält:** Secret-Patterns, Blocked Files, false-positive Filter

### 3. RB Packer (`rb_packer`)
**Zweck:** Erzeugt Context-Dumps für Agent-Kontext oder Debugging.
**Datei:** `.agent/skills/rb_packer/SKILL.md`
**Scripts:** `.agent/skills/rb_packer/scripts/packer.py`, `compare_projects.py`
**Enthält:** Auto-Detection, Custom Includes, Cross-Platform

### 4. UX Guardian (`ux_guardian`)
**Zweck:** Hüter der 5 RB-Gesetze. Prüft UI-Änderungen und Plan-Ausführung.
**Datei:** `.agent/skills/ux_guardian/SKILL.md`
**Resource:** `.agent/skills/ux_guardian/resources/checklist.md`

**Die 5 Gesetze des RB-Protokolls:**

**UX-Gesetze:**
- §1 Transparenz – Keine Hintergrund-Magie ohne Feedback
- §2 Revidierbarkeit – Jede Aktion muss rückgängig machbar sein
- §3 Progressive Offenlegung – Clean UI, Details per Click
- §4 Menschliche Hoheit – KI schlägt vor, Mensch entscheidet

**Agenten-Betriebsmodus:**
- **§5 Plan Execution Autonomy** – Sobald ein Plan finalisiert ist, mit maximaler Autonomie in chronologischer Reihenfolge ausführen. Nur Blocker eskalieren.

### 5. Error Learner (`error_learner`)
**Zweck:** Strukturiertes Erfassen gelöster Fehler in der Error-DB.
**Datei:** `.agent/skills/error_learner/SKILL.md`
**Template:** `.agent/skills/error_learner/templates/error_entry.template.md`
**Enthält:** Duplikat-Check, Kategorien, Validierung

**Error-DB Pfade:**
- **Lokal (projektspezifisch):** `docs/_rb/03_ERROR_DB.md`
- **Zentral (projektübergreifend):** `E:\_____1111____Projekte-Programmierung\Antigravity\03_ERROR_DB.md`
- **Priorität:** Zentrale DB > Lokale DB

### 6. Content Protocol (`content_protocol`) – NEU
**Zweck:** SEO + KI-optimierte Content-Erstellung nach Protokoll.
**Datei:** `.agent/skills/content_protocol/SKILL.md`
**Template:** `.agent/skills/content_protocol/templates/content_checklist.md`
**Enthält:** 5 Phasen (Recherche → Struktur → Technik → Publish → Optimierung), Keyword-Matrix, Schema.org Templates, KPI-Tracking

### 7. Doc Standard (`doc_standard`) – NEU
**Zweck:** Dokumentations-Standard für alle Projekte ("Blueprint-Prinzip").
**Datei:** `.agent/skills/doc_standard/SKILL.md`
**Goldene Regel:** Wenn eine KI nur den `docs/`-Ordner hat, muss sie das Projekt nachbauen können.
**Pflicht-Dateien:** ARCHITECTURE.md, SETUP.md, FEATURES.md, SYSTEM_FACTS, ERROR_DB

---

## 📋 REFERENZ: Zentrale Infrastruktur

| Was | Pfad |
|---|---|
| **Antigravity Root** | `E:\_____1111____Projekte-Programmierung\Antigravity\` |
| **Zentrale Error-DB** | `E:\_____1111____Projekte-Programmierung\Antigravity\03_ERROR_DB.md` |
| **Globale Skills** | `E:\_____1111____Projekte-Programmierung\Antigravity\___________GLOBALE_SKILLS\` |
| **Export-Paket (dieses)** | `E:\_____1111____Projekte-Programmierung\Antigravity\_rb-Protokoll\Export-rb-Protokoll\` |

---

## 🎨 Design System: Sovereign Glass

Das RB-Protokoll wird mit einem modernen UI-Design-System ausgeliefert:

### Farbpalette (Functional Glow)
```
Deep Obsidian (#0A0E14)   ← Hintergrund
Cyber Cyan (#00F2FF)      ← Haupt-Orchestrator (§1 Transparenz)
Sentinel Blue (#1A73E8)   ← Sicherheits-Layer
Action Amber (#FFB000)    ← Bestätigungen (§4 Menschliche Hoheit)
Trace Grey (#4A5568)      ← Logs & Details (§3 Offenlegung)
```

### Layout-Raster (3-Column Grid)
```
┌─────────────────────────────────────────────┐
│ Agent-Orch.   │ Chat-Stream   │ Context-Pane│
├─────────────────────────────────────────────┤
│ Wer arbeitet? │ Konversation  │ Logs/Meta   │
│ Transparenz   │ Fokus         │ Details     │
│ (§1)          │               │ (§3)        │
└─────────────────────────────────────────────┘
```

### Effekte
- **Glassmorphism**: Transparente Panels mit Blur
- **Streaming-Indikatoren**: Pulsing-Lines, RAG-Animation
- **Checkpoint-Cards**: Mit Undo-Buttons (§2 Revidierbarkeit)

👉 **Vollständige Spezifikation:** [DESIGN_SYSTEM_v1.md](docs/DESIGN_SYSTEM_v1.md)

---

## 📦 Context-Dump Prozess

Das RB-Protokoll erstellt automatisch **Projekt-Snapshots** für LLM-Kontext und Debugging:

### Dump erstellen
```bash
cd /pfad/zu/deinem/projekt
PYTHONIOENCODING=utf-8 python .agent/skills/rb_packer/scripts/packer.py
```

### Was passiert
```
📦 LLM Project Packer v3.0
🔍 Auto-detected directories: src, docs, .agent
📄 Found 127 file(s) to pack
✅ Context dump created: PROJECT_DUMP_2026-03-18_11-48.txt (Local: _rb-dump)
✅ Copy sent to: E:\_____1111____Projekte-Programmierung\Antigravity\.rb_dumps
📊 Size: 3773.0 KB
```

### Dump-Verwaltung
- **Lokal**: `_rb-dump/` (nur neuster Dump, alte werden gelöscht)
- **Zentral**: `E:\_____1111____Projekte-Programmierung\Antigravity\.rb_dumps`
  - Automatische Kopie (shutil.copy2)
  - Alte projekt-spezifische Dumps werden gelöscht
  - Nur aktuellster pro Projekt bleibt

### Wann Dump erstellen?
- `✓ Vor längeren LLM-Sessions` (für Context)
- `✓ Nach Major Changes` (für Forensics/Rollback)
- `✓ Bei Bugs` (für Root-Cause-Analysis)
- `✓ Vor Deployment` (Baseline-Snapshot)

### Dump-Inhalt
Enthält automatisch erkannte Verzeichnisse:
- `docs/`, `src/`, `tests/`, `scripts/`
- `.agent/` (alle Skills + Workflows)
- `README.md`, `ARCHITECTURE.md`, etc.

Automatisch **AUSGESCHLOSSEN**:
- `.env`, `.pem`, `.key` (Secrets-Safe)
- `node_modules`, `__pycache__`, `dist/` (zu groß)
- Dateien > 2MB (Performance)

---

## 🔄 §5 Plan Execution Autonomy – Die neue Regel

**Das wichtigste Update in RB-Protokoll v3.1:**

Sobald ein **Plan finalisiert** ist:

✅ **Chronologische Abarbeitung** – Alle Schritte in der definierten Reihenfolge
✅ **Maximale Autonomie** – Nicht bei jedem Schritt nachfragen, proaktiv vorangehen
✅ **Keine unnötigen Pausen** – Automatisch zum nächsten Schritt
✅ **Nur Blocker eskalieren** – Nur wenn es wirklich nicht weitergeht

**Beispiel:**
```
Du: "Plan: Datenbankmigrationen durchführen"
[Agent erstellt und zeigt Plan, du genehmigst]

Agent: ✅ Starte Ausführung (§5 Modus)
       → Backup erstellen (läuft...)
       → Schema-Update (läuft...)
       → Daten migrieren (läuft...)
       → Tests (läuft...)
       → Rollout-Verifizierung (läuft...)
       ✅ FERTIG
```

**Das bedeutet:** Nach Planfreigabe keine Unterbrechungen mehr – nur Resultate!

Siehe auch: `docs/_rb/01_PLAN_EXECUTION.md` in der Hauptinstallation

---

## 🗺️ GSD-Phasen-Logik – Der Agent-Workflow

Das RB-Protokoll v3.1 definiert 5 verpflichtende Phasen für jede Arbeit:

| Phase | Frage | Output |
|---|---|---|
| **MAP** | Was existiert? | `.planning/codebase/architecture.md` |
| **SPEC** | Was wird gebraucht? | `.planning/requirements.md` (PRD) |
| **PLAN** | Wie wird es gebaut? | `.planning/roadmap.md` (atomare Slices) |
| **EXEC** | Bauen. | Code + Git-Commits (1 pro Slice) |
| **VERIFY** | Stimmt das Ergebnis? | VERIFY-Eintrag in `roadmap.md` |

**Stopps:**
- Nach SPEC: Agent wartet auf `/approve`
- Nach PLAN: Agent wartet auf `USER_APPROVE: EXECUTE`
- Nach EXEC des letzten Slice: VERIFY ist Pflicht vor Merge

**SSOT-Regel:** Das Gedächtnis lebt in `.planning/` — nicht im Chat.

Vollständige Spezifikation: `docs/_rb/01_MISSION_PROMPT.md`

---

## ⚡ QUICK-START (TL;DR)

Für Eilige – die 5 Schritte in Kurzform:

```powershell
# 1. Kopieren
$ZIEL = "E:\MeinProjekt"
$QUELLE = "E:\_____1111____Projekte-Programmierung\Antigravity\_rb-Protokoll\Export-rb-Protokoll"
Copy-Item "$QUELLE\.agent" "$ZIEL\.agent" -Recurse -Force
Copy-Item "$QUELLE\docs" "$ZIEL\docs" -Recurse -Force
Copy-Item "$QUELLE\.cursorrules" "$ZIEL\.cursorrules" -Force

# 2. SYSTEM_FACTS ausfüllen (Editor öffnen)
code "$ZIEL\docs\_rb\02_SYSTEM_FACTS.md"

# 3. .gitignore erweitern (manuell oder per echo)

# 4. Agent starten → /bootstrap

# 5. Fertig! Alle Commands verfügbar.
```

---

## 🔄 Updates

Wenn dieses Export-Paket aktualisiert wird:

1. **Neue Skills/Workflows** einfach in `.agent/` dazukopieren
2. **Bestehende überschreiben** mit `-Force` Flag
3. **Niemals** `docs/_rb/` überschreiben → enthält projekt-spezifische Daten!
4. **SYSTEM_FACTS** und **ERROR_DB** sind pro Projekt einzigartig

---

**Version:** 3.2 | **Erstellt:** 2026-03-14 | **Aktualisiert:** 2026-04-02 (GSD-Phasen + vollständige docs/_rb) | **Autor:** Antigravity Core
