# sinpapel-reports

Pluggable, template-driven document generation (PDF overlay + DOCX) for the
[sinpapel](https://github.com/aprendomx/sinpapel) ecosystem.

## What it does

Render per-record documents by stamping live data onto a PDF template at pixel
coordinates (ReportLab + pypdf) or filling a DOCX template (docxtpl). Output is
persisted as `sinpapel.InstanciaDocumento`, optionally bundled as a ZIP.

## Install

```bash
pip install sinpapel-reports
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

**Auth:** views require `IsAuthenticated` by default. Override via `settings.SINPAPEL_REPORTS_PERMISSION_CLASSES`.

**Extensibility:** register custom renderers with `ReportEngine.register_renderer("XLSX", my_renderer)`.

## License

Copyright (C) 2024-2026 Julio Adrián.

sinpapel-reports is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

sinpapel-reports is distributed in the hope that it will be useful, but **WITHOUT ANY WARRANTY**; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the [GNU General Public License](https://github.com/aprendomx/sinpapel-reports/blob/main/LICENSE) for more details.
