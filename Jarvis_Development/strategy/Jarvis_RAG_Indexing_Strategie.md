Jarvis RAG Indexing - Strategisches Protokoll
=============================================

Dieses Dokument definiert die Strategie zur semantischen Indizierung und
Suche von Daten innerhalb des Jarvis-Ökosystems, optimiert für High-End
SSD-Setups.

1. Die Daten-Pipeline (Ingestion Flow)
--------------------------------------

Jarvis überwacht dein Google Drive und verarbeitet neue Informationen in
vier Phasen:

  **Phase**        **Aktion**                                                **Host-Ressource**
  ---------------- --------------------------------------------------------- ---------------------------
  **Extraction**   Parsing von PDF, MD, Code-Files.                          CPU Core 4-5
  **Chunking**     Aufteilen in kontextuelle Fragmente (z.B. 1000 Tokens).   CPU Core 6
  **Embedding**    Umwandlung in Vektoren via \'bge-small-en-v1.5\'.         CPU Core 16-31 (Parallel)
  **Upsert**       Speicherung in der Vektor-DB auf SSD 2.                   SSD 2 (I/O Bound)

2. Strategischer Prompt: \"The Librarian Agent\"
------------------------------------------------

MD-Anweisung für die Logik der Wissensverwaltung:

\#\#\# SYSTEM-PROMPT: Librarian Agent

Du bist der Hüter des Jarvis-Gedächtnisses.

Aufgabe: Optimiere den Suchkontext für die Coding-Agenten.

Workflow:

1\. HYBRID SEARCH: Kombiniere Vektorsuche (semantisch) mit Keyword-Suche
(exakt), um spezifische Funktionsnamen in deinem Drive sofort zu finden.

2\. CONTEXT RELEVANCE: Bewerte Suchergebnisse nach Aktualität und
Relevanz zum aktuellen Monaco-Editor-Fenster.

3\. PRUNING: Falls das RAG-Ergebnis das Token-Limit sprengt, fasse die
Dokumente zusammen (Summarization), statt sie abzuschneiden.

Gesetz der Transparenz: Zeige im \'Knowledge-Sidepanel\' an: \"🔍 Suche
in 4.500 Dokumenten abgeschlossen. 3 Treffer gefunden.\"

3. SSD-Optimierung (Multi-Disk Strategie)
-----------------------------------------

-   **Write-Ahead-Logging (WAL):** Wir legen das WAL der Vektordatenbank
    > auf die schnellste SSD (NVMe), um Schreibzugriffe bei massiven
    > Datei-Uploads zu beschleunigen.

-   **Vektor-Kompression:** Für \"Cold Data\" (alte Projekte) nutzen wir
    > Product Quantization (PQ), um RAM zu sparen, ohne die Genauigkeit
    > massiv zu beeinträchtigen.

4. Revisions-Management (Undo-King)
-----------------------------------

Jarvis indiziert nicht einfach über bestehende Daten drüber:

-   Jeder Index erhält einen **Timestamp-Tag**.

-   Wenn du sagst \"Jarvis, vergiss das letzte Dokument-Update\", kann
    > das System auf den Index-Snapshot von vor 10 Minuten
    > zurückspringen.

5. Security & Isolation
-----------------------

Der Indizierungs-Prozess läuft in einem Container ohne Netzwerkzugriff.
Embeddings werden rein lokal berechnet. Nur die fertigen
(anonymisierten) Such-Vektoren werden bei Bedarf im Kontext an den
Cloud-Orchestrator übergeben.

*Status: RAG-Indexing-Strategie finalisiert.* *Erstellt durch: The
Architekt*
