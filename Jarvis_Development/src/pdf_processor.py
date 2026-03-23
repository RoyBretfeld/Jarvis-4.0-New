"""
JARVIS 4.0 – PDF Processor
Extrahiert Text und Bilder aus PDFs (bis 200MB) seitenweise.
Nutzt pymupdf (fitz) für schnelle, speichereffiziente Verarbeitung.
Python 3.12 | pymupdf
"""
from __future__ import annotations

import base64
import logging
from dataclasses import dataclass
from pathlib import Path

import fitz  # pymupdf

log = logging.getLogger("jarvis.pdf_processor")

# Minimale Pixelfläche damit ein Bild VLM-relevant ist (klein = skip)
MIN_IMAGE_AREA = 50 * 50


@dataclass
class PdfPage:
    page_num: int       # 1-based
    text: str           # extrahierter Text
    images_b64: list[str]  # base64-encoded PNG Bilder auf der Seite
    has_significant_visuals: bool  # True wenn VLM-Scan sinnvoll


@dataclass
class PdfDocument:
    source_path: str
    page_count: int
    pages: list[PdfPage]


def extract_pdf(pdf_path: Path, dpi: int = 96) -> PdfDocument:
    """
    Liest PDF seitenweise. Rendert Seiten mit signifikanten Bildern als PNG.
    dpi=96 ist ein guter Kompromiss: lesbar für VLM, nicht zu groß.
    """
    log.info("PDF extract start: %s", pdf_path.name)
    doc = fitz.open(str(pdf_path))
    pages: list[PdfPage] = []

    for page_num, page in enumerate(doc, start=1):
        text = page.get_text("text").strip()

        # Bilder auf der Seite
        image_list = page.get_images(full=True)
        significant_images: list[str] = []

        for img_info in image_list:
            xref = img_info[0]
            try:
                base_image = doc.extract_image(xref)
                w, h = base_image["width"], base_image["height"]
                if w * h < MIN_IMAGE_AREA:
                    continue
                img_bytes = base_image["image"]
                significant_images.append(
                    base64.b64encode(img_bytes).decode("ascii")
                )
            except Exception as exc:
                log.debug("Image extract error (page %d, xref %d): %s",
                          page_num, xref, exc)

        # Seite als ganzes rendern wenn sie viele Grafiken/Tabellen hat
        # (erkannt durch wenig Text bei großem Seiteninhalt)
        has_visuals = len(significant_images) > 0
        text_density = len(text) / max(page.rect.get_area(), 1)
        if text_density < 0.005 and page.get_drawings():
            # Seite ist hauptsächlich grafisch → als Bitmap für VLM
            mat = fitz.Matrix(dpi / 72, dpi / 72)
            pixmap = page.get_pixmap(matrix=mat, alpha=False)
            page_png_b64 = base64.b64encode(pixmap.tobytes("png")).decode("ascii")
            significant_images = [page_png_b64]  # Seite als Ganzes
            has_visuals = True

        pages.append(PdfPage(
            page_num=page_num,
            text=text,
            images_b64=significant_images,
            has_significant_visuals=has_visuals,
        ))

        log.debug("Page %d: %d chars text, %d images, visuals=%s",
                  page_num, len(text), len(significant_images), has_visuals)

    doc.close()
    log.info("PDF extract done: %d pages, source=%s", len(pages), pdf_path.name)
    return PdfDocument(
        source_path=str(pdf_path),
        page_count=len(pages),
        pages=pages,
    )
