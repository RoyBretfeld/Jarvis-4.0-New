# JARVIS 4.0 – Error Knowledge Base
# AWP-118: Context-Inference – wird automatisch bei Fehler-Queries geboostet

## Docker / Container

### chromadb ImportError: numpy.float_ removed
**Fehler:** `AttributeError: module 'numpy' has no attribute 'float_'`
**Ursache:** numpy ≥ 2.0 entfernte `np.float_`; chromadb 0.5.x setzt numpy 1.x voraus.
**Fix:** `pip install "numpy==1.26.4"` vor chromadb; in Dockerfile.core: `grep -v chroma-hnswlib | pip install && pip install numpy==1.26.4`

### ChromaDB startet nicht (supervisord)
**Fehler:** `ModuleNotFoundError: No module named 'chromadb.app'`
**Ursache:** Falscher CMD in supervisord.rag.conf: `python3 -m chromadb.app --host ...`
**Fix:** `uvicorn chromadb.app:app --host 0.0.0.0 --port 8001` mit env `IS_PERSISTENT=1,PERSIST_DIRECTORY=/chroma/data`

### jarvis-core Port 8000 nicht erreichbar
**Fehler:** `Connection refused` auf Host-Port 8000
**Ursache:** Container nur im `jarvis-internal` Netz (internal=true) → Docker Desktop publiziert dort keine Ports
**Fix:** jarvis-core zusätzlich in `jarvis-external` Netz aufnehmen (docker-compose.yml)

### PYTHONPATH ImportError (librarian, agents)
**Fehler:** `ModuleNotFoundError: No module named 'librarian'`
**Ursache:** API startet als `src.api_main:app` → `/app/src` nicht im Python-Pfad
**Fix:** `PYTHONPATH=/app/src` in Core-Environment (docker-compose.yml)

## RAG / Vektordatenbank

### Qdrant Connection refused
**Fehler:** `qdrant_client.http.exceptions.UnexpectedResponse` oder `Connection refused :6333`
**Ursache:** `QDRANT_HOST=localhost` in Core-Container — localhost = eigener Container, nicht jarvis-rag
**Fix:** `QDRANT_HOST=jarvis-rag` (Docker-Service-Name) in docker-compose Environment

### ChromaDB Connection refused
**Fehler:** `chromadb.errors.ChromaError: Could not connect to tenant`
**Ursache:** `CHROMA_HOST=localhost` statt `jarvis-rag`
**Fix:** `CHROMA_HOST=jarvis-rag`, `CHROMA_PORT=8001`

### state.json not found
**Fehler:** `404 state.json not found`
**Ursache:** Dockerfile.core kopierte state.json nicht ins Image
**Fix:** Volume-Mount `./state.json:/app/state.json:ro` in docker-compose.yml

### Sentence-Transformers lädt externes Modell
**Fehler:** Langsamer Start, Netzwerkzugriff beim ersten Embedding
**Ursache:** Model-Cache nicht persistiert
**Fix:** `HF_HOME=/app/data/hf_cache`, `TRANSFORMERS_CACHE=/app/data/hf_cache` + Volume `core-data:/app/data`

## Next.js / Frontend

### CORS-Fehler bei DELETE /ingest/document
**Fehler:** `CORS preflight blocked – method DELETE not allowed`
**Ursache:** FastAPI CORS-Middleware mit `allow_methods=["GET","POST","OPTIONS"]` – DELETE fehlte
**Fix:** `allow_methods=["GET","POST","DELETE","OPTIONS"]` in api_main.py

### Chat-Streaming bricht ab
**Fehler:** Stream endet vorzeitig oder Response leer
**Ursache:** GROQ_API_KEY nicht gesetzt / abgelaufen
**Fix:** `.env.local` mit `GROQ_API_KEY=gsk_...` im `/src/ui/` Verzeichnis

### Monaco Editor lädt nicht
**Fehler:** Leere Editorbox, keine Syntax-Highlighting
**Ursache:** Monaco WebWorker-Dateien fehlen / CSP blockiert
**Fix:** In `next.config.js`: `webpack(cfg) { cfg.module.rules.push({ test: /\.ttf$/, type: 'asset/resource' }); return cfg; }`

## Python / Laufzeit

### asyncio.get_event_loop() DeprecationWarning
**Fehler:** `DeprecationWarning: There is no current event loop`
**Ursache:** Python 3.10+ deprecates `get_event_loop()` outside async context
**Fix:** `asyncio.get_running_loop()` statt `asyncio.get_event_loop()` in async-Kontext

### ProcessPoolExecutor zerstört Qdrant-Verbindung
**Fehler:** Qdrant antwortet nicht nach Embedding
**Ursache:** Fork-basierter ProcessPoolExecutor vererbt Socket-FDs an Worker-Prozesse
**Fix:** `ThreadPoolExecutor` (kein Fork) für Embedding nutzen — `embed_async()` in memory_interface.py
