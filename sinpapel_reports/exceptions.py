"""Sinpapel Reports — jerarquía de excepciones."""

from __future__ import annotations


class SinpapelReportsError(Exception):
    """Base de todas las excepciones del framework de reportes."""


class DataSourceNotFoundError(SinpapelReportsError):
    """No existe una fuente de datos registrada con el nombre solicitado."""


class UnsupportedTemplateError(SinpapelReportsError):
    """tipo_plantilla no soportado (no es 'PDF' ni 'DOCX')."""


class OverlaySchemaError(SinpapelReportsError):
    """configuracion_overlay malformada o no deserializable."""
