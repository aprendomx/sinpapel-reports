# Guía de uso — Español

## Instalación

```bash
pip install "sinpapel-reports @ git+ssh://git@github.com/aprendomx/sinpapel-reports.git@v0.1.0"
```

Agrega `"sinpapel_reports"` a `INSTALLED_APPS` (después de `"sinpapel"`).

## Registrar una fuente de datos

Crea un archivo `reports.py` en cualquier app Django instalada. El framework lo
autodescubre al inicio a través de `AppConfig.ready()`.

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

## Configurar un Documento

Establece `configuracion_overlay` en tu `sinpapel.Documento` para apuntar a la fuente
de datos y definir los campos de superposición:

```json
{
  "data_source": "solicitud",
  "campos": [
    {"key": "folio", "label": "Folio", "x": 100, "y": 200, "pagina": 1}
  ]
}
```

## Generar un documento

```python
from sinpapel_reports.services.report_engine import ReportEngine

resultado = ReportEngine.generar(documento, target_obj)
# resultado.instancia es el InstanciaDocumento guardado
# resultado.path es la ruta del archivo de salida
```

Para generar múltiples documentos y recibir un paquete ZIP:

```python
resultado_paquete = ReportEngine.generar_paquete(documentos, target_obj)
# resultado_paquete.zip_path es la ruta del archivo ZIP
```

## Capa REST (opcional)

Incluye las URLs de DRF después de instalar el extra `drf`:

```python
# urls.py
from django.urls import include, path

urlpatterns = [
    path("reports/", include("sinpapel_reports.drf.urls")),
]
```

Endpoints disponibles:

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/reports/documentos/<pk>/field-catalog/` | Lista los campos disponibles de la fuente de datos del documento |
| GET | `/reports/documentos/<pk>/overlay-config/` | Obtiene la configuración de superposición actual |
| POST | `/reports/documentos/<pk>/generate/` | Genera un documento y devuelve su URL |
| GET | `/reports/instancias/<pk>/download/` | Descarga un documento generado |
