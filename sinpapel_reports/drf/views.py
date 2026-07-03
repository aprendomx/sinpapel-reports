"""Sinpapel Reports — vistas DRF (capa opcional).

Expone lo que la SPA `sinpapel-reports-designer` consumirá: catálogo de campos,
lectura/escritura de configuracion_overlay, generación y descarga.
"""
from __future__ import annotations

from dataclasses import asdict

from django.contrib.contenttypes.models import ContentType
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from sinpapel.models import Documento, InstanciaDocumento

from sinpapel_reports.drf.serializers import (
    CampoReporteSerializer,
    GenerateRequestSerializer,
)
from sinpapel_reports.exceptions import DataSourceNotFoundError, SinpapelReportsError
from sinpapel_reports.registry import ReportDataSourceRegistry
from sinpapel_reports.services.report_engine import ReportEngine


class FieldCatalogView(APIView):
    """GET /field-catalog/?source=<name> — paleta de campos de la fuente."""

    def get(self, request):
        name = request.query_params.get("source")
        if not name:
            return Response({"detail": "Falta el parámetro 'source'."}, status=400)
        try:
            source = ReportDataSourceRegistry.get(name)
        except DataSourceNotFoundError as exc:
            return Response({"detail": str(exc)}, status=404)
        data = [asdict(c) for c in source.get_field_catalog()]
        return Response(CampoReporteSerializer(data, many=True).data)


class OverlayConfigView(APIView):
    """GET/PUT /documentos/<pk>/overlay-config/."""

    def get(self, request, pk: int):
        documento = get_object_or_404(Documento, pk=pk)
        return Response(documento.configuracion_overlay or {})

    def put(self, request, pk: int):
        documento = get_object_or_404(Documento, pk=pk)
        if not isinstance(request.data, dict):
            return Response({"detail": "El cuerpo debe ser un objeto JSON."}, status=400)
        documento.configuracion_overlay = request.data
        documento.save(update_fields=["configuracion_overlay"])
        return Response(documento.configuracion_overlay)


class GenerateView(APIView):
    """POST /documentos/<pk>/generate/."""

    def post(self, request, pk: int):
        documento = get_object_or_404(Documento, pk=pk)
        req = GenerateRequestSerializer(data=request.data)
        req.is_valid(raise_exception=True)
        ct = get_object_or_404(ContentType, pk=req.validated_data["target_content_type"])
        model = ct.model_class()
        if model is None:
            return Response({"detail": "ContentType inválido."}, status=400)
        target = get_object_or_404(model, pk=req.validated_data["target_object_id"])
        try:
            res = ReportEngine.generar(
                documento, target, data_source=req.validated_data.get("data_source")
            )
        except DataSourceNotFoundError as exc:
            return Response({"detail": str(exc)}, status=404)
        except SinpapelReportsError as exc:
            return Response({"detail": str(exc)}, status=400)
        return Response(
            {"instancia_id": res.instancia_id, "filename": res.filename},
            status=status.HTTP_201_CREATED,
        )


class DownloadView(APIView):
    """GET /instancias/<pk>/download/."""

    def get(self, request, pk: int):
        instancia = get_object_or_404(InstanciaDocumento, pk=pk)
        if not instancia.archivo_generado:
            raise Http404("La instancia no tiene archivo generado.")
        return FileResponse(instancia.archivo_generado.open("rb"))
