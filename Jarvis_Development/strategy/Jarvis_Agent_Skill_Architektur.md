\---

name: "Jarvis Agent Skill Architektur"

type: "Strategisches Protokoll"

version: "1.0.0"

status: "Finalisiert"

\---



\# 🏗️ Jarvis Agent Skill Architektur - Strategisches Protokoll



\[cite\_start]Dieses Dokument definiert den Standard für die Erweiterung der Agenten-Fähigkeiten innerhalb des Jarvis-Ökosystems\[cite: 1, 2]. \[cite\_start]Es basiert auf dem Prinzip der \*\*Expertise On-Demand\*\*\[cite: 3].



\---



\## 1. Anatomie eines Jarvis-Skills

\[cite\_start]Jeder Skill wird als Markdown-Datei im Verzeichnis `Jarvis\_Development/skills/` hinterlegt\[cite: 4, 5].



\### Metadaten (YAML-Header)

\[cite\_start]Jeder Skill startet mit folgendem Header\[cite: 6, 11]:

\- \[cite\_start]\*\*name\*\*: "Skill-Name" \[cite: 7]

\- \[cite\_start]\*\*description\*\*: "Kurze Beschreibung für den Librarian Agent" \[cite: 8]

\- \[cite\_start]\*\*version\*\*: "1.0.0" \[cite: 9]

\- \[cite\_start]\*\*tools\*\*: \["terminal", "rag\_access", "mcp\_github"] \[cite: 10]



\### Inhalt

\[cite\_start]Unter der Überschrift `# Anweisungen` folgen die strategischen Anweisungen für den Agenten, sobald der Skill aktiviert wird\[cite: 12, 13].



\---



\## 2. Der "Skill Librarian" Workflow

\[cite\_start]Um Token-Kosten zu sparen und die Präzision zu erhöhen, folgt Jarvis diesem Prozess\[cite: 14, 15]:



1\. \[cite\_start]\*\*Discovery\*\*: Der Orchestrator scannt nur die YAML-Header aller verfügbaren Skills (minimaler Token-Verbrauch)\[cite: 16].

2\. \[cite\_start]\*\*Matching\*\*: Erkennt Jarvis den Bedarf (z. B. "Optimiere SQL-Queries"), identifiziert der Librarian die passende Datei (z. B. `sql\_optimizer.md`)\[cite: 17].

3\. \[cite\_start]\*\*Injection\*\*: Erst jetzt wird der volle Inhalt in den Prompt des `@coder` geladen\[cite: 18].

4\. \[cite\_start]\*\*Execution\*\*: Der Agent führt die Befehle aus und entlädt den Skill danach wieder (\*\*Gesetz 3\*\*)\[cite: 19].



\---



\## 3. Strategischer Prompt: "The Skill Architect"

\[cite\_start]Dies ist die Instruktion, um neue Skills für Jarvis zu entwerfen, ohne Code zu schreiben\[cite: 20, 21, 22, 23, 24]:



> ### SYSTEM-PROMPT: Skill Architect

> \[cite\_start]\*\*Aufgabe\*\*: Erstelle eine neue `skill.md` basierend auf einer Benutzeranforderung\[cite: 24].

> 

> \*\*Richtlinien\*\*:

> \[cite\_start]1. \*\*ATOMARITÄT\*\*: Ein Skill löst genau EIN Problem (z. B. 'Python-Unit-Testing')\[cite: 25, 26].

> \[cite\_start]2. \*\*TOOL-BINDUNG\*\*: Definiere genau, welche MCP-Server oder Terminal-Befehle genutzt werden dürfen\[cite: 27].

> \[cite\_start]3. \*\*ERROR-HANDLING\*\*: Integriere Anweisungen für den Fall, dass ein Tool einen Fehler wirft\[cite: 28].

> 

> \[cite\_start]\*\*Gesetz der menschlichen Hoheit\*\*: Skills dürfen keine destruktiven Befehle (`rm`, `format`) ohne explizite Bestätigung im Monaco-Layer enthalten\[cite: 29].



\---



\## 4. Kategorisierung der Skills

| Kategorie | Skill-Beispiel | Ziel-Agent |

| :--- | :--- | :--- |

| \*\*Logic\*\* | `refactor\_logic\_v1.md` | `@coder` |

| \*\*DevOps\*\* | `docker\_orchestration.md` | `@tester` |

| \*\*Security\*\* | `owasp\_scanner\_logic.md` | `@security` |

| \*\*UX/UI\*\* | `accessibility\_checker.md` | `@ux\_agent` |

\[cite\_start]\[cite: 30, 31]



\---



\## 5. Integration mit MCP (Model Context Protocol)

\[cite\_start]Skills fungieren als die \*\*Logik-Schicht\*\* über den MCP-Servern\[cite: 32, 33]. \[cite\_start]Während der MCP-Server die Hardware-Anbindung (z. B. zu GitHub oder Slack) bereitstellt, sagt der Jarvis-Skill dem Agenten, wie er diese Anbindung strategisch klug nutzt\[cite: 33].



\---

\[cite\_start]\*\*Erstellt durch\*\*: The Architekt \[cite: 34]

