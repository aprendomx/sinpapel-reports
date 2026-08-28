# Changelog

All notable changes to this project are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this project adheres to [SemVer](https://semver.org/).

## [0.2.4] — 2026-08-28

### Security
- **Reemplaza `PyPDF2` por `pypdf`.** `PyPDF2` quedó descontinuado en 3.0.1 y
  arrastra PYSEC-2026-1835 (bucle infinito al parsear un PDF manipulado: DoS
  de un core al 100 %). El proyecto se renombró a `pypdf` y 3.0.1 nunca va a
  recibir el parche, así que no había versión de PyPDF2 a la que actualizar.
  `pypdf` expone la misma API (`PdfReader`, `PdfWriter`, `merge_page`,
  `add_page`), de modo que el cambio es transparente para los consumidores.

### Changed
- `OverlayRenderer.render` construye el writer con `PdfWriter(clone_from=...)`
  y fusiona sobre páginas ya adjuntas. Fusionar sobre páginas sueltas para
  añadirlas después está deprecado en pypdf (se elimina en 7.0) y su propia
  documentación lo describe como poco fiable. El resultado renderizado no
  cambia.
- Retirado el filtro `ignore::DeprecationWarning:PyPDF2` de la config de
  pytest: ya no hay nada que silenciar. La suite pasa con
  `-W error::DeprecationWarning`.

## [0.2.0] — 2026-07-03

### Added
- CI/CD: GitHub Actions workflow (tests, lint, type-check, coverage ≥ 85 %).
- Pre-commit hooks (ruff) and full `pyproject.toml` tooling (`ruff`, `mypy`, `pytest-cov`).
- Renderer registry: `ReportEngine.register_renderer(tipo, callable)` para soportar nuevos formatos sin modificar el core.
- Validación de ownership básica en `GenerateView` (`owner`, `usuario`, `creado_por`).
- Tests de seguridad DRF (403 sin auth, 403 por ownership) y tests de transaccionalidad.
- `tests/utils.py` con helpers compartidos (`_blank_pdf_bytes`, `_blank_pdf`).

### Changed
- **Breaking:** las vistas DRF ahora exigen `IsAuthenticated` por defecto (sobreescribible vía `SINPAPEL_REPORTS_PERMISSION_CLASSES`).
- `OverlayRenderer._build_overlays` refactorizado en `_render_sequential` / `_render_multi_position` (baja complejidad ciclomática).
- Excepciones silenciadas reemplazadas por `logger.warning` con contexto.
- `OverlayConfigView.put` ahora atrapa solo `TypeError`, `ValueError`, `KeyError`, `AttributeError` (no `Exception` genérico).
- `pytest.ini` migrado a `[tool.pytest.ini_options]` en `pyproject.toml`.

## [0.1.0] — 2026-06-29

### Added
- Initial extraction of the WYSIWYG overlay generator into a standalone framework.
- `OverlayConfig` schema (frozen dataclasses) with JSON round-trip and `posicion` backward-compat alias.
- `ReportDataSource` Protocol + registry + `@register_data_source` + autodiscovery of host `reports.py`.
- `OverlayRenderer` (PDF, ReportLab + PyPDF2) and `DocxRenderer` (docxtpl).
- `ReportEngine` facade: `generar` / `generar_paquete` persisting `InstanciaDocumento`, with ZIP packaging.
- Optional DRF layer: field-catalog, overlay-config, generate, download.
- Reuses `sinpapel` core `Documento` / `InstanciaDocumento` (no new tables).
