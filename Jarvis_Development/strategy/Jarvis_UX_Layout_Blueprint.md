📐 Jarvis UX Layout Blueprint - Das Cockpit der Souveränität
===========================================================

Dieses Dokument definiert die visuelle Anordnung und die interaktiven
Komponenten der Jarvis-IDE. Es dient als exakte Bauanweisung für die
Frontend-KI.

1. Die Vier-Zonen-Architektur
-----------------------------

### ZONE A: Sentinel Sidebar (Links, 15%)

-   **Top:** \"System Pulse\" -- 32 kleine, vertikale LED-Balken (Ryzen
    > 9 7950X Threads).

-   **Mitte:** Docker-Container-Manager. Status-Icons (aktiv/idle) für
    > core, rag, gateway, sandbox.

-   **Bottom:** Skill-Quickloader. Eine scrollbare Liste der MD-Skills
    > aus Drive.

### ZONE B: Monaco Core Engine (Mitte, 55%)

-   **Haupt-Editor:** Monaco Editor mit Tab-Management.

-   **Header-Leiste:** Breadcrumbs (Pfad) + \[Plan-Mode Toggle\] +
    > \[Sandbox-Run Button\].

-   **Diff-Layer:** Ein Overlay-Modus, der bei KI-Vorschlägen
    > automatisch aktiv wird (Links: Original / Rechts: Vorschlag).

-   **Veto-Bar:** Ein fest fixierter Balken am unteren Rand des Editors
    > mit den Buttons: \[BACKUP & MERGE\] und \[ABORT & WIPE\].

### ZONE C: Agentic Intelligence Hub (Rechts, 30%)

-   **Chat-Stream:** Token-by-Token Streaming der Agenten-Antworten.

-   **Agent-Avatar-Leiste:** Kleine Icons zeigen, welcher Agent
    > (\@coder, \@tester, \@security) gerade schreibt.

-   **Thought-Drawers:** Einklappbare Sektionen unter jeder Nachricht,
    > die den internen Monolog (Reasoning) zeigen.

-   **Tool-Traces:** Kleine Popups zeigen, wenn ein Plugin (MCP)
    > aufgerufen wird (z.B. \"Reading Drive\...\").

### ZONE D: Sovereign Trace Log (Unten, fixiert, 100-200px Höhe)

-   **Status:** \"Glass-Box\" Log-Stream.

-   **Links:** Echtzeit-Output der jarvis-sandbox (Terminal).

-   **Rechts:** \"Privacy Guard\" Log. Zeigt an, welche Daten maskiert
    > wurden (z.B. 12:01 - Masked IP 192.168.1.5 -\> \[INTERNAL\_IP\]).

2. Interaktions-Flow: Das \"Human-Gate\" Design
-----------------------------------------------

1.  **Eingabe:** User schreibt im Hub (Zone C).

2.  **Planung:** Agent entwirft Plan. Dieser erscheint als Checkliste im
    > Hub. User klickt \[Start Execution\].

3.  **Vorschau:** Code erscheint als \"Ghost-Text\" in Monaco (Zone B).

4.  **Testing:** Der \@tester lässt Ergebnisse im Trace Log (Zone D)
    > durchlaufen.

5.  **Entscheidung:** Erst nach grünem Licht in Zone D und Sichtung des
    > Diffs in Zone B wird der Commit-Button in der Veto-Bar aktiv.

3. Strategischer Prompt: \"The UI Implementation Guide\"
--------------------------------------------------------

\#\#\# SYSTEM-PROMPT: UI Framework Developer

Aufgabe: Setze das \'Jarvis UX Layout\' mit React und Tailwind CSS um.

Design-Vorgaben:

1\. THEME: \'Sovereign Dark\' (Tiefes Anthrazit \#121212, Akzentfarben:
Sentinel-Grün \#00FF41, Alert-Rot \#FF3131).

2\. RESPONSIVITÄT: Das Layout ist für 4K-Monitore optimiert. Nutze
CSS-Grids, um die Zonen A-D stabil zu halten.

3\. REAKTIVITÄT: Die Ryzen-Thread-Anzeige muss per WebSocket mit 500ms
Intervall aktualisiert werden.

Gesetz der Revidierbarkeit: Implementiere einen globalen
\'Panic-Button\' (ESC-Key), der alle laufenden Agenten-Tasks sofort
killt und die Sandbox bereinigt.

*Status: Layout-Spezifikation finalisiert.* *Archiviert in:
Jarvis\_Development/strategy/*
