"""Sinpapel Reports — renderer de overlay PDF (ReportLab + PyPDF2)."""

from __future__ import annotations

import io
import logging
from typing import Any

from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas

from sinpapel_reports.schemas.overlay import OverlayConfig

logger = logging.getLogger(__name__)


class OverlayRenderer:
    """Estampa valores del contexto sobre una plantilla PDF según OverlayConfig."""

    @staticmethod
    def render(template_path: str, config: OverlayConfig, contexto: dict[str, Any]) -> bytes:
        """Estampa el contexto sobre la plantilla PDF según config y devuelve bytes."""
        reader = PdfReader(template_path)
        writer = PdfWriter()
        overlays = OverlayRenderer._build_overlays(config, contexto, reader)
        for i, page in enumerate(reader.pages):
            if i < len(overlays) and overlays[i] is not None:
                page.merge_page(overlays[i])
            writer.add_page(page)
        out = io.BytesIO()
        writer.write(out)
        return out.getvalue()

    @staticmethod
    def _build_overlays(
        config: OverlayConfig, contexto: dict[str, Any], reader: PdfReader
    ) -> list[Any]:
        total_pages = len(reader.pages)
        if total_pages == 0:
            return []
        font_name = config.fuente.nombre or "Helvetica"
        font_size = config.fuente.tamano or 10

        buffers: list[io.BytesIO] = []
        canvases: list[dict[str, Any]] = []
        for page in reader.pages:
            w = float(page.mediabox.width)
            h = float(page.mediabox.height)
            buf = io.BytesIO()
            buffers.append(buf)
            canvases.append({"canvas": canvas.Canvas(buf, pagesize=(w, h)), "height": h})

        def _set_font(c: Any) -> None:
            try:
                c.setFont(font_name, font_size)
            except Exception:
                logger.warning(
                    "Fuente %s no disponible en ReportLab; usando Helvetica.", font_name
                )
                c.setFont("Helvetica", 10)

        campos = config.campos()
        usar_simple = not any(c.posiciones for c in campos.values())

        if usar_simple:
            OverlayRenderer._render_sequential(campos, contexto, canvases, config, _set_font)
        else:
            OverlayRenderer._render_multi_position(
                campos, contexto, canvases, total_pages, _set_font
            )

        overlays: list[Any] = []
        for i, buf in enumerate(buffers):
            canvases[i]["canvas"].save()
            buf.seek(0)
            try:
                ov = PdfReader(buf)
                overlays.append(ov.pages[0] if ov.pages else None)
            except Exception:
                logger.warning("Error al leer overlay de página %s; omitiendo.", i)
                overlays.append(None)
        return overlays

    @staticmethod
    def _render_sequential(
        campos: dict[str, Any],
        contexto: dict[str, Any],
        canvases: list[dict[str, Any]],
        config: OverlayConfig,
        _set_font: Any,
    ) -> None:
        """Modo secuencial: un solo canvas, campos apilados verticalmente."""
        c_info = canvases[0]
        c = c_info["canvas"]
        _set_font(c)
        y_pos = c_info["height"] - config.posicion_base.y_top_offset
        for key, campo in campos.items():
            if not campo.visible:
                continue
            valor = contexto.get(key)
            if not valor:
                continue
            if campo.x is not None and campo.y is not None:
                c.drawString(campo.x, c_info["height"] - campo.y, f"{valor}")
            else:
                c.drawString(config.posicion_base.x_left, y_pos, f"{valor}")
                y_pos -= config.posicion_base.line_height

    @staticmethod
    def _render_multi_position(
        campos: dict[str, Any],
        contexto: dict[str, Any],
        canvases: list[dict[str, Any]],
        total_pages: int,
        _set_font: Any,
    ) -> None:
        """Modo multi-posición: campos estampados en coordenadas/páginas arbitrarias."""
        for key, campo in campos.items():
            if not campo.visible:
                continue
            valor = contexto.get(key)
            if not valor:
                continue
            if not campo.posiciones:
                if campo.x is not None and campo.y is not None:
                    c_info = canvases[0]
                    c = c_info["canvas"]
                    _set_font(c)
                    c.drawString(campo.x, c_info["height"] - campo.y, f"{valor}")
                continue
            for pos in campo.posiciones:
                if not isinstance(pos, dict):
                    continue
                x = pos.get("x")
                y = pos.get("y")
                page = pos.get("page", 1)
                if x is None or y is None:
                    continue
                idx = int(page) - 1
                if idx < 0 or idx >= total_pages:
                    continue
                c_info = canvases[idx]
                c = c_info["canvas"]
                _set_font(c)
                c.drawString(x, c_info["height"] - y, f"{valor}")
