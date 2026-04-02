# 04_STANDARDS

## CODE REGELN
- **Kleine PRs**: Halte Diffs überschaubar.
- **Modularität**: Trenne Logik (Backend) strickt von Darstellung (UI).
- **Naming**: Sprechende Variablennamen.
    - Code: Englisch bevorzugt.
    - UI: Deutsch.

## DIE 4 GESETZE (UX/UI CORE)
Jedes Interface und jede Core-Logik muss diesen Regeln folgen:

### §1. TRANSPARENZ (Glass-Box Principle)
*Regel: Keine Hintergrund-Magie ohne Feedback.*
- **Pflicht**: Lange Prozesse brauchen Ladebalken oder Logs.
- **Ziel**: Der User muss jederzeit sehen, dass das System arbeitet und was es tut.

### §2. REVIDIERBARKEIT (Undo is King)
*Regel: Fehler müssen verzeihbar sein.*
- **Pflicht**: "Löschen" bedeutet immer "Papierkorb" (Soft Delete).
- **Pflicht**: Verschiebungen und kritische Änderungen brauchen eine Undo-Option.

### §3. PROGRESSIVE OFFENLEGUNG (No Clutter)
*Regel: Zeige Informationen nur, wenn sie relevant sind.*
- **Pflicht**: Clean Default-View.
- **Pflicht**: Details (Metadaten, Logs, Debug-Infos) erst per Hover oder Klick (Quick-Look) einblenden.
- **Ziel**: Den User nicht überfluten, aber nichts vorenthalten.

### §4. MENSCHLICHE HOHEIT (Human-in-the-Loop)
*Regel: Die KI ist der Antragsteller, der Mensch der Richter.*
- **Pflicht**: KI schlägt vor -> Mensch bestätigt.
- **Pflicht**: Keine Vollautomatisierung kritischer Aktionen (Löschen, Deployment) ohne explizites "God-Mode" Opt-In.

## LOGGING
- **Keine Secrets**: Niemals Passwörter oder Keys loggen.
- **Debug-Fähigkeit**: Logs müssen Timestamps und Modul-Namen enthalten, um Fehler nachvollziehbar zu machen.
