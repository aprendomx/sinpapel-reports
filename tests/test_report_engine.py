from __future__ import annotations

import io

import pytest
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from PyPDF2 import PdfReader
from sinpapel.models import Documento

from sinpapel_reports.data_sources import FakeDataSource
from sinpapel_reports.exceptions import DataSourceNotFoundError, UnsupportedTemplateError
from sinpapel_reports.registry import ReportDataSourceRegistry
from sinpapel_reports.services.report_engine import ReportEngine, ResultadoPaquete
from tests.utils import _blank_pdf_bytes


@pytest.fixture
def fake_source():
    src = FakeDataSource()
    ReportDataSourceRegistry.register(src)
    return src


@pytest.fixture
def pdf_documento(db):
    doc = Documento.objects.create(
        nombre="Oficio Demo",
        valor="oficio",
        tipo_plantilla="PDF",
        configuracion_overlay={
            "data_source": "fake",
            "campos_solicitud": {
                "folio": {
                    "visible": True,
                    "label": "Folio",
                    "posiciones": [{"x": 20, "y": 40, "page": 1}],
                },
            },
        },
    )
    doc.plantilla.save("demo.pdf", ContentFile(_blank_pdf_bytes(), name="demo.pdf"), save=True)
    return doc


@pytest.mark.django_db
def test_generar_pdf_persists_instancia(fake_source, pdf_documento):
    target = User.objects.create(username="t1")
    res = ReportEngine.generar(pdf_documento, target)
    assert res.instancia_id > 0
    assert res.filename.endswith(".pdf")
    text = PdfReader(io.BytesIO(res.contenido)).pages[0].extract_text() or ""
    assert "123" in text  # FakeDataSource folio


@pytest.mark.django_db
def test_generar_unknown_source_raises(pdf_documento):
    # Registry cleared by autouse fixture -> 'fake' not registered.
    target = User.objects.create(username="t2")
    with pytest.raises(DataSourceNotFoundError):
        ReportEngine.generar(pdf_documento, target)


@pytest.mark.django_db
def test_generar_missing_plantilla_raises_unsupported(fake_source, db):
    """Documento sin archivo adjunto debe levantar UnsupportedTemplateError, no ValueError."""
    doc = Documento.objects.create(
        nombre="Sin Archivo",
        valor="sin-archivo",
        tipo_plantilla="PDF",
        configuracion_overlay={"data_source": "fake"},
    )
    # plantilla field left empty — no .save() call
    target = User.objects.create(username="t_nofile")
    with pytest.raises(UnsupportedTemplateError):
        ReportEngine.generar(doc, target)


@pytest.mark.django_db
def test_generar_paquete_returns_zip(fake_source, pdf_documento):
    t1 = User.objects.create(username="a")
    t2 = User.objects.create(username="b")
    res = ReportEngine.generar_paquete(pdf_documento, [t1, t2])
    assert isinstance(res, ResultadoPaquete)
    assert len(res.generaciones) == 2
    import zipfile

    zf = zipfile.ZipFile(io.BytesIO(res.zip_bytes))
    assert len(zf.namelist()) == 2


@pytest.mark.django_db
def test_generar_uses_transaction_atomic(fake_source, pdf_documento):
    """Verifica que generar() envuelve la persistencia en transaction.atomic()."""
    from unittest.mock import patch

    target = User.objects.create(username="atomic")
    with patch("django.db.transaction.atomic") as mock_atomic:
        mock_atomic.return_value.__enter__ = lambda s: s
        mock_atomic.return_value.__exit__ = lambda *a: None
        ReportEngine.generar(pdf_documento, target)
    mock_atomic.assert_called_once()
