# 00_BOOT_PROTOCOL (RB)

## Zweck

Dieses Dokument ist die **Verfassung** für Menschen und Agenten. Änderungen ohne Einhaltung sind ungültig.

## Mission

- Arbeite **minimal**, **prüfbar** und **sicher**.

## Definition of Done (DoD)

Ein Task ist erst fertig, wenn:

1. **Minimaler Diff** (keine unnötigen Format‑/Refactor‑Wellen)
2. `rb check` ist **grün**
3. Wenn betroffen: passende **Trigger‑Tests** sind grün (siehe Testmatrix)
4. Ergebnis ist **im UI/API** sichtbar oder durch Test belegbar
5. Falls neuer Fehler: **Error‑DB** Eintrag erstellt

## Guardrails

- Keine Secrets ins Repo, Logs oder Dumps.
- Keine destruktiven Commands ohne explizite Freigabe.
- Max. {{MAX_FILES_CHANGED}} Dateien pro Task ohne Freigabe.
- Keine Migrations‑Änderungen ohne Rollback/Notiz.

## Agent‑Regeln (Cursor/Antigravity)

- Lies zuerst `docs/_rb/02_SYSTEM_FACTS.md`
- Dann `docs/_rb/06_TEST_MATRIX.md`
- Arbeite in kleinen Schritten: Plan → Diff → Tests → Nachweis.
- Liefere am Ende:
  - Was geändert? (kurz)
  - Warum?
  - Welche Tests liefen?
  - Risiken/Tradeoffs?
