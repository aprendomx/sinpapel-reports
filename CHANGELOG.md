# Changelog

All notable changes to this project are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this project adheres to [SemVer](https://semver.org/).

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
