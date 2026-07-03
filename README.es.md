# sinpapel-reports

Generación de documentos basada en plantillas (superposición PDF + DOCX), enchufable
al ecosistema [sinpapel](https://github.com/aprendomx/sinpapel).

## Qué hace

Renderiza documentos por registro estampando datos en vivo sobre una plantilla PDF en
coordenadas de píxel (ReportLab + PyPDF2) o rellenando una plantilla DOCX (docxtpl).
La salida se persiste como `sinpapel.InstanciaDocumento`, opcionalmente empaquetada en
un ZIP.

## Instalación

```bash
pip install "sinpapel-reports @ git+ssh://git@github.com/aprendomx/sinpapel-reports.git@v0.2.0"
```

Agrega `"sinpapel_reports"` a `INSTALLED_APPS` (después de `"sinpapel"`).

## Conecta tus datos

Declara un archivo `reports.py` en cualquier app instalada:

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

Apunta `Documento.configuracion_overlay["data_source"]` a `"solicitud"` y llama a
`ReportEngine.generar(documento, target)`.

## REST (opcional)

Instala el extra `drf` e incluye `"sinpapel_reports.drf.urls"` en tu URLconf.

Endpoints (relativos al prefijo de montaje):

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `field-catalog/?source=<nombre>` | Paleta de campos de la fuente indicada |
| GET | `documentos/<pk>/overlay-config/` | Lee la configuración de overlay almacenada |
| PUT | `documentos/<pk>/overlay-config/` | Persiste configuración de overlay (validada) |
| POST | `documentos/<pk>/generate/` | Genera; devuelve `{"instancia_id","filename"}` |
| GET | `instancias/<pk>/download/` | Descarga el archivo generado como adjunto |

**Auth:** las vistas exigen `IsAuthenticated` por defecto. Sobreescríbelo vía `settings.SINPAPEL_REPORTS_PERMISSION_CLASSES`.

**Extensibilidad:** registra renderers adicionales con `ReportEngine.register_renderer("XLSX", mi_renderer)`.

## Licencia

GPL-3.0-or-later.
