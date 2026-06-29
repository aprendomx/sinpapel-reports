# sinpapel-reports — Design Spec

**Date:** 2026-06-29
**Status:** Approved (brainstorming) — pending implementation plan
**Authors:** Julio Adrián + Rai

---

## 1. Purpose

Extract the WYSIWYG **PDF/DOCX overlay-document generator** currently embedded in the
`creditos` Django admin into a standalone, reusable framework — `sinpapel-reports` —
that is native to and harmonious with the `sinpapel` ecosystem, and that can be
integrated into platforms other than `creditos`.

The tool being extracted lets an operator take a **template** (a PDF or a DOCX file)
and produce per-record output documents by **stamping live data onto the template at
pixel coordinates** (PDF, via ReportLab + PyPDF2) or **filling template placeholders**
(DOCX, via docxtpl), optionally bundling many into a ZIP.

It is **not** a charts/BI/aggregation report builder. "Report" here means
*generated document from template + data*.

### Origin (in creditos, read-only reference)

| Concern | Location today | Disposition |
|---|---|---|
| Visual editor (drag-drop PDF canvas, palette, ~2,100 LOC inline JS) | `creditos/widgets.py` | **Stays in creditos / future `sinpapel-reports-designer` SPA** — out of this repo |
| Overlay JSON schema | `Documento.configuracion_overlay` (JSONField, in `sinpapel` core) | **Reused**; interpreted by this framework |
| PDF overlay renderer | `instancia_documento_service.py::_create_pdf_overlays / _process_pdf_template` | **Extracted** → `OverlayRenderer` |
| DOCX fill renderer | `instancia_documento_service.py::_process_docx_template` | **Extracted** → `DocxRenderer` |
| Context builder (Solicitud-specific) | `instancia_documento_service.py::_build_context_for_documento` | **Replaced** by pluggable `ReportDataSource`; creditos re-implements as an adapter (Phase 2) |
| Field palettes (hardcoded credit fields) | widget + service defaults | **Replaced** by `ReportDataSource.get_field_catalog()` |
| Output model | `InstanciaDocumento` (in `sinpapel` core) | **Reused** |
| `PlantillaDocumento` / "Tú Construyes" DOCX path | `plantilla_service.py` | **Out of scope v0.1.0** (different model) — later consolidation candidate |

---

## 2. Decisions (from brainstorming)

1. **Scope:** PDF overlay **and** DOCX template generation, both against `Documento`.
2. **Editor delivery:** standalone Vue SPA (a separate `sinpapel-reports-designer` repo,
   built later) — so **this repo is backend-only** and exposes the data the SPA consumes.
3. **Repo split:** `sinpapel-reports` = the Django backend framework at
   `/Users/jadrians/aprendo/sinpapel-reports`; the designer SPA is a separate sibling repo.
4. **Models:** **reuse** `sinpapel` core's `Documento` + `InstanciaDocumento` (depend on
   `sinpapel@v0.7.0`). No new tables, no migration of the overlay concern out of core.
5. **REST layer:** **bundled** in `sinpapel-reports` behind an optional `drf` extra,
   gated on settings — not a separate `sinpapel-reports-drf` sibling (for now).
6. **Data seam:** **Registry of named data sources** (Approach A) — Protocol + decorator +
   autodiscovery, mirroring `sinpapel-webhooks` autodiscovery and `side_effects` registration.

### Data-seam alternatives considered

- **A — Registry of named data sources (CHOSEN).** `ReportDataSource` Protocol +
  `@register_data_source` + `autodiscover_modules("reports")`. Supports multiple targets,
  curated labels, computed/derived fields. Most native to the ecosystem.
- **B — Single settings-based provider.** `SINPAPEL_REPORTS_DATA_SOURCE` + `lru_cache`
  factory (like the signing backend). Simpler but only one global provider.
- **C — Auto-introspect `model._meta`.** Zero-config but too magic; can't express
  computed/Spanish-labelled/participant sub-fields cleanly.

---

## 3. Architecture

### Package shape (mirrors `sinpapel` core conventions)

- Distribution `sinpapel-reports`, import package `sinpapel_reports`, **flat layout**
  (package at repo root via explicit `[tool.setuptools.package-dir]` + enumerated
  `packages`), `py.typed`, dual `README.md` / `README.es.md`, Keep-a-Changelog
  `CHANGELOG.md`, mkdocs + mkdocstrings, GPL-3.0-or-later.
- `requires-python >= 3.10`. Dependencies: `sinpapel @ git+ssh://…@v0.7.0`,
  `PyPDF2>=3.0`, `reportlab>=4.4`, `docxtpl`. Optional extras: `drf`
  (`djangorestframework>=3.14`), `dev` (pytest>=9, pytest-django, build, twine),
  `docs` (mkdocs, mkdocs-material, mkdocstrings[python]).
- `apps.py` → `class SinpapelReportsConfig(AppConfig)`, `name = "sinpapel_reports"`,
  `default_auto_field = "django.db.models.BigAutoField"`, Spanish `verbose_name`.
  `ready()` runs `autodiscover_modules("reports")` (host apps declare a `reports.py`).
- Settings prefix `SINPAPEL_REPORTS_*`, always read lazily via
  `getattr(settings, "SINPAPEL_REPORTS_X", default)` — never required at import.
- Version hardcoded in `pyproject.toml` `[project]` and mirrored in `__init__.__version__`.

### Directory layout

```
sinpapel_reports/
  __init__.py            # __version__
  apps.py                # SinpapelReportsConfig.ready() -> autodiscover_modules("reports")
  exceptions.py          # SinpapelReportsError base + specific errors
  registry.py            # ReportDataSourceRegistry singleton + @register_data_source
  data_sources.py        # ReportDataSource Protocol, CampoReporte, FakeDataSource
  schemas/
    __init__.py
    overlay.py           # OverlayConfig / CampoOverlay / PosicionBase / Fuente + (de)serialize
  services/
    __init__.py
    overlay_renderer.py  # OverlayRenderer (PDF: ReportLab + PyPDF2)
    docx_renderer.py     # DocxRenderer (docxtpl)
    report_engine.py     # ReportEngine facade (generar / generar_paquete)
  drf/                   # optional, gated on DRF availability
    __init__.py
    serializers.py
    views.py
    urls.py
  tests/
    settings.py
    conftest.py
    ...
  docs/                  # mkdocs site (usage en/es, api, development/changelog)
```

### Components

**3.1 Schema — `schemas/overlay.py`**
Frozen dataclasses modelling the existing `configuracion_overlay` JSON exactly:
- `Fuente(nombre: str = "Helvetica", tamaño: int = 10)`
- `PosicionBase(x_left, y_top_offset, line_height)`
- `CampoOverlay(visible: bool, label: str, x, y, posiciones: list[...])`
- `OverlayConfig(campos_solicitud: dict[str, CampoOverlay], campos_participantes: dict[str, CampoOverlay], posicion_base: PosicionBase, fuente: Fuente)`
- `OverlayConfig.from_json(dict)` / `.to_json()` — shallow-merge over defaults at load;
  preserve the **retro-compat alias** `posicion → posicion_base`.
- Schema version constant (`SCHEMA_VERSION = "0.x"`) for forward compatibility, paralleling
  the designer's `v0.2` portable schema.

> Note: field-group keys `campos_solicitud` / `campos_participantes` are retained verbatim
> for backward compatibility with stored configs. They are treated as generic
> "primary fields" / "repeated/related fields" groups; the data source supplies their
> contents, so the names are host-agnostic in practice.

**3.2 Data-source seam — `data_sources.py` + `registry.py`**
- `CampoReporte(key: str, label: str, grupo: str)` — one palette entry.
- `ReportDataSource` `@runtime_checkable` Protocol:
  - `name: ClassVar[str]`
  - `get_field_catalog() -> list[CampoReporte]` — drives the palette.
  - `build_context(target: Any) -> dict[str, Any]` — drives rendering.
- `ReportDataSourceRegistry` (private `_RegistryImpl`, public module-level singleton),
  idempotent re-register (autoreload/test-safe), `unregister()` for tests,
  `get(name)` / `list()`.
- `@register_data_source` decorator.
- `FakeDataSource` — deterministic test adapter implementing the Protocol.
- Host apps register theirs in `reports.py`; discovered via `autodiscover_modules("reports")`.

**3.3 Renderers — `services/`**
- `OverlayRenderer` — extracted PDF stamping: `PdfReader(template)` →
  per-page ReportLab canvas overlay from `OverlayConfig` + context → `merge_page` →
  `PdfWriter`. Pure function of (template file, `OverlayConfig`, context dict).
- `DocxRenderer` — `docxtpl` template fill from context dict.
- `ReportEngine` facade:
  - `generar(documento, target) -> InstanciaDocumento` — resolve data source by name,
    `build_context(target)`, pick renderer by `documento.tipo_plantilla` (`PDF`|`DOCX`),
    render, persist `InstanciaDocumento` (GenericForeignKey `target`/`actor`,
    `archivo_generado`).
  - `generar_paquete(documento, targets) -> bytes|file` — ZIP bundle.
  - Spanish public verbs (`generar`, `generar_paquete`), English plumbing internally.
  - How a `Documento` names its data source is decided in the plan (preferred: a key in
    `configuracion_overlay`, e.g. `"data_source": "<name>"`, to avoid a core model change;
    fallback documented if that proves insufficient).

**3.4 REST — `drf/` (optional, gated on `settings` + DRF import)**
Serializers + a viewset exposing what the future SPA needs:
- `GET  field-catalog?source=<name>` → palette (`list[CampoReporte]`)
- `GET/PUT overlay-config` for a `Documento` (read/write `configuracion_overlay`)
- `POST generate` / `POST generate-package`
- `GET  download` (the generated file / ZIP)
Mountable: `path("sinpapel/reports/api/", include("sinpapel_reports.drf.urls"))`.

---

## 4. Error handling

- Custom exceptions subclass a base `SinpapelReportsError` (`exceptions.py`), e.g.
  `DataSourceNotFoundError`, `UnsupportedTemplateError`, `OverlaySchemaError`.
- `ReportEngine.generar` raises on: unknown data source, unsupported `tipo_plantilla`,
  malformed `OverlayConfig`. Rendering is atomic per record; package generation skips and
  reports per-record failures without aborting the whole batch (decision deferred to plan).
- DRF layer maps framework exceptions to appropriate HTTP status codes.

---

## 5. Testing

- pytest + pytest-django; `tests/settings.py` minimal in-memory sqlite, `INSTALLED_APPS`
  with `contenttypes`, `auth`, `simple_history`, `sinpapel`, `sinpapel_reports`, plus a
  test app registering a `FakeDataSource`.
- `conftest.py`: autouse registry cleanup (`ReportDataSourceRegistry.unregister`) and any
  cache cleanup, mirroring core's conftest discipline.
- Coverage: schema round-trip (incl. `posicion` alias), registry idempotency/discovery,
  `OverlayRenderer` stamps at expected coordinates, `DocxRenderer` fills placeholders,
  `ReportEngine.generar` end-to-end with `FakeDataSource`, ZIP packaging, DRF endpoints.
- `test_no_creditos_dep.py` guard — the framework must not import any creditos symbol.

---

## 6. Scope boundaries

**In scope (v0.1.0):**
- Schema, data-source seam, both renderers, `ReportEngine`, optional DRF layer, tests,
  packaging, docs — all decoupled from creditos, validated with `FakeDataSource`.

**Out of scope (v0.1.0), flagged for follow-up:**
- **Phase 2 — creditos integration:** creditos declares `reports.py` with a
  `SolicitudDataSource` (wrapping today's `_build_context_for_documento` + palettes),
  deletes the duplicated kernel from `instancia_documento_service.py`, and delegates to
  `ReportEngine`. This is the proof the extraction works.
- **`sinpapel-reports-designer`** Vue SPA editor (separate repo, later).
- **`plantilla_service.py` / `PlantillaDocumento`** consolidation (different model).
- Charts/BI/aggregation — explicitly never in scope.

---

## 7. Ecosystem fit checklist

- [ ] Flat layout, explicit `packages`/`package-dir`, `py.typed`, version mirrored in `__init__`.
- [ ] `SinpapelReportsConfig.ready()` autodiscovers `reports.py` (webhooks pattern).
- [ ] Settings read lazily, `SINPAPEL_REPORTS_*` prefix.
- [ ] Protocol + registry + decorator for extensibility (signing/side-effects pattern).
- [ ] Core (`sinpapel`) imports nothing from this package (one-directional coupling).
- [ ] Spanish domain vocabulary, English infra plumbing; Spanish Google-style docstrings.
- [ ] `from __future__ import annotations`, modern type hints, frozen dataclasses (no Pydantic).
- [ ] Keep-a-Changelog, dual README, mkdocs, ADRs by number.
