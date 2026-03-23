"""
JARVIS 4.0 – VLM Scanner
Scannt Seiten-Bilder aus PDFs mit einem lokalen Vision-Modell (Ollama).
Bevorzugt llava, Fallback auf moondream, sonst text-only.
Python 3.12 | aiohttp | Ollama API
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Optional

import aiohttp

log = logging.getLogger("jarvis.vlm_scanner")

OLLAMA_BASE = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
VLM_PREFERRED = os.environ.get("VLM_MODEL", "llava:latest")
VLM_FALLBACK = "moondream:latest"
VLM_TIMEOUT = 60  # Sekunden pro Bild

VLM_PROMPT = (
    "Beschreibe präzise den Inhalt dieses Bildes aus einem Dokument. "
    "Extrahiere Tabellen, Diagramme, Grafiken und wichtige Texte vollständig. "
    "Antworte auf Deutsch. Sei strukturiert und vollständig."
)

_available_vlm: Optional[str] = None


async def _detect_vlm() -> Optional[str]:
    """Prüft welches Vision-Modell in Ollama verfügbar ist."""
    global _available_vlm
    if _available_vlm is not None:
        return _available_vlm
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{OLLAMA_BASE}/api/tags",
                                   timeout=aiohttp.ClientTimeout(total=5)) as resp:
                data = await resp.json()
                names = [m["name"] for m in data.get("models", [])]
                for candidate in [VLM_PREFERRED, VLM_FALLBACK]:
                    if candidate in names:
                        _available_vlm = candidate
                        log.info("VLM model detected: %s", candidate)
                        return candidate
    except Exception as exc:
        log.warning("VLM detection failed: %s", exc)
    _available_vlm = ""
    log.warning("No vision model available – skipping VLM scan")
    return None


async def describe_image(image_b64: str) -> str:
    """
    Ruft Ollama VLM mit einem base64-Bild auf.
    Gibt die Beschreibung zurück oder "" bei Fehler.
    """
    model = await _detect_vlm()
    if not model:
        return ""

    payload = {
        "model": model,
        "prompt": VLM_PROMPT,
        "images": [image_b64],
        "stream": False,
        "options": {"temperature": 0.2, "num_predict": 512},
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{OLLAMA_BASE}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=VLM_TIMEOUT),
            ) as resp:
                if resp.status != 200:
                    log.warning("VLM error HTTP %d", resp.status)
                    return ""
                data = await resp.json()
                description = data.get("response", "").strip()
                log.debug("VLM description (%d chars)", len(description))
                return description
    except asyncio.TimeoutError:
        log.warning("VLM timeout after %ds", VLM_TIMEOUT)
        return ""
    except Exception as exc:
        log.error("VLM call failed: %s", exc)
        return ""


async def scan_page_images(images_b64: list[str], max_images: int = 3) -> str:
    """
    Scannt bis zu max_images Bilder einer Seite und kombiniert die Beschreibungen.
    Limitiert auf max_images um Laufzeit zu kontrollieren.
    """
    if not images_b64:
        return ""

    tasks = [describe_image(img) for img in images_b64[:max_images]]
    descriptions = await asyncio.gather(*tasks)
    combined = "\n\n".join(d for d in descriptions if d)
    return combined
