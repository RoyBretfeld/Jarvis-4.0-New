---
name: Error Learner
description: Strukturiertes Erfassen neuer Fehler in der Error-DB. Bietet Templates, Validierung und Duplikat-Erkennung für konsistente Einträge.
author: Antigravity Core
version: 3.0.0
triggers:
  - "Learn"
  - "Fehler dokumentieren"
  - "/learn"
---

# Error Learner: Wissen aus Fehlern

> Vereint: `rb.py learn`-Command + Error-DB-Logik + Pointer-Verweis

## 1. Prerequisites

- [ ] Error-DB existiert: `docs/_rb/03_ERROR_DB.md`
- [ ] ODER zentrale DB: Pfad aus `02_SYSTEM_FACTS.md` → Feld "Error DB"
- [ ] Der Fehler ist **gelöst** (wir dokumentieren keine offenen Bugs)

## 2. Instructions

### Schritt 1: Duplikat-Check
1. Öffne die Error-DB (`docs/_rb/03_ERROR_DB.md`)
2. Suche nach ähnlichen Symptomen oder Root Causes
3. Wenn Duplikat gefunden → Bestehenden Eintrag **erweitern**, nicht neu anlegen

### Schritt 2: Eintrag erstellen
Verwende exakt dieses Template:

```markdown
---

### ERR-YYYYMMDD-KURZBESCHREIBUNG

| Feld | Wert |
|---|---|
| **ID** | ERR-YYYYMMDD-KURZBESCHREIBUNG |
| **Datum** | YYYY-MM-DD |
| **Schwere** | 🔴 KRITISCH / 🟡 MITTEL / 🟢 NIEDRIG |
| **Symptom** | Was ging schief? (User-Perspektive) |
| **Root Cause** | Warum ging es schief? (Technische Ursache) |
| **Fix** | Was wurde gemacht? (Code/Config-Änderung) |
| **Dateien** | Welche Dateien waren betroffen? |
| **Regression-Test** | Wie kann man den Fix verifizieren? |
| **Prevention Rule** | Neue Guardrail um Wiederholung zu verhindern? |
```

### Schritt 3: Kategorisierung
Ordne den Eintrag einer Kategorie zu:
- `## 🔧 Config & Environment` – Pfade, Versionen, Abhängigkeiten
- `## 🐛 Code Bugs` – Logik-Fehler, Typos, Edge-Cases
- `## 🔒 Security` – Secrets, Permissions, Injections
- `## 🎨 UI/UX` – Layout, Usability, Accessibility
- `## 📦 Build & Deploy` – Compiler, Bundler, CI/CD
- `## 🌐 Integration` – APIs, Datenbanken, externe Dienste

### Schritt 4: Validierung
- [ ] ID ist einzigartig (keine Duplikate)
- [ ] Alle Felder ausgefüllt (keine leeren Werte)
- [ ] Prevention Rule ist konkret und umsetzbar
- [ ] Regression-Test ist ausführbar

## 3. Error-DB Pfad-Auflösung

Die Error-DB kann an zwei Orten liegen:

1. **Lokal:** `docs/_rb/03_ERROR_DB.md` (projektspezifisch)
2. **Zentral:** Pfad aus `02_SYSTEM_FACTS.md` (projektübergreifend)

**Priorität:** Zentrale DB > Lokale DB. Wenn beide existieren:
- Schreibe in die **zentrale** DB
- Ergänze einen Verweis in der lokalen DB

## 4. Lern-Trigger

Dieser Skill wird automatisch relevant wenn:
- Ein neuer Bug gefixt wurde
- Ein Workaround implementiert wurde
- Ein Pattern entdeckt wurde, das zu Fehlern führt
- Die gleiche Art von Fehler zum zweiten Mal auftritt (→ Prevention Rule!)

## 5. Constraints

- **NIEMALS** offene/ungelöste Bugs dokumentieren (nur gelöste)
- **NIEMALS** Einträge löschen (Wissen ist kumulativ)
- **IMMER** Prevention Rule angeben (was lernen wir daraus?)
- **IMMER** Duplikat-Check vor neuem Eintrag
