"""
JARVIS 4.0 – Document Parser & Chunker
AWP-103: Parst PDF (PyMuPDF/fitz), TXT, MD.
AWP-104: 500-Token-Chunks mit 10% Overlap via MarkdownChunker.
Python 3.12 | pymupdf | RB-Protokoll: Glass-Box
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

log = logging.getLogger("jarvis.parser")

# ─── Chunk-Zielgröße für hochgeladene Dokumente (AWP-112: char-basiert) ────────
UPLOAD_CHUNK_SIZE    = 2000   # Zeichen (≈500 Token bei 4 Zeichen/Token)
UPLOAD_CHUNK_OVERLAP = 500    # 25% Overlap für besseren Kontext


@dataclass
class ParsedDocument:
    filename: str
    source_id: str          # "upload::<filename>"
    text_by_page: list[str] # Ein Eintrag pro Seite (PDFs) oder Absatz-Block (txt/md)
    page_count: int
    size_bytes: int


# ─────────────────────────────────────────────
# PDF Parser (PyMuPDF / fitz)
# ─────────────────────────────────────────────
def _parse_pdf(path: Path) -> ParsedDocument:
    try:
        import fitz  # pymupdf
    except ImportError as exc:
        raise RuntimeError(
            "pymupdf nicht installiert – führe aus: pip install pymupdf"
        ) from exc

    log.info("PDF parse start: %s", path.name)
    doc = fitz.open(str(path))
    pages: list[str] = []

    for page in doc:
        text = page.get_text("text").strip()
        if text:
            pages.append(text)

    doc.close()
    log.info("PDF parsed: %d Seiten mit Text, source=%s", len(pages), path.name)
    return ParsedDocument(
        filename=path.name,
        source_id=f"upload::{path.name}",
        text_by_page=pages,
        page_count=len(pages),
        size_bytes=path.stat().st_size,
    )


# ─────────────────────────────────────────────
# Text / Markdown Parser
# ─────────────────────────────────────────────
def _parse_text(path: Path) -> ParsedDocument:
    text = path.read_text(encoding="utf-8", errors="replace")
    log.info("Text parsed: %d Zeichen, source=%s", len(text), path.name)
    return ParsedDocument(
        filename=path.name,
        source_id=f"upload::{path.name}",
        text_by_page=[text],
        page_count=1,
        size_bytes=path.stat().st_size,
    )


# ─────────────────────────────────────────────
# Dispatcher
# ─────────────────────────────────────────────
def parse_document(path: Path) -> ParsedDocument:
    """
    Wählt automatisch den richtigen Parser anhand der Dateiendung.
    Unterstützt: .pdf, .txt, .md
    """
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _parse_pdf(path)
    elif suffix in (".txt", ".md"):
        return _parse_text(path)
    else:
        raise ValueError(f"Nicht unterstützter Dateityp: {suffix!r}")


# ─────────────────────────────────────────────
# AWP-104: Chunking (500 Token, 10% Overlap)
# ─────────────────────────────────────────────
def chunk_document(doc: ParsedDocument) -> list[Any]:
    """
    AWP-112: Zerlegt ein ParsedDocument via RecursiveCharacterTextSplitter.
    2000 Zeichen / 500 Overlap → semantisch kohärente Chunks für Qwen-Kontext.
    Gibt list[TextChunk] zurück (aus ingest_docs).
    """
    from ingest_docs import RecursiveCharacterTextSplitter, TextChunk  # type: ignore

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=UPLOAD_CHUNK_SIZE,
        chunk_overlap=UPLOAD_CHUNK_OVERLAP,
    )

    all_chunks: list[TextChunk] = []
    for page_idx, page_text in enumerate(doc.text_by_page, start=1):
        if not page_text.strip():
            continue
        source_label = (
            f"{doc.source_id}::page_{page_idx}"
            if doc.page_count > 1
            else doc.source_id
        )
        page_chunks = splitter.chunk(page_text, source=source_label)
        # Re-index chunk_index global over all pages
        for chunk in page_chunks:
            chunk.chunk_index = len(all_chunks) + chunk.chunk_index
        all_chunks.extend(page_chunks)

    log.info(
        "RCST-Chunking: %d Chunks aus %d Seiten (size=%d chars, overlap=%d) für %s",
        len(all_chunks), doc.page_count,
        UPLOAD_CHUNK_SIZE, UPLOAD_CHUNK_OVERLAP,
        doc.filename,
    )
    return all_chunks
