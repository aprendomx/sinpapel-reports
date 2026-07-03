"""Sinpapel Reports — renderer de plantillas DOCX (docxtpl)."""
from __future__ import annotations

import io
from typing import Any

from docxtpl import DocxTemplate


class DocxRenderer:
    """Rellena una plantilla .docx con el contexto y devuelve los bytes resultantes."""

    @staticmethod
    def render(template_path: str, contexto: dict[str, Any]) -> bytes:
        tpl = DocxTemplate(template_path)
        tpl.render(contexto)
        out = io.BytesIO()
        tpl.save(out)
        return out.getvalue()
