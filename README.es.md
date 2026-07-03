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
pip install "sinpapel-reports @ git+ssh://git@github.com/aprendomx/sinpapel-reports.git@v0.1.0"
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

## Licencia

GPL-3.0-or-later.
