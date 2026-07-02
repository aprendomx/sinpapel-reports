from __future__ import annotations

import io

from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas

from sinpapel_reports.schemas.overlay import OverlayConfig
from sinpapel_reports.services.overlay_renderer import OverlayRenderer


def _blank_pdf(path: str, pages: int = 1) -> None:
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


def test_render_preserves_page_count(tmp_path):
    tpl = tmp_path / "t.pdf"
    _blank_pdf(str(tpl), pages=2)
    cfg = OverlayConfig.from_json({})
    out = OverlayRenderer.render(str(tpl), cfg, {})
    assert PdfReader(io.BytesIO(out)).pages.__len__() == 2


def test_render_stamps_value_at_position(tmp_path):
    tpl = tmp_path / "t.pdf"
    _blank_pdf(str(tpl), pages=1)
    cfg = OverlayConfig.from_json({
        "campos_solicitud": {
            "folio": {"visible": True, "label": "Folio",
                      "posiciones": [{"x": 20, "y": 40, "page": 1}]},
        },
    })
    out = OverlayRenderer.render(str(tpl), cfg, {"folio": "ABC-999"})
    text = PdfReader(io.BytesIO(out)).pages[0].extract_text() or ""
    assert "ABC-999" in text


def test_invisible_field_not_stamped(tmp_path):
    tpl = tmp_path / "t.pdf"
    _blank_pdf(str(tpl), pages=1)
    cfg = OverlayConfig.from_json({
        "campos_solicitud": {
            "folio": {"visible": False, "label": "Folio",
                      "posiciones": [{"x": 20, "y": 40, "page": 1}]},
        },
    })
    out = OverlayRenderer.render(str(tpl), cfg, {"folio": "HIDDEN"})
    text = PdfReader(io.BytesIO(out)).pages[0].extract_text() or ""
    assert "HIDDEN" not in text
