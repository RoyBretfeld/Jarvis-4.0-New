# UX Guardian – Schnell-Checkliste

> Ausdrucken, an den Monitor kleben, bei jedem UI-Change durchgehen.

## ✅ Quick-Check (30 Sekunden)

| # | Gesetz | Frage | ✅/❌ |
|---|---|---|---|
| 1 | Transparenz | Sieht der User, was passiert? | |
| 2 | Revidierbarkeit | Kann der User es rückgängig machen? | |
| 3 | Offenlegung | Ist die Oberfläche clean? | |
| 4 | Menschl. Hoheit | Entscheidet der Mensch? | |

## 🔍 Detail-Check (bei kritischen Änderungen)

### §1 Transparenz
- [ ] Ladebalken bei Prozessen >500ms
- [ ] Fehler werden dem User gezeigt (nicht verschluckt)
- [ ] Fortschrittsanzeige bei mehrstufigen Operationen
- [ ] Status-Indikator (online/offline, verbunden/getrennt)

### §2 Revidierbarkeit
- [ ] Soft Delete statt Hard Delete
- [ ] Undo-Button oder Bestätigungsdialog
- [ ] `_archive/` oder `_trash/` Ordner
- [ ] Versionierung (Git) aktiv

### §3 Progressive Offenlegung
- [ ] Default-View zeigt nur Essentielles
- [ ] Details per Expand/Hover/Klick
- [ ] Keine 50-Felder-Formulare
- [ ] Debug-Info versteckt (nicht im UI)

### §4 Menschliche Hoheit
- [ ] KI schlägt vor, Mensch bestätigt
- [ ] Kein Auto-Deploy / Auto-Delete
- [ ] God-Mode nur per Opt-In
- [ ] Audit-Trail bei kritischen Aktionen
