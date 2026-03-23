"""
Pytest configuration für Jarvis 4.0 Tests.
Registriert asyncio-Marker und setzt Umgebungsvariablen für Tests.
"""

import os
import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )


@pytest.fixture(autouse=True)
def _set_test_env(monkeypatch):
    """Inject safe test defaults so no real services are contacted."""
    monkeypatch.setenv("QDRANT_HOST", "localhost")
    monkeypatch.setenv("QDRANT_PORT", "6333")
    monkeypatch.setenv("QDRANT_COLLECTION", "jarvis_test")
    monkeypatch.setenv("CHROMA_HOST", "localhost")
    monkeypatch.setenv("CHROMA_PORT", "8001")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("EMBEDDING_MODEL", "bge-small-en-v1.5")
