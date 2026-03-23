"""
AWP-058 – OpenAPI/Swagger Documentation Metadata
FastAPI auto-generates /docs and /redoc from this + endpoint decorators.
"""

TAGS_METADATA = [
    {
        "name": "System",
        "description": "Health checks, status, system metrics (CPU threads, RAM, disk).",
    },
    {
        "name": "RAG",
        "description": "Semantic and hybrid search over the knowledge base. "
                       "Ingest new documents into Qdrant + ChromaDB.",
    },
    {
        "name": "Skills",
        "description": "List and inspect loaded Skill definitions from `/skills/*.md`.",
    },
    {
        "name": "Agents",
        "description": "Dispatch tasks to @coder, @tester, @security agents. "
                       "Trigger the Coder→Tester→Security pipeline.",
    },
    {
        "name": "Files",
        "description": "Browse project files and read content (path-restricted to PROJECT_ROOT).",
    },
    {
        "name": "WebSockets",
        "description": (
            "Real-time streams:\n"
            "- `/ws/logs`: JSON log lines broadcast to all connected clients.\n"
            "- `/ws/terminal`: Interactive PTY shell in jarvis-sandbox.\n"
            "- `/ws/system`: System metrics (CPU threads, RAM) at 1-second intervals."
        ),
    },
]

API_INFO = {
    "title": "Jarvis 4.0 Core API",
    "version": "4.0.0",
    "description": (
        "Internal API for the Jarvis 4.0 AI development environment.\n\n"
        "**Security:** All endpoints are bound to `127.0.0.1` only. "
        "No external network exposure.\n\n"
        "**RB-Protokoll:** All actions are logged. "
        "Critical operations require explicit confirmation.\n\n"
        "**Hardware:** Optimized for AMD Ryzen 9 7950X (32 threads)."
    ),
    "contact": {
        "name": "The Architekt",
        "url": "https://github.com/jarvis-4.0",
    },
    "license_info": {
        "name": "Private – All rights reserved",
    },
}
