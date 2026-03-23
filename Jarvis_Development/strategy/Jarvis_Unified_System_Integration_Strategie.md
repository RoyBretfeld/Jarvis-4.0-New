Jarvis Unified System Integration - Master Manifest
===================================================

Dieses Dokument definiert die Synergien zwischen dem Chat, dem
RAG-System und dem Coding Lab innerhalb des Jarvis-Ökosystems nach dem
**RB-Protokoll**.

1. Die Architektur der Trinität
-------------------------------

Das System operiert als geschlossener Kreislauf:

-   **Input (Chat):** Der User gibt eine vage Idee vor.

-   **Retrieval (RAG):** Jarvis durchsucht Drive nach relevanten
    > Architektur-Vorgaben (\_rb, 02\_SYSTEM\_FACTS.md).

-   **Execution (Development):** Der \@coder erhält präzise Fragmente
    > aus dem RAG und implementiert diese in Monaco/OpenShell.

2. Strategische RAG-Anbindung für Agenten
-----------------------------------------

Der größte Flaschenhals ist das Token-Limit. Daher nutzen wir **\"Smart
Context Injection\"**:

1.  **Vector-Search:** Wenn der \@coder eine Funktion baut, triggert der
    > Orchestrator eine RAG-Suche nach ähnlichen Code-Mustern in deinen
    > bestehenden Projekten.

2.  **Fact-Checking:** Der \@security Agent gleicht den Code gegen deine
    > Sentinel\_Security\_Policy im RAG ab.

3.  **Context-Pruning:** Nur die relevantesten 3-5 Dokumenten-Chunks
    > werden in den Prompt des Sub-Agenten injiziert (**Gesetz 3:
    > Progressive Offenlegung**).

3. UI-Transition & State Management
-----------------------------------

Die UI muss nahtlos zwischen \"Beratung\" und \"Bau\" wechseln:

-   **Globaler Context:** Der Chat-Verlauf aus dem Kommunikations-Hub
    > bleibt erhalten, wenn man in das Coding Lab wechselt.

-   **Knowledge-Sidepanel:** Im Coding Lab gibt es ein einklappbares
    > Element, das die aktuell vom RAG geladenen \"Wissens-Chunks\"
    > anzeigt (**Gesetz 1: Glass-Box**).

4. Prompt-Strategie: \"The Knowledge-Aware Coder\"
--------------------------------------------------

Dies ist der strategische Prompt für den \@coder, wenn er auf das RAG
zugreift:

\#\#\# SYSTEM-PROMPT: RAG-Enhanced Coder

Du bist ein Senior Coder mit Zugriff auf das Jarvis-Gedächtnis.

Workflow:

1\. Bevor du eine Zeile schreibst, frage das RAG-System nach dem
\'RB-Coding-Standard\'.

2\. Nutze ausschließlich die im RAG gefundenen Bibliotheken und
Patterns.

3\. Falls das RAG widersprüchliche Informationen liefert, stoppe und
frage im Haupt-Chat nach Klärung.

5. Security & Privacy (The Sovereign Layer)
-------------------------------------------

Da wir Cloud-Reasoning (Nemotron) nutzen, filtert der RAG-Proxy alle
sensiblen Daten:

-   **Anonymisierung:** Namen, IPs und echte Secrets werden durch
    > Platzhalter ersetzt, bevor sie die lokale Umgebung verlassen.

-   **Re-Substitution:** Bei der Rückgabe aus der Cloud werden die
    > Platzhalter lokal in der OpenShell-Sandbox wieder durch die echten
    > Werte ersetzt.

*Status: Integrations-Strategie finalisiert.* *Erstellt durch: The
Architekt*
