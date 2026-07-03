# Changelog

All notable changes to this project are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this project adheres to [SemVer](https://semver.org/).

## [0.1.0] — 2026-06-29

### Added
- Initial extraction of the WYSIWYG overlay generator into a standalone framework.
- `OverlayConfig` schema (frozen dataclasses) with JSON round-trip and `posicion` backward-compat alias.
- `ReportDataSource` Protocol + registry + `@register_data_source` + autodiscovery of host `reports.py`.
- `OverlayRenderer` (PDF, ReportLab + PyPDF2) and `DocxRenderer` (docxtpl).
- `ReportEngine` facade: `generar` / `generar_paquete` persisting `InstanciaDocumento`, with ZIP packaging.
- Optional DRF layer: field-catalog, overlay-config, generate, download.
- Reuses `sinpapel` core `Documento` / `InstanciaDocumento` (no new tables).
