"""
AWP-054 – Local TTS Engine
Optionale lokale Text-to-Speech für Jarvis-Statusmeldungen.
Backend-Priorität:
  1. Piper TTS (lokal, schnell, Deutsch/Englisch)
  2. Coqui TTS (lokal, hohe Qualität)
  3. pyttsx3 (Windows SAPI5 / espeak, immer verfügbar)
  4. Stummfall: nur Logging

Kein Cloud-TTS – Privacy First (kein unverschlüsseltes Verlassen der Umgebung).
Python 3.12 | AsyncIO
"""

from __future__ import annotations

import asyncio
import logging
import os
import queue
import threading
from pathlib import Path
from typing import Literal

log = logging.getLogger("jarvis.tts")

TTS_BACKEND  = os.environ.get("TTS_BACKEND", "auto")   # piper | coqui | pyttsx3 | none
TTS_VOICE    = os.environ.get("TTS_VOICE", "de_DE-thorsten-high")
TTS_RATE     = int(os.environ.get("TTS_RATE", "165"))   # words per minute (pyttsx3)
TTS_ENABLED  = os.environ.get("TTS_ENABLED", "true").lower() == "true"
PIPER_PATH   = Path(os.environ.get("PIPER_PATH", "piper"))
TTS_SPEAKER  = int(os.environ.get("TTS_SPEAKER_ID", "0"))  # Thorsten: speaker_id=0


# ─────────────────────────────────────────────
# Backend detection
# ─────────────────────────────────────────────

def _detect_backend() -> str:
    if TTS_BACKEND != "auto":
        return TTS_BACKEND
    if PIPER_PATH.exists() or _which("piper"):
        return "piper"
    try:
        import TTS  # type: ignore  # noqa: F401
        return "coqui"
    except ImportError:
        pass
    try:
        import pyttsx3  # type: ignore  # noqa: F401
        return "pyttsx3"
    except ImportError:
        pass
    return "none"


def _which(cmd: str) -> bool:
    import shutil
    return shutil.which(cmd) is not None


# ─────────────────────────────────────────────
# Piper TTS backend
# ─────────────────────────────────────────────

async def _speak_piper(text: str) -> None:
    """Stream text through Piper TTS subprocess, play via ffplay.

    Model: de_DE-thorsten-high (22050 Hz, speaker_id=0)
    Piper CLI: piper --model <model.onnx> --speaker <id> --output-raw
    """
    voice_model = Path(os.environ.get(
        "PIPER_MODEL",
        f"models/{TTS_VOICE}.onnx"
    ))
    if not voice_model.exists():
        log.warning("Piper model not found: %s", voice_model)
        await _speak_pyttsx3(text)   # fallback to pyttsx3
        return

    # Sample rate for de_DE-thorsten-high is 22050 Hz
    sample_rate = 22050

    try:
        piper_cmd = [
            str(PIPER_PATH),
            "--model",   str(voice_model),
            "--speaker", str(TTS_SPEAKER),
            "--output-raw",
        ]
        player_cmd = [
            "ffplay",
            "-f", "s16le",
            "-ar", str(sample_rate),
            "-ac", "1",
            "-nodisp", "-autoexit", "-",
        ]
        piper = await asyncio.create_subprocess_exec(
            *piper_cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        player = await asyncio.create_subprocess_exec(
            *player_cmd,
            stdin=piper.stdout,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        assert piper.stdin
        piper.stdin.write(text.encode("utf-8"))
        await piper.stdin.drain()
        piper.stdin.close()
        await asyncio.gather(piper.wait(), player.wait())
    except Exception as exc:
        log.error("Piper TTS error: %s", exc)
        await _speak_pyttsx3(text)


# ─────────────────────────────────────────────
# pyttsx3 backend (runs in dedicated thread to avoid blocking event loop)
# ─────────────────────────────────────────────

_pyttsx3_queue: queue.Queue[str | None] = queue.Queue()
_pyttsx3_thread: threading.Thread | None = None


def _pyttsx3_worker() -> None:
    try:
        import pyttsx3  # type: ignore
        engine = pyttsx3.init()
        engine.setProperty("rate", TTS_RATE)

        # Prefer German SAPI5 voice (Windows: "Hedda" or any de-DE voice)
        voices = engine.getProperty("voices")
        german_voice = next(
            (v for v in voices if "de" in v.id.lower() or "german" in v.name.lower()
             or "hedda" in v.name.lower() or "stefan" in v.name.lower()),
            None,
        )
        if german_voice:
            engine.setProperty("voice", german_voice.id)
            log.info("pyttsx3: German voice selected: %s", german_voice.name)
        else:
            log.warning("pyttsx3: No German voice found — using system default")

        while True:
            text = _pyttsx3_queue.get()
            if text is None:
                break
            engine.say(text)
            engine.runAndWait()
    except Exception as exc:
        log.error("pyttsx3 worker error: %s", exc)


def _ensure_pyttsx3_thread() -> None:
    global _pyttsx3_thread
    if _pyttsx3_thread is None or not _pyttsx3_thread.is_alive():
        _pyttsx3_thread = threading.Thread(
            target=_pyttsx3_worker, daemon=True, name="pyttsx3-tts"
        )
        _pyttsx3_thread.start()


async def _speak_pyttsx3(text: str) -> None:
    loop = asyncio.get_event_loop()
    _ensure_pyttsx3_thread()
    await loop.run_in_executor(None, _pyttsx3_queue.put, text)


# ─────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────

_backend: str | None = None


def get_backend() -> str:
    global _backend
    if _backend is None:
        _backend = _detect_backend()
        log.info("TTS backend: %s", _backend)
    return _backend


async def speak(text: str) -> None:
    """Speak text using the best available backend. Non-blocking."""
    if not TTS_ENABLED:
        log.debug("TTS disabled, suppressing: %s", text[:60])
        return
    backend = get_backend()
    log.info("TTS [%s]: %s", backend, text[:80])
    if backend == "piper":
        await _speak_piper(text)
    elif backend == "pyttsx3":
        await _speak_pyttsx3(text)
    elif backend == "none":
        log.info("TTS(none): %s", text)
    # coqui: requires GPU model load, handled separately


async def announce_awp_complete(awp_id: str) -> None:
    await speak(f"Arbeitspaket {awp_id} erfolgreich abgeschlossen.")


async def announce_error(message: str) -> None:
    await speak(f"Warnung: {message}")


async def announce_pipeline_result(success: bool, file: str) -> None:
    if success:
        await speak(f"Pipeline abgeschlossen. {file} ist bereit.")
    else:
        await speak(f"Pipeline fehlgeschlagen für {file}. Menschliche Überprüfung erforderlich.")
