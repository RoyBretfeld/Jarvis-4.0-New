# Jarvis 4.0 – Developer Documentation
**Phase 2 Complete | Stand: 2026-03-20**

---

## Architektur-Übersicht

```
Jarvis_Development/
├── src/
│   ├── heartbeat.py        AWP-005  Docker & Ollama Health Monitor
│   ├── librarian.py        AWP-011  Skill .md Parser (YAML-Frontmatter)
│   ├── memory_interface.py AWP-012/014  Qdrant + ChromaDB Interface
│   ├── ingest_docs.py      AWP-013/018  Ingestion Pipeline (Multiprocessing)
│   ├── jarvis_shell.py     AWP-015  CLI (Developer / System Mode)
│   └── api_main.py         AWP-017  FastAPI Core Server
├── tests/
│   ├── conftest.py                  Pytest-Konfiguration, ENV-Mocks
│   ├── test_librarian.py   AWP-016  Unit-Tests für Librarian
│   └── test_memory_interface.py     Unit-Tests für Memory Interface
├── docker/
│   ├── qdrant.yml          AWP-007  Qdrant Konfiguration
│   ├── chromadb.yml        AWP-007  ChromaDB Konfiguration
│   ├── logging.yml         AWP-008  Fluent Bit Aggregator
│   └── fluent-bit.conf     AWP-008  Log-Routing-Regeln
├── docker-compose.yml      AWP-003  4-Zonen Container Stack
├── .env                    AWP-004  Environment (keine Secrets)
├── state.json                       AWP-Status-Tracking
├── skills/                          Skill-Definitionen (.md)
├── strategy/                        Architektur-Dokumente (.md)
├── data/rag/                        RAG-Input-Daten
├── config/                          Container-Konfigurationen
└── logs/                            Zentrale Log-Ablage
```

---

## Container-Stack (Ryzen 9 7950X CPU-Zuweisung)

| Container        | Funktion              | Threads   | RAM   |
|------------------|-----------------------|-----------|-------|
| `jarvis-core`    | API + UI (Monaco)     | 0–1       | 4 GB  |
| `jarvis-gateway` | Privacy-Filter        | 2–3       | 2 GB  |
| `jarvis-rag`     | Qdrant + ChromaDB     | 4–7       | 8 GB  |
| `jarvis-sandbox` | Agent-Execution       | 8–15      | 16 GB |

Alle Container laufen im **Rootless-Modus**. Nur `jarvis-gateway` hat externen Internetzugriff.

---

## Schnellstart

### 1. Environment einrichten
```bash
cp .env .env.local
# SSD-Mounts und Ollama-URL in .env.local anpassen
```

### 2. Docker Stack starten
```bash
docker compose up -d jarvis-rag jarvis-gateway
```

### 3. Dokumente indexieren
```bash
cd src
python ingest_docs.py ../strategy
```

### 4. API starten
```bash
cd src
python api_main.py
# → http://127.0.0.1:8000/docs
```

### 5. Shell starten
```bash
python src/jarvis_shell.py --dev       # Entwickler-Modus
python src/jarvis_shell.py --system    # System-Modus (read-only)
```

### 6. Heartbeat (einmalig)
```bash
python src/heartbeat.py --once
# Exit 0 = healthy, Exit 1 = unhealthy
```

---

## Tests ausführen

```bash
pip install pytest pytest-asyncio
pytest tests/ -v
```

**Anforderungen für Tests:** Kein laufendes Backend nötig – alle externen Calls werden gemockt.

---

## API-Endpunkte

| Method | Path       | Beschreibung                          |
|--------|------------|---------------------------------------|
| GET    | `/health`  | Backend-Status (Qdrant, ChromaDB)     |
| GET    | `/status`  | Aktueller state.json Inhalt           |
| POST   | `/search`  | Hybrid-Suche im RAG-Gedächtnis        |
| POST   | `/ingest`  | Ingestion-Pipeline starten            |
| GET    | `/skills`  | Liste aller geladenen Skills          |

---

## Dependency-Übersicht

```
# Produktiv
fastapi>=0.111
uvicorn[standard]>=0.29
qdrant-client>=1.9
chromadb>=0.5
sentence-transformers>=3.0
aiohttp>=3.9
pydantic>=2.7

# Tests
pytest>=8.0
pytest-asyncio>=0.23
```

> **Nächster Schritt:** `pip freeze > requirements.txt` nach Installation ausführen.

---

## Offene Punkte (Phase 3)

- [ ] `AWP-021` Dockerfiles erstellen (4×)
- [ ] `AWP-022` Git-Init + `.gitignore` (`.env` ausschließen!)
- [ ] `AWP-023` `requirements.txt` + `pip-audit` in CI
- [ ] `AWP-024` ChromaDB TokenAuth aktivieren (`docker/chromadb.yml`)
- [ ] `AWP-025` TLS-Termination für `jarvis-gateway`
- [ ] `AWP-026` Monaco-Editor-Frontend anbinden

---

## RB-Protokoll – Die 4 Gesetze

1. **Transparenz (Glass-Box):** Alle Aktionen werden geloggt (`logs/`).
2. **Revidierbarkeit (Undo is King):** Keine destruktiven Operationen ohne Backup/Versionierung.
3. **Progressive Offenlegung:** API gibt minimale Daten zurück, Details auf Anfrage.
4. **Menschliche Hoheit:** Shell fordert Bestätigung vor Schreiboperationen.

---

*Erstellt durch: Claude Sonnet 4.6 (Lead Developer) | Autorisiert: The Architekt*
