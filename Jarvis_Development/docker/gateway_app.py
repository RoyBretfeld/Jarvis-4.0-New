"""
Jarvis Gateway — Privacy Filter & Reverse Proxy
Einziger Container mit Außennetz-Zugriff.
Filtert ausgehende Anfragen auf verbotene Muster (API-Keys, PII).
"""
from __future__ import annotations
import re
from fastapi import FastAPI, Request, Response
import httpx

app = FastAPI(title="Jarvis Gateway", version="4.0.0")

CORE_URL = "http://jarvis-core:8000"

# Patterns that must never leave the network
_BLOCK_PATTERNS = [
    re.compile(r"sk-[a-zA-Z0-9]{32,}"),          # OpenAI key
    re.compile(r"AKIA[A-Z0-9]{16}"),              # AWS key
    re.compile(r"password\s*[:=]\s*\S+", re.I),
]


def _is_clean(text: str) -> bool:
    return not any(p.search(text) for p in _BLOCK_PATTERNS)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "jarvis-gateway"}


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy(path: str, request: Request) -> Response:
    body = await request.body()
    if body and not _is_clean(body.decode("utf-8", errors="replace")):
        return Response(
            content='{"error":"Privacy filter blocked request"}',
            status_code=403,
            media_type="application/json",
        )
    async with httpx.AsyncClient(timeout=60) as client:
        url = f"{CORE_URL}/{path}"
        resp = await client.request(
            method=request.method,
            url=url,
            headers={k: v for k, v in request.headers.items() if k.lower() != "host"},
            content=body,
            params=dict(request.query_params),
        )
    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=dict(resp.headers),
        media_type=resp.headers.get("content-type"),
    )
