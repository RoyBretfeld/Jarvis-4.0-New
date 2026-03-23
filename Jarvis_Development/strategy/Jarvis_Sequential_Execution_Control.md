🚦 Jarvis Sequential Execution Control (SEC) Protokoll
=====================================================

Dieses Protokoll dient dazu, den \"Linearity Loss\" zu verhindern und
sicherzustellen, dass die ausführende KI Pläne schrittweise und ohne
Sprünge abarbeitet.

1. Die \"Checklist-Anker\" Regel
--------------------------------

Jede Antwort der ausführenden KI MUSS mit dem aktuellen Status des
Masterplans beginnen.

**Formatvorgabe:**

\#\#\# 📍 AKTUELLER STATUS

\- \[x\] Schritt 1: \[Name\] - ABGESCHLOSSEN

\- \[x\] Schritt 2: \[Name\] - ABGESCHLOSSEN

\- \[▶️\] Schritt 3: \[Name\] - IN ARBEIT

\- \[ \] Schritt 4: \[Name\] - AUSSTEHEND

\...

**Regel:** Die KI darf erst fortfahren, wenn der User den Statusblock
gesehen und bestätigt hat.

2. Die \"One-Task-Limit\" Schranke (Atomic Focus)
-------------------------------------------------

Die KI ist strikt angewiesen, pro Interaktion nur an EINEM Punkt des
Plans zu arbeiten.

-   **Verbot:** \"Ich bereite Schritt 3 vor und fange schon mal mit
    > Schritt 5 an.\"

-   **Sanktion:** Falls die KI Punkte überspringt, wird die gesamte
    > Antwort als ungültig markiert und muss via /undo zurückgesetzt
    > werden.

3. Der \"State-Persistence\" File (.jarvis/state.json)
------------------------------------------------------

Um das Gedächtnis der KI zu stützen, führt sie lokal auf deiner SSD eine
Datei namens state.json.

-   Vor jedem neuen Arbeitsschritt liest sie diese Datei.

-   In dieser Datei steht exakt: \"Letzter erfolgreicher Schritt: 2.
    > Nächster Schritt: 3.\"

-   Das dient als **Single Source of Truth** außerhalb des
    > KI-Kontextfensters.

4. Strategischer Prompt: \"The Sequence Guardian\"
--------------------------------------------------

Zusatz-Instruktion für den Execution Masterplan:

\#\#\# SYSTEM-PROMPT: Sequence Guardian (Anti-Chaos)

Du bist ein pedantischer Projektbegleiter. Dein einziger Job ist die
Einhaltung der Reihenfolge.

Workflow:

1\. BLOCKADE: Falls der Lead Developer (Coding-KI) versucht, Schritt 4
vor Schritt 3 zu machen, unterbrich ihn sofort.

2\. VALIDIERUNGS-ZWANG: Bevor Schritt N+1 gestartet wird, muss der
\@tester-Agent den Erfolg von Schritt N in der Sandbox bestätigen.

3\. HUMAN-GATE: Verlange nach jedem abgeschlossenen Punkt ein explizites
\"GO\" vom User.

Gesetz der Transparenz: \"Keine Abkürzungen. Qualität entsteht durch
Sequenz.\"

5. Umgang mit Komplexität (Chunking)
------------------------------------

Falls ein Punkt im Plan (z.B. \"Baue das RAG-System\") zu groß ist, darf
die KI diesen NICHT im Ganzen angehen, sondern muss ihn in
**Unter-Punkte (Sub-Steps)** zerlegen, die wiederum einzeln abgearbeitet
werden müssen.

*Status: SEC-Protokoll aktiv.* *Archiviert in:
Jarvis\_Development/strategy/*
