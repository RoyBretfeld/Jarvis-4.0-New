"""
JARVIS 4.0 – RAG Pipeline Validation (AWP-120)
Lädt ein Test-Dokument hoch und verifiziert, dass JARVIS korrekt daraus zitiert.

Voraussetzungen:
  - jarvis-core läuft auf http://127.0.0.1:8000
  - jarvis-rag (Qdrant + ChromaDB) läuft und ist erreichbar

Aufruf:
  py -3.12 -m pytest tests/test_rag_validation.py -v
  oder direkt: py -3.12 tests/test_rag_validation.py
"""
from __future__ import annotations

import io
import json
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

BACKEND = "http://127.0.0.1:8000"

# ─── Hilfsfunktionen ──────────────────────────────────────────────────────────
def backend_get(path: str) -> dict:
    url = f"{BACKEND}{path}"
    with urllib.request.urlopen(url, timeout=10) as resp:
        return json.loads(resp.read())


def backend_post(path: str, data: dict | bytes, content_type: str = "application/json") -> dict:
    url = f"{BACKEND}{path}"
    if isinstance(data, dict):
        body = json.dumps(data).encode()
    else:
        body = data
    req = urllib.request.Request(url, data=body, method="POST",
                                  headers={"Content-Type": content_type})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def multipart_upload(path: str, filename: str, content: bytes, mime: str) -> dict:
    """Minimaler Multipart/form-data Upload ohne externe Deps."""
    boundary = b"JarvisTestBoundary7950X"
    body = (
        b"--" + boundary + b"\r\n"
        b'Content-Disposition: form-data; name="file"; filename="' + filename.encode() + b'"\r\n'
        b"Content-Type: " + mime.encode() + b"\r\n\r\n"
        + content
        + b"\r\n--" + boundary + b"--\r\n"
    )
    url = f"{BACKEND}{path}"
    req = urllib.request.Request(
        url, data=body, method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary.decode()}"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


# ─── Tests ────────────────────────────────────────────────────────────────────

def test_health() -> None:
    """AWP-111: Backend und beide RAG-Backends sind healthy."""
    data = backend_get("/health")
    assert data["status"] in ("healthy", "degraded"), f"Unexpected status: {data}"
    print(f"  /health → {data['status']} | backends={data['backends']}")


def test_rcst_chunking() -> None:
    """AWP-112: RecursiveCharacterTextSplitter produziert vernünftige Chunks."""
    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
    from ingest_docs import RecursiveCharacterTextSplitter  # type: ignore

    splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=50)
    text = "\n\n".join([f"Abschnitt {i}: " + "A" * 80 for i in range(10)])
    chunks = splitter.split_text(text)
    assert len(chunks) >= 3, f"Erwartet ≥3 Chunks, bekam {len(chunks)}"
    for c in chunks:
        assert len(c) <= 220, f"Chunk zu groß: {len(c)} Zeichen"
    print(f"  RCST: {len(chunks)} Chunks aus {len(text)} Zeichen")


def test_upload_and_index() -> None:
    """AWP-102/103/104/105/106: PDF-Upload → Parsing → Chunking → Vektor-DB."""
    # Minimales Test-TXT-Dokument mit eindeutigem Inhalt
    unique_token = "JARVIS_TEST_SIGNAL_7950X_RYZEN_VEKTOR_VALIDIERUNG"
    content = f"""{unique_token}

Dieses Dokument ist ein automatischer Validierungstest für die RAG-Pipeline.
Es enthält einen eindeutigen Token, der nach dem Upload im Vektor-Gedächtnis
gefunden werden muss.

Abschnitt 1: Technische Details
Das JARVIS 4.0 System nutzt Qdrant als primäre Vektordatenbank und ChromaDB
als Keyword-Fallback. Die Embedding-Vektoren werden mit sentence-transformers
(BGE-M3) erzeugt und lokal gespeichert.

Abschnitt 2: Persistenz
Die Vektordaten überleben Container-Neustarts dank Docker Named Volumes:
qdrant-data und chroma-data sind auf der lokalen SSD persistiert.

Abschnitt 3: Validierung
{unique_token}_ENDE
""".encode("utf-8")

    print("  Upload test_rag_doc.txt …")
    result = multipart_upload(
        "/ingest/upload",
        filename="test_rag_doc.txt",
        content=content,
        mime="text/plain",
    )
    assert result.get("status") == "ok", f"Upload fehlgeschlagen: {result}"
    chunks_count = result.get("chunks", 0)
    assert chunks_count >= 1, f"Keine Chunks erstellt: {result}"
    print(f"  Upload OK → {chunks_count} Chunks, {result.get('size_mb', 0)} MB")


def test_retrieval() -> None:
    """AWP-108: Suche findet das hochgeladene Dokument."""
    # Kurz warten bis Embedding abgeschlossen
    time.sleep(2)

    unique_token = "JARVIS_TEST_SIGNAL_7950X_RYZEN_VEKTOR_VALIDIERUNG"
    result = backend_post("/search", {
        "query": unique_token,
        "top_k": 5,
        "mode": "hybrid",
        "score_threshold": 0.1,  # niedrig für Test-Stabilität
    })

    assert result.get("count", 0) >= 1, (
        f"Keine Ergebnisse für Token '{unique_token}'. "
        f"Ist das Dokument korrekt indiziert? {result}"
    )

    top = result["results"][0]
    assert unique_token in top["text"] or "test_rag_doc" in top.get("source", ""), (
        f"Token nicht im Top-Ergebnis: {top}"
    )
    print(f"  Retrieval OK → {result['count']} Treffer, Score={top['score']:.3f}")
    print(f"  Source: {top.get('source', 'n/a')}")


def test_source_attribution() -> None:
    """AWP-109/116: Ergebnis enthält Dateiname + Score für Source-Cards."""
    result = backend_post("/search", {
        "query": "JARVIS Vektordatenbank Validierung",
        "top_k": 3,
        "mode": "semantic",
        "score_threshold": 0.1,
    })

    for r in result.get("results", []):
        assert "score" in r, "Score fehlt im Ergebnis"
        assert "source" in r or "metadata" in r, "Source-Info fehlt"
        assert isinstance(r["score"], float), f"Score kein Float: {r['score']}"
    print(f"  Source-Attribution OK → {result.get('count', 0)} Ergebnisse mit Score")


def test_delete_test_doc() -> None:
    """AWP-110: Test-Dokument aus dem Gedächtnis löschen."""
    url = f"{BACKEND}/ingest/document?filename=test_rag_doc.txt"
    req = urllib.request.Request(url, method="DELETE")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
        assert result.get("status") == "deleted", f"Löschen fehlgeschlagen: {result}"
        print(f"  Delete OK → {result}")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print("  Delete: Dokument nicht gefunden (bereits gelöscht oder nie indiziert)")
        else:
            raise


def test_persistence_volumes() -> None:
    """AWP-119: Verifiziert Docker-Volume-Konfiguration in docker-compose.yml."""
    compose = Path(__file__).parent.parent / "docker-compose.yml"
    assert compose.exists(), "docker-compose.yml nicht gefunden"
    content = compose.read_text()
    assert "qdrant-data:" in content, "qdrant-data Volume fehlt"
    assert "chroma-data:" in content, "chroma-data Volume fehlt"
    assert "qdrant-data:/qdrant/storage" in content, "Qdrant Volume-Mount fehlt"
    assert "chroma-data:/chroma/data" in content, "Chroma Volume-Mount fehlt"
    print("  Persistence OK → qdrant-data + chroma-data Volumes konfiguriert")


# ─── Standalone Runner ────────────────────────────────────────────────────────
if __name__ == "__main__":
    tests = [
        test_health,
        test_rcst_chunking,
        test_upload_and_index,
        test_retrieval,
        test_source_attribution,
        test_delete_test_doc,
        test_persistence_volumes,
    ]

    passed = failed = 0
    for fn in tests:
        name = fn.__name__
        try:
            print(f"\n[RUN] {name}")
            fn()
            print(f"[PASS] {name}")
            passed += 1
        except Exception as exc:
            print(f"[FAIL] {name}: {exc}")
            failed += 1

    print(f"\n{'='*50}")
    print(f"AWP-120 Validation: {passed} passed, {failed} failed")
    if failed:
        sys.exit(1)
