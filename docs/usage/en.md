# Usage — English

## Installation

```bash
pip install "sinpapel-reports @ git+ssh://git@github.com/aprendomx/sinpapel-reports.git@v0.1.0"
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
and define overlay fields:

```json
{
  "data_source": "solicitud",
  "campos": [
    {"key": "folio", "label": "Folio", "x": 100, "y": 200, "pagina": 1}
  ]
}
```

## Generating a document

```python
from sinpapel_reports.services.report_engine import ReportEngine

resultado = ReportEngine.generar(documento, target_obj)
# resultado.instancia is the saved InstanciaDocumento
# resultado.path is the output file path
```

To generate multiple documents and receive a ZIP bundle:

```python
resultado_paquete = ReportEngine.generar_paquete(documentos, target_obj)
# resultado_paquete.zip_path is the ZIP file path
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

Available endpoints:

| Method | Path | Description |
|--------|------|-------------|
| GET | `/reports/documentos/<pk>/field-catalog/` | List available fields for the document's data source |
| GET | `/reports/documentos/<pk>/overlay-config/` | Retrieve current overlay configuration |
| POST | `/reports/documentos/<pk>/generate/` | Generate a document and return its URL |
| GET | `/reports/instancias/<pk>/download/` | Download a generated document |
