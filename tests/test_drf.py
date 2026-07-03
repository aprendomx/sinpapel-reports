from __future__ import annotations

import io

import pytest
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from rest_framework.test import APIClient
from sinpapel.models import Documento

from sinpapel_reports.data_sources import FakeDataSource
from sinpapel_reports.registry import ReportDataSourceRegistry


def _blank_pdf_bytes() -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(300, 300))
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


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def fake_source():
    ReportDataSourceRegistry.register(FakeDataSource())


@pytest.fixture
def pdf_documento(db):
    doc = Documento.objects.create(
        nombre="Oficio Demo", valor="oficio", tipo_plantilla="PDF",
        configuracion_overlay={"data_source": "fake"},
    )
    doc.plantilla.save("demo.pdf", ContentFile(_blank_pdf_bytes(), name="demo.pdf"), save=True)
    return doc


@pytest.mark.django_db
def test_field_catalog(client, fake_source):
    resp = client.get("/api/field-catalog/", {"source": "fake"})
    assert resp.status_code == 200
    keys = {c["key"] for c in resp.json()}
    assert {"folio", "nombre_grupo", "curp"} <= keys


@pytest.mark.django_db
def test_overlay_config_get_put(client, pdf_documento):
    url = f"/api/documentos/{pdf_documento.pk}/overlay-config/"
    new_cfg = {"data_source": "fake", "fuente": {"nombre": "Helvetica", "tamaño": 14}}
    put = client.put(url, new_cfg, format="json")
    assert put.status_code == 200
    pdf_documento.refresh_from_db()
    assert pdf_documento.configuracion_overlay["fuente"]["tamaño"] == 14
    get = client.get(url)
    assert get.status_code == 200 and get.json()["fuente"]["tamaño"] == 14


@pytest.mark.django_db
def test_generate_and_download(client, fake_source, pdf_documento):
    target = User.objects.create(username="z")
    ct = ContentType.objects.get_for_model(User)
    resp = client.post(
        f"/api/documentos/{pdf_documento.pk}/generate/",
        {"target_content_type": ct.pk, "target_object_id": target.pk},
        format="json",
    )
    assert resp.status_code == 201, resp.content
    instancia_id = resp.json()["instancia_id"]
    dl = client.get(f"/api/instancias/{instancia_id}/download/")
    assert dl.status_code == 200
    assert dl["Content-Type"] == "application/pdf"
