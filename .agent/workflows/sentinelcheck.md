---
description: THE SENTINEL – Komplett-Prüfung aller Systeme
---

# /sentinelcheck – Vollständiger System-Audit

Dieser Workflow kombiniert ALLE anderen Checks zu einem einzigen, umfassenden Audit.
Verwende ihn wenn du sichergehen willst, dass wirklich ALLES in Ordnung ist.

## Schritte

1. **Bootstrap prüfen:**
   Führe den `/bootstrap`-Workflow aus (lies `.agent/workflows/bootstrap.md`).
   Alle Skills und Workflows müssen vorhanden sein.

2. **Police ausführen:**
   Führe den `/check`-Workflow aus (lies `.agent/workflows/check.md`).
   Security-Scan + Baseline-Tests.

3. **UX-Audit:**
   Lies `.agent/skills/ux_guardian/SKILL.md` und prüfe gegen die 4 Gesetze.
   Erstelle den vollständigen Audit-Report.

4. **Error-DB Integrität:**
   - Prüfe ob `docs/_rb/03_ERROR_DB.md` existiert und lesbar ist
   - Prüfe ob Einträge dem Template-Format entsprechen
   - Melde inkonsistente oder unvollständige Einträge

5. **SYSTEM_FACTS Validierung:**
   - Prüfe `docs/_rb/02_SYSTEM_FACTS.md` auf `{{PLACEHOLDER}}`-Reste
   - Melde alle unfilled Placeholders

6. **Sentinel-Report ausgeben:**
   ```
   ╔══════════════════════════════════════╗
   ║         SENTINEL FULL REPORT         ║
   ╠══════════════════════════════════════╣
   ║ Bootstrap:   ✅ 5/5 Skills, 6/6 WFs ║
   ║ Police:      ✅ No violations        ║
   ║ UX Guardian: ✅ / ⚠️ / ❌            ║
   ║ Error-DB:    ✅ X Einträge, valid    ║
   ║ Sys-Facts:   ✅ / ⚠️ X Platzhalter   ║
   ╠══════════════════════════════════════╣
   ║ GESAMTSTATUS: GRÜN / GELB / ROT     ║
   ╚══════════════════════════════════════╝
   ```
