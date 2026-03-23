---
description: Neuen Fehler strukturiert in der Error-DB dokumentieren
---

# /learn – Fehler dokumentieren

Dieser Workflow führt durch das strukturierte Erfassen eines gelösten Fehlers.

## Schritte

1. **Error Learner Skill laden:**
   Lies `.agent/skills/error_learner/SKILL.md` für Template und Regeln.

2. **Duplikat-Check:**
   - Öffne `docs/_rb/03_ERROR_DB.md`
   - Suche nach ähnlichen Symptomen oder Root Causes
   - Bei Duplikat: Bestehenden Eintrag erweitern statt neu anlegen

3. **Daten sammeln:**
   Frage den User nach (soweit nicht schon bekannt):
   - **Symptom:** Was ging schief?
   - **Root Cause:** Warum?
   - **Fix:** Was wurde gemacht?
   - **Betroffene Dateien:** Welche?

4. **Eintrag erstellen:**
   Verwende das Template aus `.agent/skills/error_learner/templates/error_entry.template.md`:
   - ID: `ERR-YYYYMMDD-KURZBESCHREIBUNG`
   - Alle Felder ausfüllen
   - Prevention Rule formulieren (das Wichtigste!)

5. **Eintrag einfügen:**
   Füge den neuen Eintrag in die passende Kategorie der Error-DB ein.

6. **Validierung:**
   - [ ] ID ist einzigartig
   - [ ] Alle Felder ausgefüllt
   - [ ] Prevention Rule ist konkret
   - [ ] Regression-Test ist ausführbar

7. **Bestätigung:**
   Zeige dem User den fertigen Eintrag und frage nach Freigabe (§4 Menschliche Hoheit).
