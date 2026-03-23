\---

name: "Jarvis Atomic Work-Package (AWP) Standard"

type: "Operative Direktive"

version: "1.0.0"

status: "Aktiv"

\---



\# 🧩 Jarvis Atomic Work-Package (AWP) Standard



\[cite\_start]Dieses Dokument definiert die maximale Größe und Struktur eines Arbeitsschritts, um "Chaos-Sprünge" der KI zu verhindern\[cite: 35, 36]. \[cite\_start]Es dient als operative Erweiterung des SEC-Protokolls\[cite: 37].



\---



\## 1. Die "Häppchen"-Metrik (Größenbeschränkung)

\[cite\_start]Ein Arbeitspaket (AWP) gilt nur dann als atomar, wenn es eine der folgenden Grenzen \*\*NICHT\*\* überschreitet\[cite: 38, 39]:



\* \[cite\_start]\*\*Code\*\*: Maximal 1 neue Funktion ODER das Refactoring von maximal 20 Zeilen Code\[cite: 40].

\* \[cite\_start]\*\*UI\*\*: Maximal 1 Komponente (z. B. nur der 'Button', nicht das ganze 'Formular')\[cite: 41].

\* \[cite\_start]\*\*Infrastruktur\*\*: Maximal 1 Docker-Parameter ODER 1 API-Route\[cite: 42].



\---



\## 2. Struktur eines AWP-Befehls

\[cite\_start]Sobald eine Aufgabe gestellt wird, muss die ausführende KI diese \*\*SOFORT\*\* intern in AWPs zerlegen\[cite: 43, 44].



\### Beispiel für den Umbau (Vom Chaos zum Atom):

\* \[cite\_start]❌ \*\*Falscher Befehl\*\*: "Baue das Login-System mit Frontend und Backend." \[cite: 46]

\* \[cite\_start]✅ \*\*Atomare Zerlegung\*\*: \[cite: 47]

&#x20;   \* \[cite\_start]\*\*AWP-1\*\*: Erstelle die `auth\_schema.json` für die Datenbank\[cite: 48].

&#x20;   \* \[cite\_start]\*\*AWP-2\*\*: Implementiere die `/login` Route im Gateway-Container\[cite: 49].

&#x20;   \* \[cite\_start]\*\*AWP-3\*\*: Erstelle die Monaco-Editor-Komponente für das Passwortfeld\[cite: 50].



\---



\## 3. Der "Synchronisations-Zwang" (Checkpoints)

\[cite\_start]Nach \*\*JEDEM\*\* atomaren Häppchen (AWP) muss die KI zwingend folgende Schritte ausführen\[cite: 51, 52]:



1\.  \[cite\_start]Den Code in der `OpenShell-Sandbox` erfolgreich testen\[cite: 53].

2\.  \[cite\_start]Den Status in der `.jarvis/state.json` aktualisieren\[cite: 54].

3\.  \[cite\_start]Dem User das Ergebnis präsentieren und fragen: \*"AWP-\[Nummer] abgeschlossen. Darf ich mit AWP-\[Nächste Nummer] fortfahren?"\* \[cite: 55]



\---



\## 4. Strategischer Prompt: "The Atomic Slicer"

\[cite\_start]Zusatz-Instruktion für den Orchestrator zur Komplexitätskontrolle\[cite: 56, 57]:



> \[cite\_start]### SYSTEM-PROMPT: Atomic Slicer (Complexity Guard) \[cite: 58]

> \[cite\_start]Du bist dafür verantwortlich, Aufgaben in die kleinstmöglichen Einheiten zu zerlegen\[cite: 59].

> 

> \[cite\_start]\*\*Workflow\*\*: \[cite: 60]

> 1.  \*\*SLICING\*\*: Erstelle vor dem Triggering des `@coder` eine Liste von AWPs. \[cite\_start]Jedes AWP darf nur EIN Ziel haben\[cite: 61].

> \[cite\_start]2.  \*\*CONTEXT-ISOLATION\*\*: Gib dem `@coder` für jedes AWP NUR den Kontext, der für diesen einen Schritt nötig ist\[cite: 62].

> \[cite\_start]3.  \*\*NO-PARALLELISM\*\*: Verbiete dem `@coder`, zwei AWPs gleichzeitig anzugehen\[cite: 63].

> 

> \[cite\_start]\*\*Gesetz der menschlichen Hoheit\*\*: Falls eine Aufgabe zu groß ist, antworte: \*"Das ist zu groß für ein Häppchen. Hier ist mein Vorschlag für die atomare Zerlegung..."\* \[cite: 64]



\---



\## 5. Das Veto-Recht des Architekten

\[cite\_start]Falls die KI versucht, zwei AWPs während der Ausführung zu mergen, wird dies als \*\*Protokoll-Verletzung\*\* gewertet\[cite: 65, 66]. \[cite\_start]Der Sentinel blockiert den Schreibvorgang in diesem Fall automatisch\[cite: 67].



\---

\[cite\_start]\*\*Status\*\*: AWP-Standard aktiv \[cite: 68]

\[cite\_start]\*\*Archiviert in\*\*: `Jarvis\_Development/strategy/` \[cite: 68]

