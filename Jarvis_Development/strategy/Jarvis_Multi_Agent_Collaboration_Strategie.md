Jarvis Multi-Agent Collaboration - Strategisches Protokoll
==========================================================

Dieses Dokument definiert die Interaktionslogik zwischen den Sub-Agenten
innerhalb des **Jarvis Coding Lab**. Ziel ist eine hocheffiziente,
autonome Zusammenarbeit nach dem **RB-Protokoll**.

1. Rollenhierarchie & Orchestrierung
------------------------------------

-   **Der Orchestrator (Nemotron 3 Super):** Hält die \"High-Level
    > Vision\". Er empfängt die Benutzeranfrage, zerlegt sie in
    > Teilaufgaben und delegiert diese an die Spezialisten.

-   **Die Spezialisten (Sub-Agents):**

    -   \@coder: Fokus auf reine Implementierung im Monaco-Editor.

    -   \@tester: Fokus auf Verifizierung in der OpenShell-Sandbox.

    -   \@security: Proaktive Überwachung (Sentinel-Modus).

2. Handoff-Protokoll (Der \"Staffellauf\")
------------------------------------------

Um Inkonsistenzen zu vermeiden, folgt die Aufgabenübergabe einem
strikten Muster:

1.  **Request:** Orchestrator erstellt einen \"Task-Briefing\" für
    > den \@coder.

2.  **Implementation:** \@coder schreibt den Code in den Monaco-Layer.

3.  **Transfer:** Sobald der Code steht, triggert der Orchestrator
    > den \@tester.

4.  **Validation:** \@tester erhält Zugriff auf die Datei in der
    > OpenShell-Sandbox und führt Unit-Tests aus.

5.  **Report:** Das Testergebnis (Pass/Fail) geht zurück an den
    > Orchestrator, NICHT direkt an den User (**Progressive
    > Offenlegung**).

3. Feedback-Schleifen (Korrektur-Logik)
---------------------------------------

Wenn ein Fehler auftritt, greifen automatisierte Korrekturzyklen:

-   **Logik-Fehler:** \@tester meldet Fehlermeldung an \@coder. \@coder
    > korrigiert den Code im Monaco-Editor. Maximal 3 Versuche, bevor
    > menschliche Intervention gefordert wird (**Gesetz 4: Menschliche
    > Hoheit**).

-   **Sicherheits-Veto:** \@security scannt den Code parallel. Bei
    > Funden (z.B. Plaintext-Passwörter) wird der Handoff an den
    > \@tester sofort gestoppt.

4. Shared Context & Shared Memory
---------------------------------

Damit Agenten nicht aneinander vorbeireden, nutzen wir eine **zentrale
Kontext-Datei**:

-   **project\_state.json:** Eine flüchtige Datei in der
    > OpenShell-Sandbox, die den aktuellen Status aller Teilaufgaben
    > speichert.

-   **Memory-Access:** Jeder Agent liest beim Start die
    > project\_state.json, um zu wissen, was seine Vorgänger getan
    > haben.

5. User-Interaktion (Das \"Glass-Box\" Prinzip)
-----------------------------------------------

Im rechten Chat-Panel von Jarvis werden diese internen Übergaben
visualisiert:

-   *Status:* \"🔄 \@coder übergibt an \@tester\...\"

-   *Status:* \"✅ \@tester bestätigt Funktionalität.\"

-   *Aktion:* \"Möchten Sie die Änderungen in \[Datei.py\] übernehmen?
    > \[Zustimmen\] / \[Diff ansehen\]\"

*Status: Strategische Ausarbeitung abgeschlossen.* *Erstellt durch: The
Architekt*
