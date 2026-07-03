"""Sinpapel Reports — contrato y registro de fuentes de datos.

`ReportDataSource` es el seam que desacopla el framework del dominio del host:
provee el catálogo de campos (paleta del editor) y el contexto de datos para
renderizar una plantilla contra un `target` arbitrario.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar, Protocol, runtime_checkable

from sinpapel_reports.registry import ReportDataSourceRegistry


@dataclass(frozen=True)
class CampoReporte:
    """Una entrada de la paleta de campos del editor."""

    key: str
    label: str
    grupo: str = "solicitud"


@runtime_checkable
class ReportDataSource(Protocol):
    """Contrato que una app host implementa para alimentar el generador.

    El `name` identifica la fuente en `Documento.configuracion_overlay["data_source"]`.
    """

    name: ClassVar[str]

    def get_field_catalog(self) -> list[CampoReporte]:
        """Campos disponibles para la paleta del editor."""
        ...

    def build_context(self, target: Any) -> dict[str, Any]:
        """Construye el dict de datos para renderizar contra `target`."""
        ...


def register_data_source(cls: type) -> type:
    """Decorator de clase: instancia y registra la fuente.

    Uso:
        @register_data_source
        class SolicitudDataSource:
            name = "solicitud"
            def get_field_catalog(self): ...
            def build_context(self, target): ...
    """
    ReportDataSourceRegistry.register(cls())
    return cls


class FakeDataSource:
    """Fuente determinística para tests (no depende de ningún modelo del host)."""

    name: ClassVar[str] = "fake"

    def get_field_catalog(self) -> list[CampoReporte]:
        return [
            CampoReporte(key="folio", label="Folio", grupo="solicitud"),
            CampoReporte(key="nombre_grupo", label="Nombre Grupo", grupo="solicitud"),
            CampoReporte(key="curp", label="CURP", grupo="participantes"),
        ]

    def build_context(self, target: Any) -> dict[str, Any]:
        return {"folio": 123, "nombre_grupo": "GRUPO DEMO", "curp": "XAXX010101HDFXXX01"}
