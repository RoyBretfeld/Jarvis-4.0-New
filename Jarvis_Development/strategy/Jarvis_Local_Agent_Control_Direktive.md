🧩 Spezial-Direktive: Local-Agent Control (Qwen 14b Edition)
===========================================================

Dieses Dokument ergänzt den Masterplan für den Einsatz von lokalen
Modellen wie Qwen2.5-Coder 14b innerhalb von Claude Code.

1. Die \"Eisberg\"-Regel (Kontext-Limitierung)
----------------------------------------------

Da ein 14b Modell bei zu viel Kontext zu Fehlern neigt:

-   **Direktive:** Lade niemals das gesamte Projekt in den Prompt.

-   **Aktion:** Nutze das RAG-System, um Qwen nur die exakte Datei und
    > die direkt betroffenen Schnittstellen zu zeigen. Der \"Rest des
    > Eisbergs\" bleibt unter Wasser (lokal auf der SSD).

2. Der \"Status-Anker\" Zwang
-----------------------------

Qwen neigt dazu, höflich zu sein und den Plan zu vergessen.

-   **Regel:** Jede Antwort von Qwen muss zwingend mit dem Wort STATUS:
    > beginnen, gefolgt von der AWP-Nummer aus dem Masterplan.

-   **Sanktion:** Falls Qwen direkt mit Code beginnt, muss Claude Code
    > den Task sofort abbrechen und die state.json neu einlesen.

3. Explizites \"Chaining\" statt \"Multitasking\"
-------------------------------------------------

-   **Verbot:** Qwen darf niemals zwei Dateien in einem einzigen Turn
    > bearbeiten.

-   **Workflow:**

    1.  Datei A ändern.

    2.  In Sandbox testen.

    3.  User-Bestätigung abwarten.

    4.  ERST DANN Datei B anfangen.

4. Hardware-Nutzung (Ryzen 9 7950X)
-----------------------------------

-   Qwen soll angewiesen werden, komplexe Logik-Tests in Python immer
    > als separate Multiprocessing-Skripte auszulagern, um die 32
    > Threads deines Ryzen zu nutzen, statt den Haupt-Thread des Agenten
    > zu blockieren.

*Status: Direktive für lokale Modelle verankert.* *Ziel: 100% Stabilität
bei 14b Parametern.*
