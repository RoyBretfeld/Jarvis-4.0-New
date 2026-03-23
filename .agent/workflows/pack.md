---
description: Context-Dump für Agent-Kontext oder Debugging erzeugen
---

# /pack – Context-Dump Generator

Dieser Workflow erzeugt einen strukturierten Dump des Projekts.

## Schritte

// turbo-all

1. **Skill-Instruktionen laden:**
   Lies `.agent/skills/rb_packer/SKILL.md` für Details zur Auto-Detection.

2. **Packer ausführen:**
   ```powershell
   python .agent/skills/rb_packer/scripts/packer.py
   ```

3. **Ergebnis verifizieren:**
   - Prüfe ob Dump in `.rb_dumps/` erstellt wurde
   - Melde Dateigröße und Anzahl inkludierter Dateien

4. **Optional – Custom Includes:**
   Falls der User bestimmte Verzeichnisse will:
   ```powershell
   $env:RB_PACK_INCLUDE = "backend,frontend,docs"
   python .agent/skills/rb_packer/scripts/packer.py
   ```
