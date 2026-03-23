---
description: RB-Umgebung prüfen, validieren und bei Bedarf reparieren
---

# /bootstrap – Umgebungsprüfung & Selbstheilung

Dieser Workflow prüft ob die RB-Protokoll-Umgebung vollständig und funktionsfähig ist.

## Schritte

1. **Skill-Instruktionen laden:**
   Lies `.agent/skills/rb_bootstrap/SKILL.md` für die vollständige Prüfliste.

2. **Verzeichnisstruktur prüfen:**
   Folgende Pfade müssen existieren:
   - `.agent/skills/rb_bootstrap/SKILL.md`
   - `.agent/skills/rb_police/SKILL.md`
   - `.agent/skills/rb_packer/SKILL.md`
   - `.agent/skills/ux_guardian/SKILL.md`
   - `.agent/skills/error_learner/SKILL.md`
   - `.agent/workflows/check.md`
   - `.agent/workflows/bootstrap.md`
   - `.agent/workflows/pack.md`
   - `.agent/workflows/flow-close.md`
   - `.agent/workflows/learn.md`
   - `docs/_rb/02_SYSTEM_FACTS.md`
   - `docs/_rb/03_ERROR_DB.md`

3. **Pflichtdateien validieren:**
   - Prüfe `docs/_rb/02_SYSTEM_FACTS.md` auf `{{PLACEHOLDER}}`-Reste
   - Melde unfilled Placeholders mit konkreten Vorschlägen

4. **Python-Umgebung testen:**
   // turbo
   ```powershell
   python --version
   ```

5. **Status-Report ausgeben:**
   ```
   🔍 RB-Bootstrap Report
   ═══════════════════════
   Skills:     X/5 vorhanden
   Workflows:  X/6 vorhanden
   Error-DB:   ✅/❌
   Sys-Facts:  ✅/⚠️ (X Platzhalter)
   Python:     ✅ 3.x.x
   ═══════════════════════
   Ergebnis:   BEREIT / REPARATUR NÖTIG
   ```

6. **Bei Fehlern:**
   Wenn Dateien fehlen → Frage den User ob sie wiederhergestellt werden sollen (§4 Menschliche Hoheit).
