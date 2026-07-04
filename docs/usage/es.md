# Guía de uso — Español

## Instalación

```bash
pip install "sinpapel-reports @ git+ssh://git@github.com/aprendomx/sinpapel-reports.git@v0.2.0"
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
de datos y definir los campos de superposición (esquema en
`sinpapel_reports.schemas.overlay.OverlayConfig`):

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

Notas:

- Los campos viven en los dicts `campos_solicitud` / `campos_participantes`,
  indexados por el `key` de la fuente de datos. El default es
  `"visible": false`: un campo no se estampa salvo que lo pongas en `true`.
- La coordenada `y` se mide desde el borde **superior** de la página (el
  renderer dibuja en `alto_página - y`).
- Si **algún** campo define `posiciones` (entradas `{x, y, page}`, `page`
  1-based), el renderer opera en modo multi-posición; si no, los campos sin
  `x`/`y` se apilan verticalmente desde `posicion_base` en la primera página.
- Los valores falsy (`0`, `""`, `None`) no se estampan — devuelve strings desde
  `build_context` si necesitas imprimir ceros.

## Generar un documento

```python
from sinpapel_reports.services.report_engine import ReportEngine

resultado = ReportEngine.generar(documento, target_obj, actor=request.user)
# ResultadoGeneracion (dataclass frozen):
#   resultado.instancia_id  — pk del InstanciaDocumento guardado
#   resultado.filename      — name de storage (documentos_generados/...)
#   resultado.contenido     — bytes renderizados
```

`actor` y `data_source` son argumentos keyword-only opcionales. La fuente de
datos se resuelve en orden: argumento `data_source` →
`configuracion_overlay["data_source"]` →
`settings.SINPAPEL_REPORTS_DEFAULT_DATA_SOURCE` → lanza
`DataSourceNotFoundError`.

Para generar un documento por target y recibir un paquete ZIP (una sola
transacción, todo o nada):

```python
paquete = ReportEngine.generar_paquete(documento, [t1, t2, t3], actor=request.user)
# ResultadoPaquete:
#   paquete.generaciones  — list[ResultadoGeneracion]
#   paquete.zip_bytes     — contenido del ZIP en memoria
#   paquete.zip_filename  — "<slug>_paquete.zip"
```

Las `InstanciaDocumento` individuales se persisten; el ZIP solo existe en
memoria (`zip_bytes`) — sírvelo tú (p. ej. en un `HttpResponse`).

### Renderers custom

`"PDF"` y `"DOCX"` vienen pre-registrados. Registra formatos adicionales (o
reemplaza uno existente) con:

```python
def xlsx_renderer(path: str, contexto: dict, documento) -> tuple[bytes, str]:
    ...
    return contenido_bytes, "xlsx"

ReportEngine.register_renderer("XLSX", xlsx_renderer)
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

Desde 0.2.0 las vistas DRF exigen `IsAuthenticated` por defecto. Sobreescribe
las permission classes de las cuatro vistas vía settings:

```python
SINPAPEL_REPORTS_PERMISSION_CLASSES = [MiPermiso]  # lista de clases, no dotted paths
```

Ten en cuenta que `permission_classes` se evalúa al importar el módulo, así que
el setting debe definirse en el settings del proyecto antes de arrancar
(`override_settings` en tests no tiene efecto).

`POST documentos/<pk>/generate/` además hace un check básico de ownership sobre
el target: si el target tiene un atributo `owner`, `usuario` o `creado_por`
(gana el primero no-None), debe ser igual a `request.user` (403 en caso
contrario). Los targets sin ninguno de esos atributos se asumen controlados por
el anfitrión — envuelve las vistas o define tu propia permission class para
reglas más finas; de lo contrario, cualquier usuario autenticado alcanza los
documentos por pk secuencial.
