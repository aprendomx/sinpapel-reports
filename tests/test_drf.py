from __future__ import annotations

import pytest
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile
from rest_framework.test import APIClient
from sinpapel.models import Documento

from sinpapel_reports.data_sources import FakeDataSource
from sinpapel_reports.registry import ReportDataSourceRegistry
from tests.models import OwnedThing
from tests.utils import _blank_pdf_bytes


@pytest.fixture
def client(db):
    user = User.objects.create_user(username="testuser", password="testpass")
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def fake_source():
    ReportDataSourceRegistry.register(FakeDataSource())


@pytest.fixture
def pdf_documento(db):
    doc = Documento.objects.create(
        nombre="Oficio Demo",
        valor="oficio",
        tipo_plantilla="PDF",
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
def test_overlay_config_put_rejects_malformed(client, pdf_documento):
    url = f"/api/documentos/{pdf_documento.pk}/overlay-config/"
    # campos_solicitud must be a dict; a string breaks OverlayConfig.from_json.
    resp = client.put(url, {"campos_solicitud": "not-a-dict"}, format="json")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_generate_unknown_data_source_returns_404(client, pdf_documento):
    """DataSourceNotFoundError in GenerateView must map to HTTP 404, not 400."""
    target = User.objects.create(username="z_404")
    ct = ContentType.objects.get_for_model(User)
    resp = client.post(
        f"/api/documentos/{pdf_documento.pk}/generate/",
        {
            "target_content_type": ct.pk,
            "target_object_id": target.pk,
            "data_source": "nonexistent_source",
        },
        format="json",
    )
    assert resp.status_code == 404, resp.content


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


@pytest.mark.django_db
def test_unauthenticated_returns_403(db, fake_source, pdf_documento):
    """Todos los endpoints deben rechazar peticiones sin autenticación."""
    anon = APIClient()
    assert anon.get("/api/field-catalog/", {"source": "fake"}).status_code == 403
    assert (
        anon.put(
            f"/api/documentos/{pdf_documento.pk}/overlay-config/",
            {},
            format="json",
        ).status_code
        == 403
    )
    target = User.objects.create(username="anon_target")
    ct = ContentType.objects.get_for_model(User)
    assert (
        anon.post(
            f"/api/documentos/{pdf_documento.pk}/generate/",
            {"target_content_type": ct.pk, "target_object_id": target.pk},
            format="json",
        ).status_code
        == 403
    )


@pytest.mark.django_db
def test_generate_ownership_denies_other_user(client, fake_source, pdf_documento):
    """Un usuario autenticado no puede generar sobre un target con owner distinto."""
    other_user = User.objects.create_user(username="other", password="other")
    thing = OwnedThing.objects.create(name="cosa", owner=other_user)
    ct = ContentType.objects.get_for_model(OwnedThing)
    resp = client.post(
        f"/api/documentos/{pdf_documento.pk}/generate/",
        {"target_content_type": ct.pk, "target_object_id": thing.pk},
        format="json",
    )
    assert resp.status_code == 403
    assert "permiso" in resp.json()["detail"].lower()
