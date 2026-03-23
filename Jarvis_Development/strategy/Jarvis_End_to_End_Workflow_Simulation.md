Jarvis End-to-End Workflow Simulation
=====================================

Dieses Dokument beschreibt den exakten Durchlauf einer komplexen
Benutzeranfrage durch alle Schichten der Jarvis-Architektur. Es dient
als Referenz für die System-Validierung nach dem **RB-Protokoll**.

🚀 Szenario: \"Implementiere ein verschlüsseltes Logging-Modul\"
---------------------------------------------------------------

### Phase 1: Der Kommunikations-Hub (Input)

-   **Aktion:** Der User tippt im Jarvis-Chat: *\"Ich brauche ein
    > Python-Modul, das Logs verschlüsselt auf SSD 2 speichert.\"*

-   **Status:** Der Orchestrator erkennt den Task \"Security/IO\" und
    > aktiviert den \@coder.

### Phase 2: Das Langzeitgedächtnis (Retrieval)

-   **Aktion:** Der **Librarian Agent** durchsucht das RAG nach:

    1.  RB-Coding-Standard

    2.  ryzen\_multi\_thread\_optimizer (für SSD-Performance)

    3.  Vorhandene Krypto-Libs in Drive-Projekten.

-   **Ergebnis:** Die relevanten Wissens-Chunks werden als Kontext
    > bereitgestellt.

### Phase 3: Der Sovereign Layer (Privacy Masking)

-   **Aktion:** Der **Privacy Filter Agent** scannt den Kontext.

-   **Maskierung:** Der reale Pfad zu SSD 2 (D:/Jarvis/Logs) wird durch
    > \[STORAGE\_PATH\_SECURE\] ersetzt.

-   **Egress:** Der bereinigte Prompt geht an die Ollama-Cloud
    > (nemotron-3-super).

### Phase 4: Die Reasoning-Engine (Cloud)

-   **Aktion:** Nemotron entwirft die Logik basierend auf den maskierten
    > Daten.

-   **Output:** Generierter Python-Code, der Platzhalter nutzt.

### Phase 5: Die Werkstatt (Execution & Sandbox)

-   **Aktion:** Der Code landet in der **OpenShell-Sandbox**
    > (jarvis-sandbox).

-   **Re-Substitution:** Jarvis ersetzt \[STORAGE\_PATH\_SECURE\] lokal
    > wieder durch den echten Pfad.

-   **Validation:** Der \@tester Agent führt einen Testlauf durch.

-   **Sentinel-Check:** Der \@security Agent prüft, ob die
    > Verschlüsselung (AES) korrekt implementiert ist.

### Phase 6: Die Menschliche Hoheit (UI/UX)

-   **Aktion:** Der Monaco-Editor wechselt in den **Diff-Modus**.

-   **Visualisierung:** Der User sieht links den leeren Editor, rechts
    > den verschlüsselten Logging-Code.

-   **Entscheidung:** Der User klickt auf \[Änderungen übernehmen\].

*Status: Workflow-Simulation abgeschlossen.* *Archiviert in:
Jarvis\_Development/strategy/*
