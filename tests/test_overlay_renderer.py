from __future__ import annotations

import io

from PyPDF2 import PdfReader

from sinpapel_reports.schemas.overlay import OverlayConfig
from sinpapel_reports.services.overlay_renderer import OverlayRenderer
from tests.utils import _blank_pdf


def test_render_preserves_page_count(tmp_path):
    tpl = tmp_path / "t.pdf"
    _blank_pdf(str(tpl), pages=2)
    cfg = OverlayConfig.from_json({})
    out = OverlayRenderer.render(str(tpl), cfg, {})
    assert PdfReader(io.BytesIO(out)).pages.__len__() == 2


def test_render_stamps_value_at_position(tmp_path):
    tpl = tmp_path / "t.pdf"
    _blank_pdf(str(tpl), pages=1)
    cfg = OverlayConfig.from_json(
        {
            "campos_solicitud": {
                "folio": {
                    "visible": True,
                    "label": "Folio",
                    "posiciones": [{"x": 20, "y": 40, "page": 1}],
                },
            },
        }
    )
    out = OverlayRenderer.render(str(tpl), cfg, {"folio": "ABC-999"})
    text = PdfReader(io.BytesIO(out)).pages[0].extract_text() or ""
    assert "ABC-999" in text


def test_render_stamps_on_second_page(tmp_path):
    tpl = tmp_path / "t.pdf"
    _blank_pdf(str(tpl), pages=2)
    cfg = OverlayConfig.from_json(
        {
            "campos_solicitud": {
                "nombre": {
                    "visible": True,
                    "label": "Nombre",
                    "posiciones": [{"x": 20, "y": 40, "page": 2}],
                },
            },
        }
    )
    out = OverlayRenderer.render(str(tpl), cfg, {"nombre": "PAGINA-DOS"})
    reader = PdfReader(io.BytesIO(out))
    text_p0 = reader.pages[0].extract_text() or ""
    text_p1 = reader.pages[1].extract_text() or ""
    assert "PAGINA-DOS" not in text_p0
    assert "PAGINA-DOS" in text_p1


def test_render_sequential_simple_mode(tmp_path):
    tpl = tmp_path / "t.pdf"
    _blank_pdf(str(tpl), pages=1)
    # No posiciones, no x/y — triggers the sequential (posicion_base) fallback.
    cfg = OverlayConfig.from_json(
        {
            "campos_solicitud": {
                "folio": {"visible": True, "label": "Folio"},
            },
        }
    )
    out = OverlayRenderer.render(str(tpl), cfg, {"folio": "SEQ-001"})
    text = PdfReader(io.BytesIO(out)).pages[0].extract_text() or ""
    assert "SEQ-001" in text


def test_invisible_field_not_stamped(tmp_path):
    tpl = tmp_path / "t.pdf"
    _blank_pdf(str(tpl), pages=1)
    cfg = OverlayConfig.from_json(
        {
            "campos_solicitud": {
                "folio": {
                    "visible": False,
                    "label": "Folio",
                    "posiciones": [{"x": 20, "y": 40, "page": 1}],
                },
            },
        }
    )
    out = OverlayRenderer.render(str(tpl), cfg, {"folio": "HIDDEN"})
    text = PdfReader(io.BytesIO(out)).pages[0].extract_text() or ""
    assert "HIDDEN" not in text
