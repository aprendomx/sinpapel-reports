"""Sinpapel Reports — fachada de generación de documentos.

Resuelve la fuente de datos, construye el contexto, elige el renderer según
`tipo_plantilla` y persiste un `InstanciaDocumento`. `generar_paquete` agrupa
varios targets en un ZIP en memoria.
"""
from __future__ import annotations

import io
import zipfile
from dataclasses import dataclass
from typing import Any

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils.text import slugify
from sinpapel.models import Documento, InstanciaDocumento

from sinpapel_reports.exceptions import DataSourceNotFoundError, UnsupportedTemplateError
from sinpapel_reports.registry import ReportDataSourceRegistry
from sinpapel_reports.schemas.overlay import OverlayConfig
from sinpapel_reports.services.docx_renderer import DocxRenderer
from sinpapel_reports.services.overlay_renderer import OverlayRenderer


@dataclass(frozen=True)
class ResultadoGeneracion:
    instancia_id: int
    filename: str
    contenido: bytes


@dataclass(frozen=True)
class ResultadoPaquete:
    generaciones: list[ResultadoGeneracion]
    zip_bytes: bytes
    zip_filename: str


class ReportEngine:
    """Genera documentos a partir de un Documento (plantilla) y un target."""

    @staticmethod
    def _resolve_source_name(documento: Documento, data_source: str | None) -> str:
        if data_source:
            return data_source
        config = documento.configuracion_overlay or {}
        if config.get("data_source"):
            return config["data_source"]
        default = getattr(settings, "SINPAPEL_REPORTS_DEFAULT_DATA_SOURCE", None)
        if default:
            return default
        raise DataSourceNotFoundError(
            f"Documento {documento.pk} no declara data_source y no hay "
            f"SINPAPEL_REPORTS_DEFAULT_DATA_SOURCE configurado."
        )

    @staticmethod
    def _render(documento: Documento, contexto: dict[str, Any]) -> tuple[bytes, str]:
        path = getattr(documento.plantilla, "path", None)
        if not path:
            raise UnsupportedTemplateError(f"Documento {documento.pk} sin archivo de plantilla.")
        stem = slugify(documento.nombre or str(documento.pk))
        if documento.tipo_plantilla == "PDF":
            config = OverlayConfig.from_json(documento.configuracion_overlay or {})
            return OverlayRenderer.render(path, config, contexto), f"{stem}.pdf"
        if documento.tipo_plantilla == "DOCX":
            return DocxRenderer.render(path, contexto), f"{stem}.docx"
        raise UnsupportedTemplateError(
            f"tipo_plantilla '{documento.tipo_plantilla}' no soportado (Documento {documento.pk})."
        )

    @classmethod
    def generar(
        cls,
        documento: Documento,
        target: Any,
        *,
        actor: Any = None,
        data_source: str | None = None,
    ) -> ResultadoGeneracion:
        source = ReportDataSourceRegistry.get(cls._resolve_source_name(documento, data_source))
        contexto = source.build_context(target)
        contenido, base_filename = cls._render(documento, contexto)
        target_id = getattr(target, "pk", None)
        filename = f"{base_filename.rsplit('.', 1)[0]}_{target_id}.{base_filename.rsplit('.', 1)[1]}"
        with transaction.atomic():
            instancia = InstanciaDocumento(target=target, documento=documento, actor=actor)
            instancia.save()
            instancia.archivo_generado.save(filename, ContentFile(contenido, name=filename), save=True)
        return ResultadoGeneracion(
            instancia_id=instancia.pk,
            filename=instancia.archivo_generado.name,
            contenido=contenido,
        )

    @classmethod
    def generar_paquete(
        cls,
        documento: Documento,
        targets: list[Any],
        *,
        actor: Any = None,
        data_source: str | None = None,
    ) -> ResultadoPaquete:
        generaciones: list[ResultadoGeneracion] = []
        zip_buffer = io.BytesIO()
        with transaction.atomic():
            with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
                for target in targets:
                    res = cls.generar(documento, target, actor=actor, data_source=data_source)
                    generaciones.append(res)
                    arcname = res.filename.rsplit("/", 1)[-1]
                    zf.writestr(arcname, res.contenido)
        zip_buffer.seek(0)
        zip_filename = f"{slugify(documento.nombre or str(documento.pk))}_paquete.zip"
        return ResultadoPaquete(
            generaciones=generaciones,
            zip_bytes=zip_buffer.getvalue(),
            zip_filename=zip_filename,
        )
