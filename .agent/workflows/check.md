---
description: Pre-Commit Gate – Police + Baseline Tests + Error-DB Validierung
---

# /check – Sicherheits- und Qualitätsprüfung

Dieser Workflow führt alle Pre-Commit-Checks durch.

## Schritte

// turbo-all

1. **Error-DB Existenz prüfen:**
   Stelle sicher, dass `docs/_rb/03_ERROR_DB.md` existiert.
   Ohne Error-DB ist §1 (Transparenz) und §2 (Revidierbarkeit) nicht erfüllt.

2. **Police ausführen:**
   ```powershell
   python .agent/skills/rb_police/scripts/pre_commit_police.py
   ```
   Interpretiere das Ergebnis:
   - `✅ Scan complete` → Weiter zu Schritt 3
   - `⚠️` oder `❌` → Stopp, Findings dem User melden

3. **Baseline-Tests (wenn konfiguriert):**
   Prüfe `docs/_rb/02_SYSTEM_FACTS.md` auf einen konfigurierten Test-Command.
   Wenn vorhanden: Ausführen. Wenn Platzhalter: Überspringen mit Info.

4. **Ergebnis melden:**
   - Alles grün → `✅ All checks passed! (4 Laws Compliant)`
   - Fehler → Detaillierte Auflistung der Findings
