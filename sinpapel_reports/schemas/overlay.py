"""Sinpapel Reports — esquema de configuración de overlay.

Modela el JSON almacenado en `Documento.configuracion_overlay` con dataclasses
inmutables. Preserva las claves históricas (`campos_solicitud`,
`campos_participantes`, `tamaño`, alias `posicion`) por compatibilidad con
configuraciones ya guardadas en producción.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

SCHEMA_VERSION = "0.1"


@dataclass(frozen=True)
class Fuente:
    """Fuente tipográfica para el overlay PDF."""

    nombre: str = "Helvetica"
    tamano: int = 10


@dataclass(frozen=True)
class PosicionBase:
    """Coordenadas base para el modo secuencial de overlay."""

    x_left: float = 50
    y_top_offset: float = 50
    line_height: float = 15


@dataclass(frozen=True)
class CampoOverlay:
    """Configuración de un campo estampable en el overlay."""

    visible: bool = False
    label: str = ""
    x: float | None = None
    y: float | None = None
    posiciones: tuple[dict[str, Any], ...] = ()


def _campo_from_json(data: dict[str, Any]) -> CampoOverlay:
    posiciones = tuple(dict(p) for p in data.get("posiciones", []) or [])
    return CampoOverlay(
        visible=bool(data.get("visible", False)),
        label=str(data.get("label", "")),
        x=data.get("x"),
        y=data.get("y"),
        posiciones=posiciones,
    )


def _campo_to_json(campo: CampoOverlay) -> dict[str, Any]:
    return {
        "visible": campo.visible,
        "label": campo.label,
        "x": campo.x,
        "y": campo.y,
        "posiciones": [dict(p) for p in campo.posiciones],
    }


@dataclass(frozen=True)
class OverlayConfig:
    """Configuración completa de overlay parseada desde JSON."""

    campos_solicitud: dict[str, CampoOverlay] = field(default_factory=dict)
    campos_participantes: dict[str, CampoOverlay] = field(default_factory=dict)
    posicion_base: PosicionBase = field(default_factory=PosicionBase)
    fuente: Fuente = field(default_factory=Fuente)
    data_source: str | None = None

    @classmethod
    def from_json(cls, data: dict[str, Any] | None) -> OverlayConfig:
        """Construye OverlayConfig desde un dict JSON (con alias retro-compatibles)."""
        data = data or {}
        fuente_raw = data.get("fuente", {}) or {}
        fuente = Fuente(
            nombre=fuente_raw.get("nombre", "Helvetica"),
            tamano=fuente_raw.get("tamaño", fuente_raw.get("tamano", 10)),
        )
        # Alias retro-compat: `posicion` -> `posicion_base`.
        pos_raw = data.get("posicion_base", data.get("posicion", {})) or {}
        base = replace(
            PosicionBase(),
            **{k: pos_raw[k] for k in ("x_left", "y_top_offset", "line_height") if k in pos_raw},
        )
        return cls(
            campos_solicitud={
                k: _campo_from_json(v) for k, v in (data.get("campos_solicitud", {}) or {}).items()
            },
            campos_participantes={
                k: _campo_from_json(v)
                for k, v in (data.get("campos_participantes", {}) or {}).items()
            },
            posicion_base=base,
            fuente=fuente,
            data_source=data.get("data_source"),
        )

    def to_json(self) -> dict[str, Any]:
        """Serializa la configuración a dict JSON."""
        out: dict[str, Any] = {
            "campos_solicitud": {k: _campo_to_json(v) for k, v in self.campos_solicitud.items()},
            "campos_participantes": {
                k: _campo_to_json(v) for k, v in self.campos_participantes.items()
            },
            "posicion_base": {
                "x_left": self.posicion_base.x_left,
                "y_top_offset": self.posicion_base.y_top_offset,
                "line_height": self.posicion_base.line_height,
            },
            "fuente": {"nombre": self.fuente.nombre, "tamaño": self.fuente.tamano},
        }
        if self.data_source is not None:
            out["data_source"] = self.data_source
        return out

    def campos(self) -> dict[str, CampoOverlay]:
        """Campos fusionados de ambos grupos (solicitud primero), orden preservado."""
        merged: dict[str, CampoOverlay] = {}
        merged.update(self.campos_solicitud)
        merged.update(self.campos_participantes)
        return merged
