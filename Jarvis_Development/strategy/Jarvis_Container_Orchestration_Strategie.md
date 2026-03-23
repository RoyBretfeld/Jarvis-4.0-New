\---

name: "Jarvis Container Orchestration"

type: "Strategisches Protokoll"

version: "1.0.0"

status: "Finalisiert"

\---



\# \[cite\_start]🏗️ Jarvis Container Orchestration - Strategisches Protokoll \[cite: 69]



\[cite\_start]Dieses Dokument definiert die Isolations- und Deployment-Strategie für das Jarvis-Ökosystem unter Nutzung von Docker/Podman auf der Ryzen 9 Architektur. \[cite: 70]



\---



\## \[cite\_start]1. Die Container-Topologie (The Modular Core) \[cite: 71]

\[cite\_start]Jarvis wird in vier logische Sicherheitszonen unterteilt, um maximale Stabilität und Sicherheit zu gewährleisten: \[cite: 72]



| Container-ID | Name | Funktion | Ressourcen-Limit |

| :--- | :--- | :--- | :--- |

| \*\*jarvis-core\*\* | The Brain | \[cite\_start]UI (Monaco), API-Routing \& Chat-Logik. \[cite: 73] | \[cite\_start]2 Kerne / 4GB RAM \[cite: 73] |

| \*\*jarvis-rag\*\* | The Memory | \[cite\_start]Qdrant/ChromaDB \& lokaler Embedding-Dienst. \[cite: 73] | \[cite\_start]4 Kerne / 8GB RAM \[cite: 73] |

| \*\*jarvis-gateway\*\* | The Border | \[cite\_start]Privacy-Filter \& Cloud-Verschlüsselung. \[cite: 73] | \[cite\_start]2 Kerne / 2GB RAM \[cite: 73] |

| \*\*jarvis-sandbox\*\* | The Workshop | \[cite\_start]OpenShell-Runtime für Agenten-Execution. \[cite: 73] | \[cite\_start]8 Kerne / 16GB RAM \[cite: 73] |



\---



\## \[cite\_start]2. Strategischer Prompt: "The DevOps Architect" \[cite: 74]

\[cite\_start]Instruktion für das Setup der Umgebung und die Ausarbeitung der Konfiguration: \[cite: 75]



> \[cite\_start]### SYSTEM-PROMPT: DevOps Architect \[cite: 76]

> \[cite\_start]\*\*Rolle\*\*: Experte für Container-Sicherheit und Hochleistungs-Infrastruktur. \[cite: 77]

> \[cite\_start]\*\*Aufgabe\*\*: Entwurf der Docker-Compose-Struktur für Jarvis. \[cite: 78]

> 

> \[cite\_start]\*\*Spezifikationen\*\*: \[cite: 79]

> 1. \*\*NETZWERK\*\*: Erstelle ein isoliertes internes Netzwerk 'jarvis-internal'. \[cite\_start]Nur das 'jarvis-gateway' hat Zugriff auf das externe Internet (Cloud-Reasoning). \[cite: 80]

> \[cite\_start]2. \*\*VOLUMES\*\*: Nutze dedizierte SSD-Mounts für die Vektor-DB, um I/O-Wait-Zeiten zu minimieren. \[cite: 81]

> 3. \*\*REVIDIERBARKEIT\*\*: Konfiguriere 'Health-Checks'. \[cite\_start]Falls ein Agent-Container hängt, muss er automatisch neu gestartet werden (State-Recovery via SSD-Cache). \[cite: 82]

> 

> \[cite\_start]\*\*Gesetz der Transparenz\*\*: Alle Container-Logs müssen an den 'jarvis-core' gestreamt werden, um sie in der IDE-Sidebar anzuzeigen. \[cite: 83]



\---



\## \[cite\_start]3. Sentinel-Härtung (Security Layer) \[cite: 84]

\* \[cite\_start]\*\*Rootless-Mode\*\*: Alle Container laufen im "Rootless"-Modus, um Privilegieneskalation zu verhindern. \[cite: 85]

\* \[cite\_start]\*\*AMD-V Integration\*\*: Wir nutzen die Hardware-Virtualisierung des Ryzen, um die `jarvis-sandbox` zusätzlich durch gVisor oder Kata Containers vom Host-Kernel zu isolieren. \[cite: 86]

\* \[cite\_start]\*\*No-Persistence\*\*: Der Sandbox-Container wird nach jedem größeren Coding-Task per `docker-compose down --volumes` bereinigt, um "Configuration Drift" zu vermeiden. \[cite: 87]



\---



\## \[cite\_start]4. Ressourcen-Management (Ryzen Optimization) \[cite: 88]

\[cite\_start]Nutzung von CPU-Sets, um sicherzustellen, dass das RAG-System niemals die UI-Reaktionszeit (Monaco) beeinträchtigt: \[cite: 89]



\* \[cite\_start]\*\*cpuset-cpus: "0-1"\*\*: Reserviert für den Core-Container. \[cite: 90]

\* \[cite\_start]\*\*cpuset-cpus: "4-7"\*\*: Reserviert für das RAG-System (Parallel Processing von Embeddings). \[cite: 91]

\* \[cite\_start]\*\*cpuset-cpus: "8-15"\*\*: Reserviert für die Sandbox (High-Speed Testing). \[cite: 92]



\---

\[cite\_start]\*\*Status\*\*: Container-Strategie finalisiert. \[cite: 93]

\[cite\_start]\*\*Erstellt durch\*\*: The Architekt \[cite: 93]

