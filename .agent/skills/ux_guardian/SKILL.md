---
name: UX Guardian
description: Aktiver Hüter der 4 UX-Gesetze. Prüft UI-Änderungen gegen Transparenz, Revidierbarkeit, Progressive Offenlegung und Menschliche Hoheit. Pflicht bei /flow-close.
author: Antigravity Core
version: 3.0.0
triggers:
  - "Flow schließen"
  - "UX prüfen"
  - "UX Audit"
---

# UX Guardian: Die 4 Gesetze

> Vereint: `04_UX_LAWS.md` + `04_STANDARDS.md` (Duplikat aufgelöst)

## 1. Prerequisites

- [ ] UI-Änderung wurde durchgeführt (oder steht bevor)
- [ ] Zugriff auf die geänderten Dateien
- [ ] `resources/checklist.md` gelesen

## 2. Die 4 Gesetze (Core)

### §1. TRANSPARENZ (Glass-Box Principle)
> *Keine Hintergrund-Magie ohne Feedback.*

**Pflicht-Prüfung:**
- [ ] Haben lange Prozesse (>500ms) einen Ladebalken oder Log-Output?
- [ ] Sieht der User jederzeit, DASS das System arbeitet?
- [ ] Sieht der User jederzeit, WAS das System tut?
- [ ] Gibt es Fehlermeldungen für alle Fehlerfälle (nicht nur stille Fails)?

**Verstöße melden als:** `⚠️ §1 TRANSPARENZ: [Beschreibung des Verstoßes]`

### §2. REVIDIERBARKEIT (Undo is King)
> *Fehler müssen verzeihbar sein.*

**Pflicht-Prüfung:**
- [ ] "Löschen" → bedeutet es IMMER "in den Papierkorb" (Soft Delete)?
- [ ] Haben Verschiebungen eine Undo-Option?
- [ ] Haben kritische Änderungen eine Bestätigungsdialog?
- [ ] Gibt es ein `_archive/` oder `_trash/` Fallback?

**Verstöße melden als:** `⚠️ §2 REVIDIERBARKEIT: [Beschreibung des Verstoßes]`

### §3. PROGRESSIVE OFFENLEGUNG (No Clutter)
> *Zeige Informationen nur, wenn sie relevant sind.*

**Pflicht-Prüfung:**
- [ ] Ist die Default-View clean und aufgeräumt?
- [ ] Werden Details erst bei Hover/Klick sichtbar?
- [ ] Wird der User NICHT mit Informationen überflutet?
- [ ] Sind Debug-Infos, Metadaten und Logs hinter einem Expand?

**Verstöße melden als:** `⚠️ §3 PROGRESSIVE OFFENLEGUNG: [Beschreibung des Verstoßes]`

### §4. MENSCHLICHE HOHEIT (Human-in-the-Loop)
> *Die KI ist der Antragsteller, der Mensch der Richter.*

**Pflicht-Prüfung:**
- [ ] Schlägt die KI nur vor, bestätigt der Mensch?
- [ ] Sind kritische Aktionen NICHT vollautomatisiert?
- [ ] Gibt es ein explizites Opt-In für "God-Mode" Automatisierungen?
- [ ] Wird bei Deployment/Löschen IMMER nachgefragt?

**Verstöße melden als:** `⚠️ §4 MENSCHLICHE HOHEIT: [Beschreibung des Verstoßes]`

## 3. Code-Standards (Bonus-Check)

- [ ] **Kleine PRs:** Diffs überschaubar halten
- [ ] **Modularität:** Logik (Backend) strikt getrennt von Darstellung (UI)
- [ ] **Naming:** Sprechende Variablennamen
  - Code: Englisch bevorzugt
  - UI: Deutsch
- [ ] **Keine Secrets:** Niemals Passwörter oder Keys loggen
- [ ] **Debug-fähig:** Logs haben Timestamps und Modul-Namen

## 4. Audit-Protokoll

Wenn der UX Guardian aufgerufen wird, erstelle folgenden Report:

```
╔══════════════════════════════════════╗
║       UX GUARDIAN AUDIT REPORT       ║
╠══════════════════════════════════════╣
║ §1 Transparenz:      ✅ / ⚠️ / ❌   ║
║ §2 Revidierbarkeit:  ✅ / ⚠️ / ❌   ║
║ §3 Offenlegung:      ✅ / ⚠️ / ❌   ║
║ §4 Menschl. Hoheit:  ✅ / ⚠️ / ❌   ║
╠══════════════════════════════════════╣
║ Code-Standards:      ✅ / ⚠️ / ❌   ║
╠══════════════════════════════════════╣
║ ERGEBNIS: GRÜN / GELB / ROT         ║
╚══════════════════════════════════════╝
```

- **GRÜN:** Alle Gesetze eingehalten → Flow darf geschlossen werden
- **GELB:** Warnungen vorhanden → Fixes empfohlen, kein Block
- **ROT:** Verstöße gefunden → Flow DARF NICHT geschlossen werden

## 5. Constraints

- **NIEMALS** einen Flow schließen, wenn §2 (Revidierbarkeit) verletzt ist
- **NIEMALS** §4 überstimmen – die Menschliche Hoheit ist unantastbar
- **IMMER** den vollständigen Audit-Report ausgeben, nie nur "sieht gut aus"
