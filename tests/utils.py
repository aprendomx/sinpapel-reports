"""Utilidades compartidas entre tests."""

from __future__ import annotations

import io

from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas


def _blank_pdf_bytes(pages: int = 1) -> bytes:
    """Genera un PDF en blanco de `pages` páginas y devuelve los bytes."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(300, 300))
    for _ in range(pages):
        c.showPage()
    c.save()
    buf.seek(0)
    reader = PdfReader(buf)
    writer = PdfWriter()
    for p in reader.pages:
        writer.add_page(p)
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def _blank_pdf(path: str, pages: int = 1) -> None:
    """Escribe un PDF en blanco de `pages` páginas en `path`."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(300, 300))
    for _ in range(pages):
        c.showPage()
    c.save()
    buf.seek(0)
    reader = PdfReader(buf)
    writer = PdfWriter()
    for p in reader.pages:
        writer.add_page(p)
    with open(path, "wb") as fh:
        writer.write(fh)
