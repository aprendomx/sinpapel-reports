from __future__ import annotations

from sinpapel_reports.schemas.overlay import (
    CampoOverlay,
    Fuente,
    OverlayConfig,
    PosicionBase,
)


def test_from_json_empty_uses_defaults():
    cfg = OverlayConfig.from_json({})
    assert cfg.fuente == Fuente()
    assert cfg.posicion_base == PosicionBase()
    assert cfg.campos_solicitud == {}
    assert cfg.data_source is None


def test_from_json_parses_campos_and_fuente():
    data = {
        "campos_solicitud": {
            "folio": {"visible": True, "label": "Folio", "x": 10, "y": 20, "posiciones": []},
        },
        "fuente": {"nombre": "Times-Roman", "tamaño": 12},
        "data_source": "solicitud",
    }
    cfg = OverlayConfig.from_json(data)
    campo = cfg.campos_solicitud["folio"]
    assert isinstance(campo, CampoOverlay)
    assert campo.visible is True and campo.x == 10 and campo.y == 20
    assert cfg.fuente.nombre == "Times-Roman" and cfg.fuente.tamano == 12
    assert cfg.data_source == "solicitud"


def test_posicion_alias_backward_compat():
    cfg = OverlayConfig.from_json({"posicion": {"x_left": 99}})
    assert cfg.posicion_base.x_left == 99


def test_to_json_roundtrip_preserves_tamano_key():
    cfg = OverlayConfig.from_json(
        {
            "fuente": {"nombre": "Helvetica", "tamaño": 8},
            "campos_participantes": {
                "curp": {
                    "visible": True,
                    "label": "CURP",
                    "posiciones": [{"x": 1, "y": 2, "page": 1}],
                }
            },
        }
    )
    out = cfg.to_json()
    assert out["fuente"]["tamaño"] == 8
    assert out["campos_participantes"]["curp"]["posiciones"] == [{"x": 1, "y": 2, "page": 1}]
    # round-trip stable
    assert OverlayConfig.from_json(out).to_json() == out


def test_campos_merges_groups_solicitud_first():
    cfg = OverlayConfig.from_json(
        {
            "campos_solicitud": {"folio": {"visible": True, "label": "F"}},
            "campos_participantes": {"curp": {"visible": True, "label": "C"}},
        }
    )
    merged = cfg.campos()
    assert list(merged.keys()) == ["folio", "curp"]
