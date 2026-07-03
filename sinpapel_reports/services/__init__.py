"""Sinpapel Reports — services."""

from __future__ import annotations

from sinpapel_reports.services.docx_renderer import DocxRenderer
from sinpapel_reports.services.overlay_renderer import OverlayRenderer
from sinpapel_reports.services.report_engine import (
    ReportEngine,
    ResultadoGeneracion,
    ResultadoPaquete,
)

__all__ = [
    "DocxRenderer",
    "OverlayRenderer",
    "ReportEngine",
    "ResultadoGeneracion",
    "ResultadoPaquete",
]
