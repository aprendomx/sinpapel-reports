# sinpapel-reports

Pluggable, template-driven document generation (PDF overlay + DOCX) for the
[sinpapel](https://github.com/aprendomx/sinpapel) ecosystem.

## What it does

Render per-record documents by stamping live data onto a PDF template at pixel
coordinates (ReportLab + PyPDF2) or filling a DOCX template (docxtpl). Output is
persisted as `sinpapel.InstanciaDocumento`, optionally bundled as a ZIP.

## Install

```bash
pip install "sinpapel-reports @ git+ssh://git@github.com/aprendomx/sinpapel-reports.git@v0.1.0"
```

Add `"sinpapel_reports"` to `INSTALLED_APPS` (after `"sinpapel"`).

## Plug in your data

Declare a `reports.py` in any installed app:

```python
from sinpapel_reports.data_sources import CampoReporte, register_data_source

@register_data_source
class SolicitudDataSource:
    name = "solicitud"
    def get_field_catalog(self):
        return [CampoReporte(key="folio", label="Folio")]
    def build_context(self, target):
        return {"folio": target.id}
```

Point a `Documento.configuracion_overlay["data_source"]` at `"solicitud"` and call
`ReportEngine.generar(documento, target)`.

## REST (optional)

Install the `drf` extra and `include("sinpapel_reports.drf.urls")`.

Endpoints (relative to the mount prefix):

| Method | Path | Description |
|--------|------|-------------|
| GET | `field-catalog/?source=<name>` | Field palette for the named data source |
| GET | `documentos/<pk>/overlay-config/` | Read stored overlay config |
| PUT | `documentos/<pk>/overlay-config/` | Persist overlay config (validated) |
| POST | `documentos/<pk>/generate/` | Generate; returns `{"instancia_id","filename"}` |
| GET | `instancias/<pk>/download/` | Download generated file as attachment |

**Auth:** views delegate to the host's `DEFAULT_PERMISSION_CLASSES`; configure appropriately.

## License

GPL-3.0-or-later.
