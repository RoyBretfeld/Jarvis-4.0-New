---
name: Project Documentation Standard
description: >
  Definiert den Dokumentations-Standard für alle Projekte.
  Kernregel: Die Dokumentation muss so vollständig sein, dass eine KI
  das Projekt allein daraus nachbauen kann.
author: Antigravity Core
version: 1.0.0
---

# 📚 Dokumentations-Standard: "Blueprint-Prinzip"

> **Goldene Regel:** Wenn eine KI nur den `docs/`-Ordner hat und sonst nichts –
> muss sie das gesamte Projekt davon nachbauen können.

## 1. Pflicht-Dateien in `docs/`

Jedes Projekt MUSS mindestens diese Dateien in `docs/` haben:

### `docs/ARCHITECTURE.md` – Wie ist das Projekt aufgebaut?
- Tech-Stack (Sprache, Framework, Version)
- Projektstruktur (Verzeichnisbaum mit Erklärungen)
- Datenfluss (was geht wo hin?)
- Externe Abhängigkeiten (APIs, DBs, Services)

### `docs/SETUP.md` – Wie bekomme ich es zum Laufen?
- Voraussetzungen (Node, Python, etc.)
- Installation Schritt für Schritt
- Environment-Variablen (Namen + Beschreibung, KEINE Werte!)
- Erster Start-Befehl

### `docs/FEATURES.md` – Was kann das Projekt?
- Feature-Liste mit Kurzbeschreibung
- Was ist fertig, was ist geplant?
- User-Stories oder Use-Cases

### `docs/_rb/02_SYSTEM_FACTS.md` – Projektspezifischer Kontext
- Wie im RB-Protokoll definiert
- Kritische Befehle, wichtige Pfade
- Sicherheitsregeln

### `docs/_rb/03_ERROR_DB.md` – Gelerntes Fehlerwissen
- Gelöste Bugs mit Root Cause + Fix
- Prevention Rules

## 2. Optionale Dateien (je nach Projektgröße)

| Datei | Wann nötig |
|---|---|
| `docs/API.md` | Wenn APIs vorhanden |
| `docs/DATABASE.md` | Wenn DB-Schema existiert |
| `docs/DEPLOYMENT.md` | Wenn Deployment-Pipeline existiert |
| `docs/DESIGN.md` | Wenn UI/UX-Entscheidungen dokumentiert werden |
| `docs/CHANGELOG.md` | Ab Version 2.0+ |

## 3. Der "KI-Nachbau-Test"

So prüfst du ob die Doku ausreicht:

**Stell dir vor, du gibst einer KI nur den `docs/`-Ordner. Kann sie:**
- [ ] Die richtige Sprache/Framework wählen?
- [ ] Die Verzeichnisstruktur anlegen?
- [ ] Die Kernlogik implementieren?
- [ ] Die Datenbank aufsetzen?
- [ ] Das Projekt starten?
- [ ] Die bekannten Fehler vermeiden?

Wenn ein Punkt mit ❌ beantwortet wird → Dokumentation ergänzen.

## 4. Anti-Patterns (was NICHT in docs/ gehört)

- ❌ **Keine Secrets** – Keine API-Keys, Passwörter, Tokens
- ❌ **Keine generierten Dateien** – Keine Build-Outputs, Coverage-Reports
- ❌ **Keine Duplikate** – Nicht das selbe in 3 verschiedenen Dateien
- ❌ **Kein Roman** – Prägnant, strukturiert, mit Code-Beispielen

## 5. Template für neue Projekte

Wenn ein neues Projekt angelegt wird, erstelle sofort:

```
docs/
├── ARCHITECTURE.md    # Tech-Stack + Struktur
├── SETUP.md           # Installation + Start
├── FEATURES.md        # Was kann es?
└── _rb/
    ├── 02_SYSTEM_FACTS.md   # Projektkontext
    └── 03_ERROR_DB.md       # Leere DB (wächst)
```

## 6. Constraints

- **IMMER** Deutsch für Beschreibungen, Englisch für Code-Beispiele
- **IMMER** aktualisieren wenn sich die Architektur ändert
- **NIEMALS** "wird später gemacht" – Doku ist Teil der Definition of Done
