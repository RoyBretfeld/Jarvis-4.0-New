🎨 Jarvis UI Visual Identity & Dashboard Blueprint
=================================================

Basierend auf den initialen Design-Gedanken definiert dieses Dokument
die visuelle Sprache und das funktionale Layout des Jarvis-Dashboards
nach dem **RB-Protokoll**.

1. Das \"Agentic Aura\" Element (Zentraler Indikator)
-----------------------------------------------------

Wie in den Skizzen angedeutet, erhält Jarvis einen zentralen visuellen
Status-Hub:

-   **Zustand: IDLE:** Ruhiges, blaues Pulsieren (System bereit).

-   **Zustand: REASONING:** Schnelles, violettes Kreisen
    > (Cloud-Reasoning aktiv).

-   **Zustand: EVOLVING:** Rotes Glühen (Selbstoptimierung /
    > Code-Generierung).

-   **Zustand: ALERT:** Orangefarbenes Warnlicht (Privacy-Filter hat
    > Egress gestoppt).

2. Die \"Evolution-Timeline\" (Rechter Side-Panel)
--------------------------------------------------

Anstatt eines statischen Chats nutzen wir eine fließende Timeline der
System-Ereignisse:

1.  **Event-Cards:** Jede Aktion (z.B. \"RAG Index updated\") wird als
    > kleine Karte mit Zeitstempel dargestellt.

2.  **Deep-Dive:** Klickt man auf eine Karte, öffnet sich im
    > Monaco-Editor (Mitte) sofort der zugehörige Code-Diff oder das
    > Fehler-Log.

3. Ressourcen-Widget (Ryzen 9 Fokus)
------------------------------------

Um die Hardware-Hoheit zu visualisieren:

-   **32-Core Matrix:** Eine kompakte Ansicht aller Threads. Aktive
    > Agenten-Threads werden farblich hervorgehoben (z.B. \@tester =
    > grün, \@coder = blau).

-   **SSD I/O Meter:** Ein kleiner \"Tachometer\", der zeigt, wie
    > schnell das RAG-System gerade Daten von der NVMe-SSD liest.

4. Der \"Evolution-Approval\" Dialog
------------------------------------

Bevor Jarvis Code umschreibt, erscheint ein Full-Screen Overlay
(Glass-Box):

-   **Links:** \"Mein aktueller Zustand\" (Alt-Code).

-   **Rechts:** \"Mein verbesserter Zustand\" (Neu-Code).

-   **Unten:** Ein großer Button \[SYSTEM EVOLVIEREN\] -- geschützt
    > durch eine Sicherheitsabfrage.

5. Strategischer Prompt: \"The Frontend Alchemist\"
---------------------------------------------------

Anweisung für die Umsetzung der UI-Elemente:

\#\#\# SYSTEM-PROMPT: UI Alchemist

Aufgabe: Setze die \'Agentic Aura\' und das \'Evolution-Widget\' in
React um.

Richtlinien:

1\. PERFORMANCE: Die UI darf niemals mehr als 1% der CPU-Last des Ryzen
9 beanspruchen. Alles muss hardwarebeschleunigt (GPU) gerendert werden.

2\. FEEDBACK: Jede Cursor-Bewegung im Monaco-Editor muss subtile
Animationen im Dashboard triggern, um die Verbindung zwischen Code und
Systemzustand zu zeigen.

3\. DARK-MODE: Nutze ein High-Contrast Dark-Theme (OLED optimiert).

Transparenz-Gesetz: Wenn ein Pixel auf dem Bildschirm flackert, muss ein
Log-Eintrag existieren, der erklärt, warum.

*Status: Visueller Blueprint finalisiert.* *Archiviert in:
Jarvis\_Development/strategy/*
