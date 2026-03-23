Jarvis Skill-Creation-Protokoll
===============================

Dieses Dokument definiert den standardisierten Prozess, wie Jarvis
selbstständig neue Fähigkeiten (Skills) entwickelt, validiert und in den
Master-Katalog aufnimmt.

1. Identifikation (Gap Analysis)
--------------------------------

Der Orchestrator erkennt, wenn ein Benutzerauftrag eine Expertise
erfordert, die im Jarvis\_Master\_Skill\_Katalog fehlt.

-   **Aktion:** Jarvis fragt: *\"Ich habe keinen Skill für \[Thema\].
    > Soll ich ein neues Skill-Profil erstellen?\"*

2. Draft-Phase (Prompt Engineering)
-----------------------------------

Der **Skill Architect** entwirft eine neue .md-Datei im Verzeichnis
skills/.

-   **Inhalt:** YAML-Header, strategische Anweisungen und notwendige
    > Tool-Anbindungen.

-   **Sicherheits-Check:** Der Skill muss das **Police-Prinzip** (keine
    > Hardcoded Secrets) bereits in seiner Anweisung verankert haben.

3. Validierungs-Zyklus (Sandbox Testing)
----------------------------------------

Ein neuer Skill wird nicht sofort aktiv geschaltet. Er durchläuft eine
Testphase:

1.  **Simulation:** Jarvis führt einen Test-Task in der Sandbox unter
    > Nutzung des neuen Skills aus.

2.  **Review:** Der \@tester prüft, ob der Output des neuen Skills
    > stabil und effizient (Ryzen-optimiert) ist.

3.  **Feedback:** Bei Fehlern wird der Skill-Prompt automatisch
    > nachjustiert.

4. Integration (Master Catalog Update)
--------------------------------------

Nach erfolgreichem Test erfolgt die Registrierung:

-   **Eintrag:** Der neue Skill wird als Kurzreferenz im
    > Jarvis\_Master\_Skill\_Katalog hinzugefügt.

-   **Persistenz:** Die detaillierte MD-Datei wird in Drive gespeichert.

5. Strategischer Prompt: \"The Self-Evolution Agent\"
-----------------------------------------------------

MD-Anweisung für Jarvis zur Selbstentwicklung:

\#\#\# SYSTEM-PROMPT: Self-Evolution Agent

Aufgabe: Erweitere deine eigenen Fähigkeiten durch Skill-Design.

Workflow:

1\. ANALYSE: Falls eine Fehlerrate bei einem bestimmten Task-Typ (z.B.
CSS-Grid) steigt, entwirf einen \'Correction-Skill\'.

2\. HARDWARE-ALIGNMENT: Optimiere jeden neuen Skill für die 32 Kerne des
Ryzen 9.

3\. RB-DOC: Schreibe die Dokumentation des Skills so, dass sie für
Menschen (Glass-Box) und andere Agenten lesbar ist.

Menschliche Hoheit: Ein neuer Skill wird erst nach deiner expliziten
Freigabe \'Scharf\' geschaltet.

*Status: Protokoll für System-Evolution finalisiert.* *Archiviert in:
Jarvis\_Development/skills/*
