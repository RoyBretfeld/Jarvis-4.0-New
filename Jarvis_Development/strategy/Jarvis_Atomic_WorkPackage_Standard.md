\---

name: "Jarvis Atomic Work-Package (AWP) Standard"

type: "Operative Direktive"

version: "1.0.0"

status: "Aktiv"

\---



\# 🧩 Jarvis Atomic Work-Package (AWP) Standard



Dieses Dokument definiert die maximale Größe und Struktur eines Arbeitsschritts, um "Chaos-Sprünge" der KI zu verhindern. Es dient als operative Erweiterung des SEC-Protokolls.



\---



\## 1. Die "Häppchen"-Metrik (Größenbeschränkung)

Ein Arbeitspaket (AWP) gilt nur dann als atomar, wenn es eine der folgenden Grenzen \*\*NICHT\*\* überschreitet:



\* \*\*Code\*\*: Maximal 1 neue Funktion ODER das Refactoring von maximal 20 Zeilen Code.

\* \*\*UI\*\*: Maximal 1 Komponente (z. B. nur der 'Button', nicht das ganze 'Formular').

\* \*\*Infrastruktur\*\*: Maximal 1 Docker-Parameter ODER 1 API-Route.



\---



\## 2. Struktur eines AWP-Befehls

Sobald eine Aufgabe gestellt wird, muss die ausführende KI diese \*\*SOFORT\*\* intern in AWPs zerlegen.



\### Beispiel für den Umbau (Vom Chaos zum Atom):

\* ❌ \*\*Falscher Befehl\*\*: "Baue das Login-System mit Frontend und Backend."

\* ✅ \*\*Atomare Zerlegung\*\*:

&#x20;   \* \*\*AWP-1\*\*: Erstelle die `auth\_schema.json` für die Datenbank.

&#x20;   \* \*\*AWP-2\*\*: Implementiere die `/login` Route im Gateway-Container.

&#x20;   \* \*\*AWP-3\*\*: Erstelle die Monaco-Editor-Komponente für das Passwortfeld.



\---



\## 3. Der "Synchronisations-Zwang" (Checkpoints)

Nach \*\*JEDEM\*\* atomaren Häppchen (AWP) muss die KI zwingend folgende Schritte ausführen:



1\.  Den Code in der `OpenShell-Sandbox` erfolgreich testen.

2\.  Den Status in der `.jarvis/state.json` aktualisieren.

3\.  Dem User das Ergebnis präsentieren und fragen: \*"AWP-\[Nummer] abgeschlossen. Darf ich mit AWP-\[Nächste Nummer] fortfahren?"\*



\---



\## 4. Strategischer Prompt: "The Atomic Slicer"

Zusatz-Instruktion für den Orchestrator zur Komplexitätskontrolle:



> ### SYSTEM-PROMPT: Atomic Slicer (Complexity Guard)

> Du bist dafür verantwortlich, Aufgaben in die kleinstmöglichen Einheiten zu zerlegen.

> 

> \*\*Workflow\*\*:

> 1.  \*\*SLICING\*\*: Erstelle vor dem Triggering des `@coder` eine Liste von AWPs. Jedes AWP darf nur EIN Ziel haben.

> 2.  \*\*CONTEXT-ISOLATION\*\*: Gib dem `@coder` für jedes AWP NUR den Kontext, der für diesen einen Schritt nötig ist.

> 3.  \*\*NO-PARALLELISM\*\*: Verbiete dem `@coder`, zwei AWPs gleichzeitig anzugehen.

> 

> \*\*Gesetz der menschlichen Hoheit\*\*: Falls eine Aufgabe zu groß ist, antworte: \*"Das ist zu groß für ein Häppchen. Hier ist mein Vorschlag für die atomare

