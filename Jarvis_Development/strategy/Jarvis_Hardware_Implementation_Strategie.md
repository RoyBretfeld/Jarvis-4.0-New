Jarvis Technological Implementation - Hardware Mapping
======================================================

Dieses Dokument definiert die technische Nutzung der vorhandenen
Hardware (AMD Ryzen 9 7950X, 32GB RAM) zur Steuerung des
Jarvis-Ökosystems nach dem **RB-Protokoll**.

1. Ressourcen-Allokation (Workload Distribution)
------------------------------------------------

  **Komponente**          **Host-Ressource**         **Strategie**
  ----------------------- -------------------------- ------------------------------------------------------
  **Jarvis Core Hub**     CPU Core 0-3               Zentrales Management & UI-Routing.
  **RAG Vector DB**       CPU Core 4-7 + SSD A       Lokale Indizierung und schnelle semantische Suche.
  **OpenShell Sandbox**   CPU Core 8-15 + 16GB RAM   Isolierte Umgebung für Code-Tests & Sub-Agenten.
  **Privacy Filter**      CPU Core 16-31             Echtzeit-Maskierung vor dem Cloud-Egress (Nemotron).

2. Der \"Local-First\" Daten-Stack
----------------------------------

Trotz Cloud-Reasoning bleibt die Datenhoheit lokal:

-   **Vector DB:** Einsatz von **Qdrant** oder **ChromaDB**
    > (Docker-basiert), optimiert für die AVX-512 Befehlssätze des Ryzen
    > 7950X.

-   **Embedding Modell:** Ein kleines, CPU-optimiertes Modell (z.B.
    > bge-small-en-v1.5) läuft permanent lokal, um Drive-Dokumente zu
    > vektorisieren.

3. Strategischer Prompt: \"The Hardware-Aware Orchestrator\"
------------------------------------------------------------

MD-Anweisung für Jarvis, wie er die lokale Power nutzt:

\#\#\# SYSTEM-PROMPT: Resource Manager Agent

Du bist der Verwalter der Jarvis-Rechenpower.

Aufgabe: Überwache die Last auf dem Ryzen 9 7950X.

Workflow:

1\. Falls ein Coding-Task massive Unit-Tests erfordert, spawne bis zu 8
parallele Test-Threads in der OpenShell-Sandbox.

2\. Priorisiere RAM für den Privacy-Filter und die Vektordatenbank.

3\. Falls der RAM-Verbrauch 80% übersteigt, archiviere inaktive
Agenten-Kontexte sofort auf die SSD (Gesetz 2: Revidierbarkeit).

Transparenz-Gesetz: Zeige in der Jarvis-Statusbar die aktuelle CPU-Last
der aktiven Sub-Agenten an.

4. SSD-Konfiguration für maximale Performance
---------------------------------------------

-   **Drive 1 (System):** Jarvis OS & Core App.

-   **Drive 2 (Data):** Vektor-Indizes & lokaler Datei-Cache von Google
    > Drive.

-   **Drive 3 (Sandbox):** Flüchtige Daten der OpenShell-Sandbox. Wird
    > nach jedem Projekt-Abschluss bereinigt.

5. Security-Layer (Sentinel)
----------------------------

Die Sandbox (OpenShell) wird durch die
Hardware-Virtualisierungs-Features des Ryzen (AMD-V) zusätzlich
gehärtet, um Ausbrüche aus der Sandbox auf das Host-System zu
verhindern.

*Status: Hardware-Mapping abgeschlossen.* *Erstellt durch: The
Architekt*
