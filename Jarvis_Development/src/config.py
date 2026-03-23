"""
AWP-057 – Central Config (Audit Fix: de-duplicate os.environ reads)
Single source of truth for all environment variables.
All modules import from here instead of calling os.environ directly.
"""

from __future__ import annotations

import os
from pathlib import Path

# ── Project ───────────────────────────────────────────────────────────────
PROJECT_ROOT  = Path(__file__).parent.parent.resolve()
LOG_DIR       = PROJECT_ROOT / "logs"
DATA_DIR      = PROJECT_ROOT / "data" / "rag"
SKILLS_DIR    = PROJECT_ROOT / "skills"
STRATEGY_DIR  = PROJECT_ROOT / "strategy"

# ── Ollama ────────────────────────────────────────────────────────────────
OLLAMA_BASE_URL  = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL     = os.environ.get("OLLAMA_MODEL_DEFAULT", "mistral")
OLLAMA_TIMEOUT   = int(os.environ.get("OLLAMA_TIMEOUT_SECONDS", "120"))

# ── RAG / Vector DB ───────────────────────────────────────────────────────
QDRANT_HOST       = os.environ.get("QDRANT_HOST", "localhost")
QDRANT_PORT       = int(os.environ.get("QDRANT_PORT", "6333"))
QDRANT_COLLECTION = os.environ.get("QDRANT_COLLECTION", "jarvis_knowledge")
CHROMA_HOST       = os.environ.get("CHROMA_HOST", "localhost")
CHROMA_PORT       = int(os.environ.get("CHROMA_PORT", "8001"))
EMBEDDING_MODEL   = os.environ.get("EMBEDDING_MODEL", "bge-small-en-v1.5")
RAG_CHUNK_SIZE    = int(os.environ.get("RAG_CHUNK_SIZE", "1000"))
RAG_CHUNK_OVERLAP = int(os.environ.get("RAG_CHUNK_OVERLAP", "100"))

# ── API ───────────────────────────────────────────────────────────────────
CORE_API_HOST = os.environ.get("CORE_API_HOST", "127.0.0.1")
CORE_API_PORT = int(os.environ.get("CORE_API_PORT", "8000"))
DOCKER_HOST   = os.environ.get("DOCKER_HOST", "http://localhost:2375")

# ── Heartbeat ─────────────────────────────────────────────────────────────
HEARTBEAT_INTERVAL  = int(os.environ.get("HEARTBEAT_INTERVAL", "30"))
HEARTBEAT_SELF_HEAL = os.environ.get("HEARTBEAT_SELF_HEAL", "true").lower() == "true"

# ── Storage ───────────────────────────────────────────────────────────────
SSD1_MOUNT = os.environ.get("SSD1_MOUNT", "C:/")
SSD2_MOUNT = os.environ.get("SSD2_MOUNT", "E:/")

# ── Features ──────────────────────────────────────────────────────────────
TTS_ENABLED      = os.environ.get("TTS_ENABLED", "true").lower() == "true"
NOTIFY_ENABLED   = os.environ.get("NOTIFY_ENABLED", "true").lower() == "true"
DEBATE_MAX_ROUNDS = int(os.environ.get("DEBATE_MAX_ROUNDS", "3"))
EMBED_WORKERS    = int(os.environ.get("EMBED_WORKERS", "4"))
