Jarvis Control Center - UI/UX Spezifikation
===========================================

Dieses Dokument definiert das Interface-Design und die Benutzerführung
für das zentrale Steuerungsmodul von Jarvis. Es folgt strikt dem
**RB-Protokoll** (Glass-Box & Progressive Offenlegung).

1. Das Drei-Spalten-Layout (The Command Bridge)
-----------------------------------------------

Die IDE-Umgebung ist in drei funktionale vertikale Sektionen unterteilt:

### A. Linke Spalte: Sovereign Explorer (20%)

-   **Datei-Explorer:** Lokale Projektstruktur.

-   **Container-Status:** Echtzeit-Indikatoren (🟢/🔴) für jarvis-core,
    > rag, gateway und sandbox.

-   **Resource Monitor:** Ein kompakter Graph, der die Lastverteilung
    > auf den 32 Threads deines Ryzen 9 7950X zeigt.

### B. Mittlere Spalte: Monaco Core (50%)

-   **Editor:** Monaco Editor Instanz mit Full-Syntax-Highlighting.

-   **Diff-Overlay:** Bei KI-Vorschlägen wird automatisch ein
    > Side-by-Side-Vergleich eingeblendet.

-   **Floating Action Bar:** Buttons für \[Kompilieren\], \[In Sandbox
    > testen\] und \[Veto/Abbruch\].

### C. Rechte Spalte: Agentic Intelligence Hub (30%)

-   **Chat-Interface:** Trennung zwischen Benutzer-Eingabe und
    > Agenten-Output.

-   **Thought Blocks:** Die Gedankengänge von Nemotron 3 Super werden in
    > einklappbaren Blöcken dargestellt (**Progressive Offenlegung**).

-   **Skill-Dock:** Anzeige der aktuell geladenen Skills aus dem
    > Master-Katalog.

2. Die \"Glass-Box\" Features (Echtzeit-Monitoring)
---------------------------------------------------

Um das Black-Box-Phänomen zu eliminieren, integrieren wir:

1.  **Trace-Log:** Ein schmales Terminal am unteren Rand, das die
    > maskierten Prompts zeigt, die an die Cloud gesendet werden
    > (Sovereign Layer Transparenz).

2.  **Privacy-Alerts:** Ein visuelles Signal, wenn der Filter-Agent
    > sensible Daten erkennt und maskiert.

3.  **Undo-Historie:** Ein Slider, um den Zustand des Monaco-Editors auf
    > jeden beliebigen Snapshot der letzten 60 Minuten zurückzusetzen
    > (**Gesetz 2: Revidierbarkeit**).

3. Interaktions-Logik (Menschliche Hoheit)
------------------------------------------

Jarvis darf niemals autonom Dateien auf deinem Host-System
überschreiben.

-   **Stage 1 (Entwurf):** Code erscheint im Monaco-Editor in einem
    > temporären Puffer.

-   **Stage 2 (Validation):** Der \@tester Agent prüft den Code in der
    > jarvis-sandbox.

-   **Stage 3 (Commit):** Erst nach deinem Klick auf \[Änderungen
    > übernehmen\] wird die lokale Datei physikalisch geschrieben.

4. Strategischer Prompt: \"The UX Architect\"
---------------------------------------------

Anweisung zur Ausarbeitung der Frontend-Komponenten:

\#\#\# SYSTEM-PROMPT: UI Component Architect

Aufgabe: Entwirfe die Spezifikation für das \'Jarvis Dashboard Widget\'.

1\. MONITORING: Erstelle ein Layout für 32 kleine Balken, die die
Ryzen-Threads repräsentieren.

2\. AGENT-BUBBLES: Definiere Icons für \@coder, \@tester und \@security,
die pulsieren, wenn der jeweilige Container CPU-Zyklen beansprucht.

3\. KNOWLEDGE-CHIPS: Entwirf eine Anzeige für RAG-Ergebnisse, die wie
kleine \'Wissens-Karten\' aussehen und per Drag-and-Drop in den Chat
gezogen werden können.

Gesetz der Transparenz: Der User muss jederzeit sehen können, welcher
Skill gerade \'aktiv\' im RAM geladen ist.

*Status: UI/UX Spezifikation finalisiert.* *Erstellt durch: The
Architekt*
