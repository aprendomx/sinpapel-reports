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

Endpoints disponibles (relativos al prefijo de montaje, p. ej. `/reports/`):

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `field-catalog/?source=<nombre>` | Devuelve `[{key, label, grupo}]` para la fuente de datos indicada |
| GET | `documentos/<pk>/overlay-config/` | Devuelve el JSON `configuracion_overlay` almacenado |
| PUT | `documentos/<pk>/overlay-config/` | Persiste una nueva configuración de overlay (validada); devuelve la config guardada |
| POST | `documentos/<pk>/generate/` | Genera un documento; body: `{target_content_type, target_object_id, data_source?}`; devuelve `{"instancia_id", "filename"}` |
| GET | `instancias/<pk>/download/` | Descarga el archivo generado como adjunto |

## Seguridad / autenticación

Las vistas DRF de este paquete **no** definen `permission_classes` propias.
Delegan completamente a `DEFAULT_PERMISSION_CLASSES` del proyecto anfitrión.
El anfitrión **debe** configurar un default apropiado (p. ej. `[IsAuthenticated]`)
o envolver el `include(...)` con sus propios permisos; de lo contrario, las vistas
sirven y mutan documentos por pk secuencial sin ninguna restricción de acceso.
