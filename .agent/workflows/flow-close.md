---
description: Flow-Integrität prüfen – Navigation + UX-Audit gegen die 4 Gesetze
---

# /flow-close – Flow sauber abschließen

Dieser Workflow stellt sicher, dass ein Feature-Flow mit voller Integrität abgeschlossen wird.
**Nie** einen Flow beenden, ohne diesen Check durchlaufen zu haben.

## Schritte

1. **Navigations-Check:**
   - Ist die aktuelle Änderung vom Root (Startseite/Hauptmenü) aus erreichbar?
   - Gibt es einen klaren Rückweg zum Root?
   - Keine "Dead Ends" im UI

2. **UX Guardian laden:**
   Lies `.agent/skills/ux_guardian/SKILL.md` und führe den vollständigen Audit durch.

3. **4-Gesetze-Audit durchführen:**
   Prüfe die letzten Änderungen gegen:

   | Gesetz | Frage | Status |
   |---|---|---|
   | §1 Transparenz | Sieht der User was passiert? | ✅/❌ |
   | §2 Revidierbarkeit | Kann der User es rückgängig machen? | ✅/❌ |
   | §3 Offenlegung | Ist die UI clean, Details per Click? | ✅/❌ |
   | §4 Menschl. Hoheit | Entscheidet der Mensch? | ✅/❌ |

4. **Security-Quick-Check:**
   - Keine neuen Secrets im Code?
   - Keine neuen `.env`-Dateien committed?

5. **Audit-Report ausgeben:**
   Verwende das Format aus dem UX Guardian Skill (Box-Report).

6. **Entscheidung:**
   - **GRÜN:** Flow darf geschlossen werden → Bestätigung an User
   - **GELB:** Warnungen → Empfehlungen aussprechen, User entscheidet
   - **ROT:** Verstöße → Flow DARF NICHT geschlossen werden, Fixes zuerst
