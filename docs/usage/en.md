# Usage — English

## Installation

```bash
pip install "sinpapel-reports @ git+ssh://git@github.com/aprendomx/sinpapel-reports.git@v0.2.0"
```

Add `"sinpapel_reports"` to `INSTALLED_APPS` (after `"sinpapel"`).

## Registering a data source

Create a `reports.py` file in any installed Django app. The framework autodiscovers it
on startup via `AppConfig.ready()`.

```python
from sinpapel_reports.data_sources import CampoReporte, register_data_source

@register_data_source
class SolicitudDataSource:
    name = "solicitud"

    def get_field_catalog(self) -> list[CampoReporte]:
        return [
            CampoReporte(key="folio", label="Folio"),
            CampoReporte(key="monto", label="Monto", grupo="financiero"),
        ]

    def build_context(self, target) -> dict:
        return {"folio": target.id, "monto": str(target.monto)}
```

## Configuring a Documento

Set `configuracion_overlay` on your `sinpapel.Documento` to point at the data source
and define overlay fields (schema in `sinpapel_reports.schemas.overlay.OverlayConfig`):

```json
{
  "data_source": "solicitud",
  "campos_solicitud": {
    "folio": {"visible": true, "label": "Folio", "x": 100, "y": 200, "posiciones": []},
    "curp":  {"visible": true, "label": "CURP", "posiciones": [
      {"x": 100, "y": 200, "page": 2}
    ]}
  },
  "campos_participantes": {},
  "posicion_base": {"x_left": 50, "y_top_offset": 50, "line_height": 15},
  "fuente": {"nombre": "Helvetica", "tamaño": 10}
}
```

Notes:

- Fields live in the `campos_solicitud` / `campos_participantes` dicts, keyed by
  the data-source field `key`. Fields default to `"visible": false` and are
  skipped unless set to `true`.
- The `y` coordinate is measured from the **top** of the page (the renderer draws
  at `page_height - y`).
- If **any** field defines `posiciones` (entries `{x, y, page}`, `page` 1-based),
  the renderer runs in multi-position mode; otherwise fields without `x`/`y` are
  stacked vertically starting at `posicion_base` on the first page.
- Falsy values (`0`, `""`, `None`) are not stamped — return strings from
  `build_context` if you need to print zeros.

## Generating a document

```python
from sinpapel_reports.services.report_engine import ReportEngine

resultado = ReportEngine.generar(documento, target_obj, actor=request.user)
# ResultadoGeneracion (frozen dataclass):
#   resultado.instancia_id  — pk of the saved InstanciaDocumento
#   resultado.filename      — storage name (documentos_generados/...)
#   resultado.contenido     — rendered bytes
```

`actor` and `data_source` are optional keyword-only arguments. The data source is
resolved in order: `data_source` argument → `configuracion_overlay["data_source"]`
→ `settings.SINPAPEL_REPORTS_DEFAULT_DATA_SOURCE` → raises `DataSourceNotFoundError`.

To generate one document per target and receive a ZIP bundle (single transaction,
all-or-nothing):

```python
paquete = ReportEngine.generar_paquete(documento, [t1, t2, t3], actor=request.user)
# ResultadoPaquete:
#   paquete.generaciones  — list[ResultadoGeneracion]
#   paquete.zip_bytes     — in-memory ZIP content
#   paquete.zip_filename  — "<slug>_paquete.zip"
```

The individual `InstanciaDocumento` records are persisted; the ZIP only exists in
memory (`zip_bytes`) — serve it yourself (e.g. in an `HttpResponse`).

### Custom renderers

`"PDF"` and `"DOCX"` renderers come pre-registered. Register additional formats
(or replace an existing one) with:

```python
def xlsx_renderer(path: str, contexto: dict, documento) -> tuple[bytes, str]:
    ...
    return contenido_bytes, "xlsx"

ReportEngine.register_renderer("XLSX", xlsx_renderer)
```

## REST layer (optional)

Include the DRF URLs after installing the `drf` extra:

```python
# urls.py
from django.urls import include, path

urlpatterns = [
    path("reports/", include("sinpapel_reports.drf.urls")),
]
```

Available endpoints (relative to the mount prefix, e.g. `/reports/`):

| Method | Path | Description |
|--------|------|-------------|
| GET | `field-catalog/?source=<name>` | Return `[{key, label, grupo}]` for the named data source |
| GET | `documentos/<pk>/overlay-config/` | Return the stored `configuracion_overlay` JSON |
| PUT | `documentos/<pk>/overlay-config/` | Persist a new overlay config (validated); returns the saved config |
| POST | `documentos/<pk>/generate/` | Generate a document; body: `{target_content_type, target_object_id, data_source?}`; returns `{"instancia_id", "filename"}` |
| GET | `instancias/<pk>/download/` | Stream the generated file as a download attachment |

## Security / auth

Since 0.2.0 the DRF views require `IsAuthenticated` by default. Override the
permission classes for all four views via settings:

```python
SINPAPEL_REPORTS_PERMISSION_CLASSES = [MyPermission]  # list of classes, not dotted paths
```

Note that `permission_classes` is evaluated at module import time, so the setting
must be defined in the project settings before startup (`override_settings` in
tests has no effect).

`POST documentos/<pk>/generate/` additionally performs a basic ownership check on
the target: if the target has an `owner`, `usuario` or `creado_por` attribute
(first non-None wins), it must equal `request.user` (403 otherwise). Targets with
none of those attributes are assumed to be access-controlled by the host — wrap
the views or supply your own permission class for finer-grained rules; otherwise
authenticated users can reach documents by sequential pk.
