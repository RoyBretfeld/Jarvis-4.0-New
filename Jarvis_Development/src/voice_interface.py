"""
AWP-075 – Voice Command Interface
Faster-Whisper für lokale Speech-to-Text → Jarvis Command Parser.

Pipeline:
  1. Record audio chunk (sounddevice / PyAudio)
  2. Transcribe via faster-whisper (local, CPU/GPU)
  3. Match against known commands → dispatch to API
  4. TTS response via tts_engine.py

Wake word: "Jarvis" (configurable)

Python 3.12 | AsyncIO | Threading
"""

from __future__ import annotations

import asyncio
import logging
import queue
import re
import threading
from dataclasses import dataclass
from typing import Any

import httpx

log = logging.getLogger("jarvis.voice_interface")

WAKE_WORD      = __import__("os").environ.get("WAKE_WORD", "jarvis").lower()
SAMPLE_RATE    = 16000
CHUNK_SECONDS  = 3.0       # record window after wake word detection
WHISPER_MODEL  = __import__("os").environ.get("WHISPER_MODEL", "base")
API_BASE       = "http://localhost:8000"


@dataclass
class VoiceCommand:
    transcript: str
    command: str           # matched command key or "unknown"
    args: dict[str, str]   # extracted arguments
    confidence: float


# ── Command patterns ────────────────────────────────────────────────────────

COMMAND_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("status",   re.compile(r"\b(status|wie geht|health)\b", re.I)),
    ("search",   re.compile(r"\b(suche?|search|find|finde?)\s+(.+)", re.I)),
    ("ingest",   re.compile(r"\b(ingest|import|lade)\s+(.+)", re.I)),
    ("stop",     re.compile(r"\b(stop|halt|cancel|abbruch)\b", re.I)),
    ("commit",   re.compile(r"\b(commit|speichere?|save)\b", re.I)),
    ("help",     re.compile(r"\b(help|hilfe|was kannst)\b", re.I)),
]


def _parse_command(transcript: str) -> VoiceCommand:
    for key, pattern in COMMAND_PATTERNS:
        m = pattern.search(transcript)
        if m:
            args = {}
            if m.lastindex and m.lastindex >= 2:
                args["query"] = m.group(2).strip()
            return VoiceCommand(
                transcript=transcript,
                command=key,
                args=args,
                confidence=0.9,
            )
    return VoiceCommand(transcript=transcript, command="unknown", args={}, confidence=0.5)


# ── Whisper transcription ───────────────────────────────────────────────────

def _transcribe_sync(audio_data: Any) -> str:
    """Run faster-whisper transcription (blocking, in executor)."""
    try:
        from faster_whisper import WhisperModel  # type: ignore
        model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
        segments, _ = model.transcribe(audio_data, language="de", beam_size=3)
        return " ".join(s.text for s in segments).strip()
    except ImportError:
        log.warning("faster-whisper not installed")
        return ""
    except Exception as exc:
        log.error("Transcription error: %s", exc)
        return ""


# ── Audio recording ─────────────────────────────────────────────────────────

def _record_chunk_sync(seconds: float) -> Any:
    """Record audio from microphone (blocking)."""
    try:
        import numpy as np  # type: ignore
        import sounddevice as sd  # type: ignore
        audio = sd.rec(
            int(seconds * SAMPLE_RATE),
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
        )
        sd.wait()
        return audio.flatten()
    except ImportError:
        log.warning("sounddevice/numpy not installed — voice unavailable")
        return None
    except Exception as exc:
        log.error("Recording error: %s", exc)
        return None


# ── Command dispatcher ──────────────────────────────────────────────────────

async def _dispatch(cmd: VoiceCommand) -> str:
    """Send voice command to Jarvis API and return response text."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            if cmd.command == "status":
                resp = await client.get(f"{API_BASE}/status")
                data = resp.json()
                return f"Jarvis läuft. Aura: {data.get('aura', 'unknown')}."

            elif cmd.command == "search":
                query = cmd.args.get("query", "")
                resp = await client.get(f"{API_BASE}/search", params={"q": query, "limit": 3})
                data = resp.json()
                hits = data.get("hits", [])
                if hits:
                    return f"Gefunden: {hits[0].get('content', '')[:100]}"
                return "Keine Ergebnisse gefunden."

            elif cmd.command == "help":
                return ("Verfügbare Befehle: Status, Suche, Stop, Commit, Ingest. "
                        "Sage den Befehl nach dem Weckwort Jarvis.")

            elif cmd.command == "stop":
                return "Verstanden. Stoppe aktuellen Prozess."

            else:
                return f"Befehl '{cmd.transcript}' nicht erkannt."
    except Exception as exc:
        log.error("Dispatch error: %s", exc)
        return "API nicht erreichbar."


# ── Main voice loop ─────────────────────────────────────────────────────────

class VoiceInterface:
    """Continuous listen → transcribe → dispatch loop."""

    def __init__(self) -> None:
        self._running = False
        self._loop: asyncio.AbstractEventLoop | None = None

    async def start(self) -> None:
        """Start the voice interface listen loop."""
        self._running = True
        self._loop = asyncio.get_event_loop()
        log.info("Voice interface started (wake word: '%s')", WAKE_WORD)

        try:
            from tts_engine import speak  # type: ignore
            await speak(f"Jarvis Spracheingabe aktiv.")
        except Exception:
            pass

        while self._running:
            await self._listen_once()

    async def stop(self) -> None:
        self._running = False

    async def _listen_once(self) -> None:
        """Record one chunk, check for wake word, dispatch if found."""
        assert self._loop is not None
        audio = await self._loop.run_in_executor(None, _record_chunk_sync, CHUNK_SECONDS)
        if audio is None:
            await asyncio.sleep(1)
            return

        transcript = await self._loop.run_in_executor(None, _transcribe_sync, audio)
        if not transcript:
            return

        log.debug("Heard: %s", transcript)

        if WAKE_WORD not in transcript.lower():
            return

        # Strip wake word from command
        clean = re.sub(rf"\b{re.escape(WAKE_WORD)}\b", "", transcript, flags=re.I).strip()
        log.info("Voice command: %s", clean)

        cmd = _parse_command(clean)
        response = await _dispatch(cmd)
        log.info("Voice response: %s", response)

        try:
            from tts_engine import speak  # type: ignore
            await speak(response)
        except Exception:
            pass


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(VoiceInterface().start())
