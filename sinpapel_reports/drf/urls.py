"""Sinpapel Reports — rutas DRF."""
from __future__ import annotations

from django.urls import path

from sinpapel_reports.drf.views import (
    DownloadView,
    FieldCatalogView,
    GenerateView,
    OverlayConfigView,
)

app_name = "sinpapel_reports"

urlpatterns = [
    path("field-catalog/", FieldCatalogView.as_view(), name="field-catalog"),
    path("documentos/<int:pk>/overlay-config/", OverlayConfigView.as_view(), name="overlay-config"),
    path("documentos/<int:pk>/generate/", GenerateView.as_view(), name="generate"),
    path("instancias/<int:pk>/download/", DownloadView.as_view(), name="download"),
]
