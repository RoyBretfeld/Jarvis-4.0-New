---
name: RB Bootstrap
description: Prüft und repariert die RB-Protokoll-Umgebung. Verifiziert Verzeichnisstruktur, Pflichtdateien und Konfiguration. Autonome Selbstheilung bei fehlenden Dateien.
author: Antigravity Core
version: 3.0.0
triggers:
  - "Bootstrap jetzt"
  - "/bootstrap"
---

# RB Bootstrap: Umgebungsprüfung & Selbstheilung

> Vereint: `00_BOOT_PROTOCOL.md` + `01_AGENT_LOOP.md` + `BOOTSTRAP_PROMPT.md` + `installer.py`

## 1. Prerequisites

- [ ] Python 3.12+ verfügbar
- [ ] Workspace-Root ist `_rb-Protokoll/`
- [ ] Git initialisiert (für Rollback-Sicherheit)

## 2. Boot-Sequenz (MANDATORY bei Session-Start)

**Vor jeder anderen Aktion in einer neuen Session:**

1. **SYSTEM_FACTS lesen:** `docs/_rb/02_SYSTEM_FACTS.md` → Projektkontext laden
2. **ERROR_DB scannen:** `docs/_rb/03_ERROR_DB.md` → Bekannte Fallen prüfen
3. **Skills validieren:** Prüfe ob alle 5 Core-Skills vorhanden sind
4. **Umgebung prüfen:** Verzeichnisstruktur gegen Soll abgleichen

> ⚠️ **Dies ist NICHT optional. Failure to follow → wiederholte Bugs, verlorener Kontext.**

## 3. Verzeichnis-Soll (Struktur-Validator)

Folgende Pfade MÜSSEN existieren:

```
_rb-Protokoll/
├── .agent/skills/rb_bootstrap/SKILL.md
├── .agent/skills/rb_police/SKILL.md
├── .agent/skills/rb_packer/SKILL.md
├── .agent/skills/ux_guardian/SKILL.md
├── .agent/skills/error_learner/SKILL.md
├── .agent/workflows/check.md
├── .agent/workflows/bootstrap.md
├── .agent/workflows/pack.md
├── .agent/workflows/flow-close.md
├── .agent/workflows/learn.md
├── docs/_rb/02_SYSTEM_FACTS.md
└── docs/_rb/03_ERROR_DB.md
```

## 4. Selbstheilung (Auto-Repair)

Wenn eine Pflichtdatei fehlt:

1. **Warnung ausgeben:** `⚠️ MISSING: <Pfad>`
2. **Template bereitstellen:** Aus `templates/` Ordner dieses Skills
3. **User fragen:** Soll die Datei wiederhergestellt werden? (§4 Menschliche Hoheit)
4. **Erstellen + Loggen:** Datei anlegen und in ERROR_DB dokumentieren

## 5. Agent-Arbeitsschleife (Loop)

Nach dem Boot folgt bei jeder Aufgabe dieser Zyklus:

```
1. Task verstehen    → Ziel + Scope + Nicht-Ziele
2. Status quo prüfen → /check (Police + Tests)
3. Error-DB scannen  → Ähnliche Symptome? Bekannte Fallen?
4. Minimal ändern    → Kleiner Patch, nicht alles umschreiben
5. Wieder prüfen     → /check
6. Tests laufen      → Trigger-Tests wenn betroffen
7. Ergebnis belegen  → Screenshot / Log / Test-Output
8. Bei neuem Fehler  → /learn (Error-DB Eintrag)
9. Abschluss         → Diff-Summary + Test-Nachweis
```

## 6. Mission & Guardrails

### Mission
Wir bauen Software, die **minimal**, **prüfbar** und **mensch-zentriert** ist.

### Definition of Done (DoD)
Ein Task gilt erst als fertig, wenn:
- [ ] `/check` ist Grün (Police + Baseline)
- [ ] Die 4 UX-Gesetze eingehalten (siehe `ux_guardian` Skill)
- [ ] Keine destruktive Funktion ohne Undo/Trash-Fallback
- [ ] Bei neuen Fehlern: Error-DB Eintrag via `/learn`

### Guardrails
1. **No Secrets:** Keine Passwörter, Tokens, Keys im Repo, Logs oder Dumps
2. **Safety:** Keine destruktiven Commands ohne explizite User-Freigabe
3. **Daten-Souveränität:** Lokale Daten bleiben lokal
4. **Concept First:** Code erst nach verstandenem Konzept

## 7. Constraints

- **NIEMALS** Boot-Sequenz überspringen
- **NIEMALS** Dateien löschen ohne `_archive/` Backup
- **NIEMALS** Platzhalter in produktivem Code lassen
- **IMMER** erst Plan (Artifact), dann Code
