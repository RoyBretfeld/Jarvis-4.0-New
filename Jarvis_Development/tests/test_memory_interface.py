"""
Tests für src/memory_interface.py
Nutzt Mocks – kein laufendes Qdrant/ChromaDB erforderlich.
pytest 8.x | Python 3.12
"""

import sys
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from memory_interface import (
    Document,
    SearchResult,
    JarvisMemory,
    QdrantMemory,
    ChromaMemory,
    embed,
    _get_encoder,
)


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def make_doc(text: str = "test text", **meta) -> Document:
    return Document.from_text(text=text, metadata={"source": "test.md", **meta})


def make_result(doc_id: str, score: float, source: str = "qdrant") -> SearchResult:
    doc = Document(doc_id=doc_id, text=f"text for {doc_id}", metadata={}, score=score)
    return SearchResult(document=doc, source=source, score=score)


# ─────────────────────────────────────────────
# Document
# ─────────────────────────────────────────────
class TestDocument:
    def test_from_text_generates_uuid(self):
        d1 = Document.from_text("hello", {})
        d2 = Document.from_text("hello", {})
        assert d1.doc_id != d2.doc_id

    def test_metadata_stored(self):
        doc = Document.from_text("x", {"key": "value"})
        assert doc.metadata["key"] == "value"

    def test_default_score_zero(self):
        doc = Document.from_text("x", {})
        assert doc.score == 0.0


# ─────────────────────────────────────────────
# embed (mocked SentenceTransformer)
# ─────────────────────────────────────────────
class TestEmbed:
    def test_returns_list_of_floats(self):
        mock_model = MagicMock()
        mock_model.encode.return_value = MagicMock(tolist=lambda: [0.1] * 384)
        with patch("memory_interface._encoder", mock_model):
            result = embed("test query")
        assert isinstance(result, list)
        assert len(result) == 384


# ─────────────────────────────────────────────
# QdrantMemory (mocked qdrant_client)
# ─────────────────────────────────────────────
class TestQdrantMemory:
    @pytest.fixture
    def mock_client(self):
        client = MagicMock()
        client.get_collections.return_value = MagicMock(collections=[])
        return client

    def test_health_returns_false_when_unreachable(self):
        qm = QdrantMemory()
        # No client set, import will fail in test env → health = False
        with patch.dict("sys.modules", {"qdrant_client": None}):
            assert qm.health() is False

    @pytest.mark.asyncio
    async def test_upsert_empty_list_returns_zero(self):
        qm = QdrantMemory()
        result = await qm.upsert([])
        assert result == 0

    @pytest.mark.asyncio
    async def test_search_returns_list(self):
        qm = QdrantMemory()
        mock_client = MagicMock()
        mock_client.search.return_value = []
        qm._client = mock_client

        with patch("memory_interface.embed_async", new=AsyncMock(return_value=[0.0] * 384)):
            results = await qm.search("query")
        assert results == []


# ─────────────────────────────────────────────
# JarvisMemory – Hybrid Search logic
# ─────────────────────────────────────────────
class TestJarvisMemoryHybridSearch:
    @pytest.mark.asyncio
    async def test_hybrid_deduplication_prefers_higher_score(self):
        memory = JarvisMemory()

        shared_id = "doc-shared"
        qdrant_result = make_result(shared_id, score=0.9, source="qdrant")
        chroma_result = make_result(shared_id, score=0.6, source="chroma")
        unique_result = make_result("doc-unique", score=0.7, source="chroma")

        memory.qdrant.search = AsyncMock(return_value=[qdrant_result])
        memory.chroma.search = AsyncMock(return_value=[chroma_result, unique_result])

        results = await memory.search("test query", mode="hybrid")

        # shared_id should appear once with the higher score
        ids = [r.document.doc_id for r in results]
        assert ids.count(shared_id) == 1
        shared = next(r for r in results if r.document.doc_id == shared_id)
        assert shared.score == 0.9

    @pytest.mark.asyncio
    async def test_semantic_mode_only_calls_qdrant(self):
        memory = JarvisMemory()
        memory.qdrant.search = AsyncMock(return_value=[make_result("a", 0.8)])
        memory.chroma.search = AsyncMock(return_value=[])

        await memory.search("q", mode="semantic")

        memory.qdrant.search.assert_called_once()
        memory.chroma.search.assert_not_called()

    @pytest.mark.asyncio
    async def test_keyword_mode_only_calls_chroma(self):
        memory = JarvisMemory()
        memory.qdrant.search = AsyncMock(return_value=[])
        memory.chroma.search = AsyncMock(return_value=[make_result("b", 0.7)])

        await memory.search("q", mode="keyword")

        memory.chroma.search.assert_called_once()
        memory.qdrant.search.assert_not_called()

    @pytest.mark.asyncio
    async def test_results_sorted_by_score_descending(self):
        memory = JarvisMemory()
        results = [
            make_result("c", 0.5),
            make_result("a", 0.9),
            make_result("b", 0.7),
        ]
        memory.qdrant.search = AsyncMock(return_value=results)
        memory.chroma.search = AsyncMock(return_value=[])

        output = await memory.search("q", mode="hybrid")
        scores = [r.score for r in output]
        assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_top_k_respected(self):
        memory = JarvisMemory()
        many = [make_result(f"doc-{i}", score=float(i) / 10) for i in range(10)]
        memory.qdrant.search = AsyncMock(return_value=many)
        memory.chroma.search = AsyncMock(return_value=[])

        output = await memory.search("q", mode="hybrid", top_k=3)
        assert len(output) <= 3

    def test_health_returns_dict_with_backends(self):
        memory = JarvisMemory()
        memory.qdrant.health = MagicMock(return_value=True)
        memory.chroma.health = MagicMock(return_value=False)
        result = memory.health()
        assert result == {"qdrant": True, "chroma": False}

    @pytest.mark.asyncio
    async def test_upsert_calls_both_backends(self):
        memory = JarvisMemory()
        memory.qdrant.upsert = AsyncMock(return_value=2)
        memory.chroma.upsert = AsyncMock(return_value=2)

        docs = [make_doc(), make_doc()]
        counts = await memory.upsert(docs)

        memory.qdrant.upsert.assert_called_once_with(docs)
        memory.chroma.upsert.assert_called_once_with(docs)
        assert counts == {"qdrant": 2, "chroma": 2}
