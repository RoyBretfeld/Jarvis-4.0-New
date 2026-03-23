# 📖 RB-Protokoll v3.0 – Benutzerhandbuch

> Anleitung für die Verwendung des Skills-nativen RB-Protokolls

---

## Schnellstart (30 Sekunden)

Du brauchst nur **3 Dinge** zu wissen:

| Was du willst | Was du tippst | Was passiert |
|---|---|---|
| Code vor Commit prüfen | `/check` | Police scannt, Tests laufen |
| Umgebung reparieren | `/bootstrap` | Prüft Struktur, heilt fehlende Dateien |
| Fehler dokumentieren | `/learn` | Geführter Error-DB-Eintrag |
| Feature abschließen | `/flow-close` | UX-Audit gegen die 4 Gesetze |
| Debug-Dump erstellen | `/pack` | Context-Dump in `.rb_dumps/` |

**Das war's.** Alles andere passiert automatisch.

---

## Wie funktioniert das?

### Das Skill-System

Jeder Skill ist ein **Ordner** unter `.agent/skills/` mit einer `SKILL.md`-Datei.
Der Agent (Gemini, Copilot, etc.) erkennt diese Datei automatisch und kann:

1. **Finden:** Die YAML-Metadaten im Frontmatter beschreiben den Skill
2. **Lesen:** Die Markdown-Instruktionen erklären was zu tun ist
3. **Ausführen:** Die eingebetteten Skripte werden bei Bedarf gestartet

```
.agent/skills/rb_police/
├── SKILL.md                    ← Agent liest das
└── scripts/
    └── pre_commit_police.py    ← Agent führt das aus
```

### Das Workflow-System

Workflows sind `.md`-Dateien unter `.agent/workflows/` die als **Slash-Commands** fungieren.
Jeder Workflow beschreibt eine Schritt-für-Schritt-Anleitung die der Agent autonom abarbeitet.

```yaml
# .agent/workflows/check.md
---
description: Pre-Commit Gate – Police + Baseline Tests
---
1. Error-DB prüfen
2. Police ausführen
3. Baseline-Tests laufen lassen
4. Ergebnis melden
```

**Turbo-Modus:** Wenn `// turbo-all` im Workflow steht, führt der Agent alle
Terminal-Commands automatisch aus, ohne jedes Mal nachzufragen.

---

## §5 Plan Execution Autonomy

**Wenn ein Plan finalisiert ist:**

Der Agent arbeitet mit **maximaler Autonomie** – nicht bei jedem Schritt nachfragen, sondern proaktiv vorangehen:

1. **Strikte Reihenfolge** – Alle Schritte in der definierten Reihenfolge
2. **Ohne Pausen** – Automatisch weiter zum nächsten Schritt
3. **Eigenständige Entscheidungen** – Bei erwarteten Szenarien selbst handeln
4. **Nur Blocker eskalieren** – Nur wenn es wirklich nicht weitergeht

**Beispiel:**
```
Du: "/plan: Datenbankmigrationen durchführen"
[Agent genehmigt Plan]

Agent: ✅ Starte Ausführung (§5 Modus)
       → Backup erstellen
       → Schema-Update
       → Daten migrieren
       → Tests
       → Rollout-Verifizierung
       ✅ Alle Schritte abgeschlossen!
```

👉 **Siehe auch:** [docs/_rb/01_PLAN_EXECUTION.md](../_rb/01_PLAN_EXECUTION.md)

---

## Detaillierte Workflow-Beschreibungen

### `/check` – Pre-Commit Gate
**Wann:** Vor jedem Commit oder wenn du unsicher bist ob der Code sauber ist.

```
Du: /check
Agent: 🚓 Running pre-commit checks...
       ✅ Error DB found
       ✅ Police: No violations
       ✅ All checks passed! (4 Laws Compliant)
```

### `/bootstrap` – Umgebungsprüfung
**Wann:** Bei Session-Start, nach Problemen, oder wenn etwas "kaputt" wirkt.

```
Du: /bootstrap
Agent: 🔍 RB-Bootstrap Report
       ═══════════════════════
       Skills:     5/5 vorhanden
       Workflows:  6/6 vorhanden
       Error-DB:   ✅
       Sys-Facts:  ⚠️ 3 Platzhalter
       ═══════════════════════
       Ergebnis:   BEREIT (mit Hinweisen)
```

### `/flow-close` – Feature abschließen
**Wann:** Wenn ein Feature fertig ist und du den Flow sauber beenden willst.

```
Du: /flow-close
Agent: ╔══════════════════════════════════════╗
       ║       UX GUARDIAN AUDIT REPORT       ║
       ╠══════════════════════════════════════╣
       ║ §1 Transparenz:      ✅              ║
       ║ §2 Revidierbarkeit:  ✅              ║
       ║ §3 Offenlegung:      ⚠️ Detail-View  ║
       ║ §4 Menschl. Hoheit:  ✅              ║
       ╠══════════════════════════════════════╣
       ║ ERGEBNIS: GELB                       ║
       ╚══════════════════════════════════════╝
       Empfehlung: Detail-View noch hinter Expand packen.
```

### `/learn` – Fehler dokumentieren
**Wann:** Nachdem du einen Bug gefixt hast – damit er nie wieder vorkommt.

```
Du: /learn
Agent: 📝 Duplikat-Check... kein ähnlicher Eintrag gefunden.
       Bitte beschreibe:
       - Symptom?
       - Root Cause?
       - Fix?
Du: Login ging nicht weil die DB-Connection falsch war...
Agent: ✅ Eintrag ERR-20260219-DB-CONNECTION erstellt.
```

### `/pack` – Context-Dump
**Wann:** Wenn du einen Dump für Debugging oder Agent-Kontext brauchst.

```
Du: /pack
Agent: 📦 RB-Framework Packer v3.0
       🔍 Auto-detected: docs, scripts, src, .agent
       📄 Found 127 files
       ✅ Context dump created: PROJECT_DUMP_2026-03-18_11-48.txt (Local: _rb-dump)
       ✅ Copy sent to: E:\_____1111____Projekte-Programmierung\Antigravity\.rb_dumps
       📊 Size: 3773.0 KB
```

**Was passiert automatisch:**
- 📁 Lokal: `_rb-dump/` (nur neuster, alte werden gelöscht)
- 🌐 Zentral: `E:\_____1111____Projekte-Programmierung\Antigravity\.rb_dumps` (Kopie für alle Projekte)
- 🔒 Secrets-Safe: `.env`, `.pem`, `.key` werden ausgeschlossen
- 📦 Intelligente Auto-Detection: `src/`, `docs/`, `.agent/`, etc.

---

## Wie binde ich das in ein neues Projekt ein?

### Option A: Einfaches Kopieren

1. Kopiere den `.agent/`-Ordner in dein neues Projekt
2. Erstelle `docs/_rb/02_SYSTEM_FACTS.md` (projektspezifisch befüllen)
3. Erstelle `docs/_rb/03_ERROR_DB.md` (leer starten)
4. Fertig. Die Slash-Commands funktionieren sofort.

### Option B: Symlink (alle Projekte teilen dieselben Skills)

```powershell
# Einmalig einen Symlink setzen
$GLOBAL_SKILLS = "E:\_____1111____Projekte-Programmierung\Antigravity\_rb-Protokoll\.agent\skills"
$MEIN_PROJEKT  = "C:\path\zu\mein-projekt\.agent\skills"

New-Item -ItemType SymbolicLink -Path $MEIN_PROJEKT -Target $GLOBAL_SKILLS
```

**Vorteil:** Wenn du einen Skill updatest, profitieren alle Projekte.

---

## Architektur-Diagramm

```
┌─────────────────────────────────────────────┐
│                  USER                        │
│         "Police" / "/check" / "Pack"         │
└────────────────────┬────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────┐
│              AGENT (Gemini/Copilot)          │
│                                              │
│  1. Erkennt Trigger                          │
│  2. Sucht passenden Skill/Workflow           │
│  3. Liest SKILL.md Instruktionen             │
│  4. Führt eingebettete Scripts aus           │
│  5. Reportet Ergebnis                        │
└────────────────────┬────────────────────────┘
                     │
          ┌──────────┼──────────┐
          ▼          ▼          ▼
   ┌──────────┐ ┌────────┐ ┌────────┐
   │ Skills/  │ │ docs/  │ │Scripts │
   │ SKILL.md │ │ _rb/   │ │ .py    │
   └──────────┘ └────────┘ └────────┘
```

---

## FAQ

**Q: Muss ich die Python-Skripte manuell ausführen?**
A: Nein. Der Agent tut das automatisch wenn du `/check` oder `/pack` sagst.

**Q: Kann ich eigene Skills hinzufügen?**
A: Ja! Erstelle einen neuen Ordner unter `.agent/skills/` mit einer `SKILL.md`.
   Folge dem Everlast-Standard (3 Layers: Hook, Logic, Assets).

**Q: Was passiert wenn ein Skill fehlt?**
A: `/bootstrap` erkennt das und bietet Reparatur an.

**Q: Funktioniert das auch mit anderen Agents?**
A: Ja, solange der Agent das `.agent/skills/`-Format unterstützt
   (Gemini Code Assist, GitHub Copilot Workspace, Cursor).
