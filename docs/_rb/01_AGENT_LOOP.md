# 01_AGENT_LOOP

1. Task verstehen: Ziel + Scope + Nicht‑Ziele
2. Status quo prüfen: `rb check` (und Failures notieren)
3. Error‑DB scannen: ähnliche Symptome? bekannte Fallen?
4. Minimal ändern (kleiner Patch)
5. Wieder prüfen: `rb check`
6. Trigger‑Tests laufen lassen (falls betroffen)
7. Ergebnis belegen (Screenshot/Log/Test)
8. Wenn neuer Fehler: Error‑DB Eintrag
9. Abschluss: Diff‑Summary + Test‑Nachweis
