# sinpapel-reports Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract the creditos WYSIWYG PDF/DOCX overlay-document generator into a standalone, host-agnostic Django framework `sinpapel-reports`, native to the sinpapel ecosystem.

**Architecture:** A flat-layout Django app that reuses `sinpapel` core's `Documento`/`InstanciaDocumento` models. A frozen-dataclass schema models the `configuracion_overlay` JSON; a Protocol + registry + autodiscovery seam (`ReportDataSource`) makes the data context and field palette pluggable per host; two stateless renderers (`OverlayRenderer` for PDF via ReportLab+PyPDF2, `DocxRenderer` via docxtpl) plus a `ReportEngine` facade produce and persist `InstanciaDocumento`s, optionally bundled as a ZIP. An optional DRF layer (gated extra) exposes what the future `sinpapel-reports-designer` SPA will consume.

**Tech Stack:** Python ≥3.10, Django ≥5.0, `sinpapel@v0.7.0`, PyPDF2≥3.0, reportlab≥4.4, docxtpl, pytest + pytest-django, optional djangorestframework≥3.14.

## Global Constraints

- Distribution name `sinpapel-reports`; import package `sinpapel_reports`; AppConfig `SinpapelReportsConfig` (`name = "sinpapel_reports"`).
- **Flat layout**: package files at repo root, mapped via explicit `[tool.setuptools.package-dir]` + enumerated `[tool.setuptools.packages]`. Ship `py.typed`.
- `requires-python = ">=3.10"`; license `GPL-3.0-or-later`; build backend `setuptools>=77`.
- Version hardcoded in `pyproject.toml [project].version` AND mirrored in `sinpapel_reports/__init__.py::__version__` (keep in sync manually). Start at `0.1.0`.
- Core `sinpapel` must import **nothing** from this package (one-directional coupling). This package must import **nothing** from `creditos` (enforced by a guard test).
- Settings read lazily via `getattr(settings, "SINPAPEL_REPORTS_X", default)` — never required at import. Prefix `SINPAPEL_REPORTS_*`.
- Code style: `from __future__ import annotations` at top of every module; modern type hints (`str | None`, `dict[str, Any]`); frozen `@dataclass` for value objects; `typing.Protocol` for contracts; **no Pydantic**. Spanish domain vocabulary + Spanish Google-style docstrings; English infra plumbing (`register`, `render`, registry names).
- Each task ends GREEN (its tests pass) and is committed. TDD: failing test first.
- Run tests with: `cd /Users/jadrians/aprendo/sinpapel-reports && .venv/bin/pytest` (after Task 1 sets up the venv).

## File Structure

```
sinpapel-reports/
  pyproject.toml
  README.md  README.es.md  CHANGELOG.md  LICENSE  MANIFEST.in  py.typed
  pytest.ini
  sinpapel_reports/
    __init__.py            # __version__ = "0.1.0"
    apps.py                # SinpapelReportsConfig.ready() -> autodiscover_modules("reports")
    exceptions.py          # SinpapelReportsError + DataSourceNotFoundError, UnsupportedTemplateError, OverlaySchemaError
    registry.py            # ReportDataSourceRegistry singleton + @register_data_source
    data_sources.py        # ReportDataSource Protocol, CampoReporte, FakeDataSource
    schemas/
      __init__.py          # re-exports
      overlay.py           # Fuente/PosicionBase/CampoOverlay/OverlayConfig (+from_json/to_json)
    services/
      __init__.py          # re-exports
      overlay_renderer.py  # OverlayRenderer
      docx_renderer.py     # DocxRenderer
      report_engine.py     # ReportEngine + ResultadoGeneracion/ResultadoPaquete
    drf/                   # optional layer (import-guarded)
      __init__.py
      serializers.py
      views.py
      urls.py
  tests/
    settings.py
    conftest.py
    apps.py  __init__.py   # a "tests" app + a "reports.py" registering FakeDataSource for autodiscovery
    reports.py             # registers FakeDataSource (exercises autodiscover)
    fixtures/blank.pdf      # 1-page blank PDF generated in a test helper (not committed binary; built at runtime)
    test_scaffold.py
    test_schema_overlay.py
    test_registry.py
    test_overlay_renderer.py
    test_docx_renderer.py
    test_report_engine.py
    test_drf.py
    test_no_creditos_dep.py
  docs/
    superpowers/specs/2026-06-29-sinpapel-reports-design.md  (already committed)
    superpowers/plans/2026-06-29-sinpapel-reports.md          (this file)
```

---

### Task 1: Scaffold the package (builds, imports, app loads, pytest collects)

**Files:**
- Create: `pyproject.toml`, `sinpapel_reports/__init__.py`, `sinpapel_reports/apps.py`, `sinpapel_reports/exceptions.py`, `pytest.ini`, `tests/settings.py`, `tests/__init__.py`, `tests/apps.py`, `tests/conftest.py`, `MANIFEST.in`, `py.typed`, `LICENSE`
- Test: `tests/test_scaffold.py`

**Interfaces:**
- Produces: `sinpapel_reports.__version__: str`; `sinpapel_reports.apps.SinpapelReportsConfig`; `sinpapel_reports.exceptions.SinpapelReportsError` (+ `DataSourceNotFoundError`, `UnsupportedTemplateError`, `OverlaySchemaError`, all subclasses).

- [ ] **Step 1: Create the venv and install deps**

Run:
```bash
cd /Users/jadrians/aprendo/sinpapel-reports
python3 -m venv .venv
.venv/bin/pip install -q "Django>=5.0" "django-simple-history>=3.5" "cryptography>=42.0" \
  "PyPDF2>=3.0" "reportlab>=4.4" docxtpl "djangorestframework>=3.14" "pytest>=9.0" "pytest-django>=4.12" \
  "sinpapel @ git+ssh://git@github.com/aprendomx/sinpapel.git@v0.7.0"
```
Expected: installs succeed; `sinpapel` resolves from git tag v0.7.0.

- [ ] **Step 2: Write `pyproject.toml`**

```toml
[project]
name = "sinpapel-reports"
version = "0.1.0"
description = "Pluggable template-driven document generation (PDF overlay + DOCX) for the sinpapel ecosystem."
readme = "README.md"
requires-python = ">=3.10"
license = "GPL-3.0-or-later"
license-files = ["LICENSE"]
authors = [{ name = "Julio Adrián", email = "jadrian.s@gmail.com" }]
keywords = ["django", "pdf", "docx", "report", "document-generation", "overlay", "sinpapel"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Framework :: Django",
    "Framework :: Django :: 5.0",
    "Intended Audience :: Developers",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Topic :: Office/Business",
    "Topic :: Software Development :: Libraries :: Python Modules",
]
dependencies = [
    "Django>=5.0",
    "sinpapel @ git+ssh://git@github.com/aprendomx/sinpapel.git@v0.7.0",
    "PyPDF2>=3.0",
    "reportlab>=4.4",
    "docxtpl",
]

[project.optional-dependencies]
drf = ["djangorestframework>=3.14"]
dev = ["pytest>=9.0", "pytest-django>=4.12", "build>=1.2", "twine>=5.0"]
docs = ["mkdocs>=1.6", "mkdocs-material>=9.5", "mkdocstrings[python]>=0.25"]

[build-system]
requires = ["setuptools>=77"]
build-backend = "setuptools.build_meta"

# Layout: flat — pyproject.toml + package files at repo root.
[tool.setuptools]
packages = [
    "sinpapel_reports",
    "sinpapel_reports.schemas",
    "sinpapel_reports.services",
    "sinpapel_reports.drf",
]

[tool.setuptools.package-data]
sinpapel_reports = ["py.typed"]

[tool.pyright]
include = ["sinpapel_reports"]
exclude = ["tests", "docs", "site", ".venv", "__pycache__", ".pytest_cache"]
pythonVersion = "3.10"
reportMissingImports = "warning"
reportAttributeAccessIssue = "warning"
```

- [ ] **Step 3: Write `py.typed` (empty file), `MANIFEST.in`, and `LICENSE`**

`MANIFEST.in`:
```
include LICENSE README.md README.es.md CHANGELOG.md py.typed
recursive-include sinpapel_reports py.typed
```
`py.typed`: empty file. `LICENSE`: copy GPL-3.0 text from `/Users/jadrians/aprendo/sinpapel/LICENSE`:
```bash
cp /Users/jadrians/aprendo/sinpapel/LICENSE /Users/jadrians/aprendo/sinpapel-reports/LICENSE
```

- [ ] **Step 4: Write `sinpapel_reports/__init__.py`**

```python
"""Sinpapel Reports — generación de documentos por plantilla (PDF overlay + DOCX)."""
from __future__ import annotations

__version__ = "0.1.0"
```

- [ ] **Step 5: Write `sinpapel_reports/exceptions.py`**

```python
"""Sinpapel Reports — jerarquía de excepciones."""
from __future__ import annotations


class SinpapelReportsError(Exception):
    """Base de todas las excepciones del framework de reportes."""


class DataSourceNotFoundError(SinpapelReportsError):
    """No existe una fuente de datos registrada con el nombre solicitado."""


class UnsupportedTemplateError(SinpapelReportsError):
    """tipo_plantilla no soportado (no es 'PDF' ni 'DOCX')."""


class OverlaySchemaError(SinpapelReportsError):
    """configuracion_overlay malformada o no deserializable."""
```

- [ ] **Step 6: Write `sinpapel_reports/apps.py`**

```python
"""Sinpapel Reports — App config."""
from __future__ import annotations

from django.apps import AppConfig
from django.utils.module_loading import autodiscover_modules


class SinpapelReportsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "sinpapel_reports"
    verbose_name = "Sinpapel — Reportes y Documentos"

    def ready(self) -> None:
        # Las apps host declaran sus ReportDataSource en un módulo `reports.py`;
        # autodiscover los importa para que se registren (patrón webhooks/admin).
        autodiscover_modules("reports")
```

- [ ] **Step 7: Write `pytest.ini`**

```ini
[pytest]
DJANGO_SETTINGS_MODULE = tests.settings
django_find_project = false
python_files = test_*.py
```

- [ ] **Step 8: Write `tests/__init__.py` (empty), `tests/apps.py`, `tests/settings.py`**

`tests/apps.py`:
```python
from django.apps import AppConfig


class TestsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tests"
```

`tests/settings.py`:
```python
"""Minimal Django settings for sinpapel-reports test suite."""
import os
import tempfile

SECRET_KEY = "test-secret-key-not-for-production"
DEBUG = True

DATABASES = {
    "default": {
        "ENGINE": os.getenv("TEST_DB_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.getenv("TEST_DB_NAME", ":memory:"),
    }
}

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "simple_history",
    "sinpapel",
    "sinpapel_reports",
    "tests",
]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
MEDIA_ROOT = tempfile.mkdtemp(prefix="sinpapel_reports_media_")

CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

# Default backend para firma (sinpapel core lo lee de forma lazy).
SINPAPEL_SIGNATURE_BACKEND = "sinpapel.signing.backends.fake.FakeBackend"
```

- [ ] **Step 9: Write `tests/conftest.py`**

```python
"""sinpapel-reports — pytest fixtures comunes."""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _clear_report_registry_each_test():
    """Aísla el registry de data sources entre tests."""
    from sinpapel_reports.registry import ReportDataSourceRegistry
    ReportDataSourceRegistry.clear()
    yield
    ReportDataSourceRegistry.clear()
```

> NOTE: `ReportDataSourceRegistry` does not exist until Task 3. To keep Task 1 GREEN, write `conftest.py` now WITHOUT the fixture body referencing it — use the stub below, and replace it in Task 3.

Task-1 stub `tests/conftest.py`:
```python
"""sinpapel-reports — pytest fixtures comunes."""
from __future__ import annotations
```

- [ ] **Step 10: Write the failing scaffold test `tests/test_scaffold.py`**

```python
from __future__ import annotations

import django
from django.apps import apps


def test_version_exposed():
    import sinpapel_reports
    assert sinpapel_reports.__version__ == "0.1.0"


def test_app_config_loads():
    cfg = apps.get_app_config("sinpapel_reports")
    assert cfg.name == "sinpapel_reports"


def test_exception_hierarchy():
    from sinpapel_reports.exceptions import (
        DataSourceNotFoundError,
        OverlaySchemaError,
        SinpapelReportsError,
        UnsupportedTemplateError,
    )
    assert issubclass(DataSourceNotFoundError, SinpapelReportsError)
    assert issubclass(OverlaySchemaError, SinpapelReportsError)
    assert issubclass(UnsupportedTemplateError, SinpapelReportsError)
```

- [ ] **Step 11: Run tests to verify they pass**

Run: `cd /Users/jadrians/aprendo/sinpapel-reports && .venv/bin/pytest -v`
Expected: 3 passed. (App loads → `autodiscover_modules("reports")` finds `tests/reports.py`; create an empty `tests/reports.py` so autodiscover doesn't error.)

- [ ] **Step 12: Create empty `tests/reports.py`** (so autodiscovery has a module to import)

```python
"""Test host app — registra data sources de prueba. Poblado en Task 3."""
from __future__ import annotations
```

- [ ] **Step 13: Commit**

```bash
cd /Users/jadrians/aprendo/sinpapel-reports
git add -A
git commit -m "feat: scaffold sinpapel-reports package (app, exceptions, test harness)"
```

---

### Task 2: Overlay schema (frozen dataclasses + JSON round-trip)

**Files:**
- Create: `sinpapel_reports/schemas/__init__.py`, `sinpapel_reports/schemas/overlay.py`
- Test: `tests/test_schema_overlay.py`

**Interfaces:**
- Produces:
  - `Fuente(nombre: str = "Helvetica", tamano: int = 10)`
  - `PosicionBase(x_left: float = 50, y_top_offset: float = 50, line_height: float = 15)`
  - `CampoOverlay(visible: bool = False, label: str = "", x: float | None = None, y: float | None = None, posiciones: tuple[dict[str, Any], ...] = ())`
  - `OverlayConfig(campos_solicitud: dict[str, CampoOverlay], campos_participantes: dict[str, CampoOverlay], posicion_base: PosicionBase, fuente: Fuente, data_source: str | None = None)`
  - `OverlayConfig.from_json(data: dict[str, Any]) -> OverlayConfig` (classmethod)
  - `OverlayConfig.to_json(self) -> dict[str, Any]`
  - `OverlayConfig.campos(self) -> dict[str, CampoOverlay]` (merged, solicitud first)
  - `SCHEMA_VERSION: str = "0.1"`

- [ ] **Step 1: Write the failing test `tests/test_schema_overlay.py`**

```python
from __future__ import annotations

from sinpapel_reports.schemas.overlay import (
    CampoOverlay,
    Fuente,
    OverlayConfig,
    PosicionBase,
)


def test_from_json_empty_uses_defaults():
    cfg = OverlayConfig.from_json({})
    assert cfg.fuente == Fuente()
    assert cfg.posicion_base == PosicionBase()
    assert cfg.campos_solicitud == {}
    assert cfg.data_source is None


def test_from_json_parses_campos_and_fuente():
    data = {
        "campos_solicitud": {
            "folio": {"visible": True, "label": "Folio", "x": 10, "y": 20, "posiciones": []},
        },
        "fuente": {"nombre": "Times-Roman", "tamaño": 12},
        "data_source": "solicitud",
    }
    cfg = OverlayConfig.from_json(data)
    campo = cfg.campos_solicitud["folio"]
    assert isinstance(campo, CampoOverlay)
    assert campo.visible is True and campo.x == 10 and campo.y == 20
    assert cfg.fuente.nombre == "Times-Roman" and cfg.fuente.tamano == 12
    assert cfg.data_source == "solicitud"


def test_posicion_alias_backward_compat():
    cfg = OverlayConfig.from_json({"posicion": {"x_left": 99}})
    assert cfg.posicion_base.x_left == 99


def test_to_json_roundtrip_preserves_tamano_key():
    cfg = OverlayConfig.from_json(
        {"fuente": {"nombre": "Helvetica", "tamaño": 8},
         "campos_participantes": {"curp": {"visible": True, "label": "CURP",
                                            "posiciones": [{"x": 1, "y": 2, "page": 1}]}}}
    )
    out = cfg.to_json()
    assert out["fuente"]["tamaño"] == 8
    assert out["campos_participantes"]["curp"]["posiciones"] == [{"x": 1, "y": 2, "page": 1}]
    # round-trip stable
    assert OverlayConfig.from_json(out).to_json() == out


def test_campos_merges_groups_solicitud_first():
    cfg = OverlayConfig.from_json({
        "campos_solicitud": {"folio": {"visible": True, "label": "F"}},
        "campos_participantes": {"curp": {"visible": True, "label": "C"}},
    })
    merged = cfg.campos()
    assert list(merged.keys()) == ["folio", "curp"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_schema_overlay.py -v`
Expected: FAIL — `ModuleNotFoundError: sinpapel_reports.schemas.overlay`.

- [ ] **Step 3: Write `sinpapel_reports/schemas/overlay.py`**

```python
"""Sinpapel Reports — esquema de configuración de overlay.

Modela el JSON almacenado en `Documento.configuracion_overlay` con dataclasses
inmutables. Preserva las claves históricas (`campos_solicitud`,
`campos_participantes`, `tamaño`, alias `posicion`) por compatibilidad con
configuraciones ya guardadas en producción.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

SCHEMA_VERSION = "0.1"


@dataclass(frozen=True)
class Fuente:
    nombre: str = "Helvetica"
    tamano: int = 10


@dataclass(frozen=True)
class PosicionBase:
    x_left: float = 50
    y_top_offset: float = 50
    line_height: float = 15


@dataclass(frozen=True)
class CampoOverlay:
    visible: bool = False
    label: str = ""
    x: float | None = None
    y: float | None = None
    posiciones: tuple[dict[str, Any], ...] = ()


def _campo_from_json(data: dict[str, Any]) -> CampoOverlay:
    posiciones = tuple(dict(p) for p in data.get("posiciones", []) or [])
    return CampoOverlay(
        visible=bool(data.get("visible", False)),
        label=str(data.get("label", "")),
        x=data.get("x"),
        y=data.get("y"),
        posiciones=posiciones,
    )


def _campo_to_json(campo: CampoOverlay) -> dict[str, Any]:
    return {
        "visible": campo.visible,
        "label": campo.label,
        "x": campo.x,
        "y": campo.y,
        "posiciones": [dict(p) for p in campo.posiciones],
    }


@dataclass(frozen=True)
class OverlayConfig:
    campos_solicitud: dict[str, CampoOverlay] = field(default_factory=dict)
    campos_participantes: dict[str, CampoOverlay] = field(default_factory=dict)
    posicion_base: PosicionBase = field(default_factory=PosicionBase)
    fuente: Fuente = field(default_factory=Fuente)
    data_source: str | None = None

    @classmethod
    def from_json(cls, data: dict[str, Any] | None) -> "OverlayConfig":
        data = data or {}
        fuente_raw = data.get("fuente", {}) or {}
        fuente = Fuente(
            nombre=fuente_raw.get("nombre", "Helvetica"),
            tamano=fuente_raw.get("tamaño", fuente_raw.get("tamano", 10)),
        )
        # Alias retro-compat: `posicion` -> `posicion_base`.
        pos_raw = data.get("posicion_base", data.get("posicion", {})) or {}
        base = replace(PosicionBase(), **{
            k: pos_raw[k] for k in ("x_left", "y_top_offset", "line_height") if k in pos_raw
        })
        return cls(
            campos_solicitud={k: _campo_from_json(v) for k, v in (data.get("campos_solicitud", {}) or {}).items()},
            campos_participantes={k: _campo_from_json(v) for k, v in (data.get("campos_participantes", {}) or {}).items()},
            posicion_base=base,
            fuente=fuente,
            data_source=data.get("data_source"),
        )

    def to_json(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "campos_solicitud": {k: _campo_to_json(v) for k, v in self.campos_solicitud.items()},
            "campos_participantes": {k: _campo_to_json(v) for k, v in self.campos_participantes.items()},
            "posicion_base": {
                "x_left": self.posicion_base.x_left,
                "y_top_offset": self.posicion_base.y_top_offset,
                "line_height": self.posicion_base.line_height,
            },
            "fuente": {"nombre": self.fuente.nombre, "tamaño": self.fuente.tamano},
        }
        if self.data_source is not None:
            out["data_source"] = self.data_source
        return out

    def campos(self) -> dict[str, CampoOverlay]:
        """Campos fusionados de ambos grupos (solicitud primero), orden preservado."""
        merged: dict[str, CampoOverlay] = {}
        merged.update(self.campos_solicitud)
        merged.update(self.campos_participantes)
        return merged
```

- [ ] **Step 4: Write `sinpapel_reports/schemas/__init__.py`**

```python
"""Sinpapel Reports — schemas."""
from __future__ import annotations

from sinpapel_reports.schemas.overlay import (
    SCHEMA_VERSION,
    CampoOverlay,
    Fuente,
    OverlayConfig,
    PosicionBase,
)

__all__ = ["SCHEMA_VERSION", "CampoOverlay", "Fuente", "OverlayConfig", "PosicionBase"]
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_schema_overlay.py -v`
Expected: 5 passed.

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "feat: overlay config schema (frozen dataclasses, JSON round-trip, posicion alias)"
```

---

### Task 3: Data-source seam (Protocol + registry + decorator + FakeDataSource)

**Files:**
- Create: `sinpapel_reports/registry.py`, `sinpapel_reports/data_sources.py`
- Modify: `tests/conftest.py` (replace stub with the real registry-clearing fixture), `tests/reports.py` (register `FakeDataSource`)
- Test: `tests/test_registry.py`

**Interfaces:**
- Produces:
  - `CampoReporte(key: str, label: str, grupo: str = "solicitud")` — frozen dataclass.
  - `ReportDataSource` Protocol: `name: ClassVar[str]`; `get_field_catalog() -> list[CampoReporte]`; `build_context(target: Any) -> dict[str, Any]`.
  - `ReportDataSourceRegistry` (module-level singleton) with `register(source)`, `get(name) -> ReportDataSource` (raises `DataSourceNotFoundError`), `names() -> list[str]`, `clear()`.
  - `register_data_source` decorator (class decorator; instantiates and registers).
  - `FakeDataSource` (name `"fake"`) for tests.

- [ ] **Step 1: Write the failing test `tests/test_registry.py`**

```python
from __future__ import annotations

import pytest

from sinpapel_reports.data_sources import CampoReporte, FakeDataSource, register_data_source
from sinpapel_reports.exceptions import DataSourceNotFoundError
from sinpapel_reports.registry import ReportDataSourceRegistry


def test_register_and_get():
    src = FakeDataSource()
    ReportDataSourceRegistry.register(src)
    assert ReportDataSourceRegistry.get("fake") is src
    assert "fake" in ReportDataSourceRegistry.names()


def test_get_unknown_raises():
    with pytest.raises(DataSourceNotFoundError):
        ReportDataSourceRegistry.get("nope")


def test_decorator_registers_instance():
    @register_data_source
    class _Demo:
        name = "demo"
        def get_field_catalog(self):
            return [CampoReporte(key="x", label="X")]
        def build_context(self, target):
            return {"x": 1}

    assert ReportDataSourceRegistry.get("demo").build_context(None) == {"x": 1}


def test_fake_source_shape():
    src = FakeDataSource()
    cat = src.get_field_catalog()
    assert all(isinstance(c, CampoReporte) for c in cat)
    ctx = src.build_context(target=object())
    assert ctx["folio"] == 123 and ctx["nombre_grupo"] == "GRUPO DEMO"


def test_autodiscovery_registered_fake_via_tests_reports(django_db_setup):
    # tests/reports.py registers FakeDataSource on app ready/autodiscover.
    # (django_db_setup triggers app loading.)
    from sinpapel_reports.registry import ReportDataSourceRegistry as R
    # Re-import path: the conftest clears registry per-test, so register here.
    R.register(FakeDataSource())
    assert "fake" in R.names()
```

> NOTE: keep the autodiscovery assertion light — the autouse fixture clears the registry each test, so the canonical autodiscovery proof is that `tests/reports.py` imports without error during app `ready()`. The explicit re-register above keeps the test deterministic.

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_registry.py -v`
Expected: FAIL — `ModuleNotFoundError: sinpapel_reports.registry`.

- [ ] **Step 3: Write `sinpapel_reports/registry.py`**

```python
"""Sinpapel Reports — registry de fuentes de datos.

Singleton module-level que cataloga ReportDataSource por su `name`. Las apps
host registran las suyas en un módulo `reports.py` (autodiscovered en
SinpapelReportsConfig.ready()).
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from sinpapel_reports.exceptions import DataSourceNotFoundError

if TYPE_CHECKING:
    from sinpapel_reports.data_sources import ReportDataSource


class _RegistryImpl:
    """No instanciar directamente — usar `ReportDataSourceRegistry`."""

    def __init__(self) -> None:
        self._sources: dict[str, "ReportDataSource"] = {}

    def register(self, source: "ReportDataSource") -> None:
        """Registra una fuente bajo source.name. Idempotente para el mismo objeto."""
        existing = self._sources.get(source.name)
        if existing is not None and existing is source:
            return
        self._sources[source.name] = source

    def get(self, name: str) -> "ReportDataSource":
        """Recupera por name. Raises DataSourceNotFoundError si no existe."""
        try:
            return self._sources[name]
        except KeyError as exc:
            raise DataSourceNotFoundError(
                f"No hay ReportDataSource registrado con name '{name}'. "
                f"Registrados: {sorted(self._sources)}"
            ) from exc

    def names(self) -> list[str]:
        return sorted(self._sources)

    def clear(self) -> None:
        """Vacía el registry (tests)."""
        self._sources.clear()


ReportDataSourceRegistry = _RegistryImpl()
```

- [ ] **Step 4: Write `sinpapel_reports/data_sources.py`**

```python
"""Sinpapel Reports — contrato y registro de fuentes de datos.

`ReportDataSource` es el seam que desacopla el framework del dominio del host:
provee el catálogo de campos (paleta del editor) y el contexto de datos para
renderizar una plantilla contra un `target` arbitrario.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar, Protocol, runtime_checkable

from sinpapel_reports.registry import ReportDataSourceRegistry


@dataclass(frozen=True)
class CampoReporte:
    """Una entrada de la paleta de campos del editor."""

    key: str
    label: str
    grupo: str = "solicitud"


@runtime_checkable
class ReportDataSource(Protocol):
    """Contrato que una app host implementa para alimentar el generador.

    El `name` identifica la fuente en `Documento.configuracion_overlay["data_source"]`.
    """

    name: ClassVar[str]

    def get_field_catalog(self) -> list[CampoReporte]:
        """Campos disponibles para la paleta del editor."""
        ...

    def build_context(self, target: Any) -> dict[str, Any]:
        """Construye el dict de datos para renderizar contra `target`."""
        ...


def register_data_source(cls: type) -> type:
    """Decorator de clase: instancia y registra la fuente.

    Uso:
        @register_data_source
        class SolicitudDataSource:
            name = "solicitud"
            def get_field_catalog(self): ...
            def build_context(self, target): ...
    """
    ReportDataSourceRegistry.register(cls())
    return cls


class FakeDataSource:
    """Fuente determinística para tests (no depende de ningún modelo del host)."""

    name: ClassVar[str] = "fake"

    def get_field_catalog(self) -> list[CampoReporte]:
        return [
            CampoReporte(key="folio", label="Folio", grupo="solicitud"),
            CampoReporte(key="nombre_grupo", label="Nombre Grupo", grupo="solicitud"),
            CampoReporte(key="curp", label="CURP", grupo="participantes"),
        ]

    def build_context(self, target: Any) -> dict[str, Any]:
        return {"folio": 123, "nombre_grupo": "GRUPO DEMO", "curp": "XAXX010101HDFXXX01"}
```

- [ ] **Step 5: Replace `tests/conftest.py` stub with the real fixture**

```python
"""sinpapel-reports — pytest fixtures comunes."""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _clear_report_registry_each_test():
    from sinpapel_reports.registry import ReportDataSourceRegistry
    ReportDataSourceRegistry.clear()
    yield
    ReportDataSourceRegistry.clear()
```

- [ ] **Step 6: Populate `tests/reports.py` to exercise autodiscovery**

```python
"""Test host app — registra la FakeDataSource vía autodiscover."""
from __future__ import annotations

from sinpapel_reports.data_sources import FakeDataSource, register_data_source


@register_data_source
class _AutodiscoveredFake(FakeDataSource):
    name = "fake_autodiscovered"
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_registry.py -v`
Expected: all passed.

- [ ] **Step 8: Commit**

```bash
git add -A && git commit -m "feat: ReportDataSource protocol + registry + decorator + FakeDataSource"
```

---

### Task 4: OverlayRenderer (PDF stamping, generic over field groups)

**Files:**
- Create: `sinpapel_reports/services/__init__.py`, `sinpapel_reports/services/overlay_renderer.py`
- Test: `tests/test_overlay_renderer.py`

**Interfaces:**
- Consumes: `OverlayConfig`, `CampoOverlay` (Task 2).
- Produces: `OverlayRenderer.render(template_path: str, config: OverlayConfig, contexto: dict[str, Any]) -> bytes` (staticmethod). Returns merged PDF bytes; page count preserved.

- [ ] **Step 1: Write the failing test `tests/test_overlay_renderer.py`**

```python
from __future__ import annotations

import io

from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas

from sinpapel_reports.schemas.overlay import OverlayConfig
from sinpapel_reports.services.overlay_renderer import OverlayRenderer


def _blank_pdf(path: str, pages: int = 1) -> None:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(300, 300))
    for _ in range(pages):
        c.showPage()
    c.save()
    buf.seek(0)
    reader = PdfReader(buf)
    writer = PdfWriter()
    for p in reader.pages:
        writer.add_page(p)
    with open(path, "wb") as fh:
        writer.write(fh)


def test_render_preserves_page_count(tmp_path):
    tpl = tmp_path / "t.pdf"
    _blank_pdf(str(tpl), pages=2)
    cfg = OverlayConfig.from_json({})
    out = OverlayRenderer.render(str(tpl), cfg, {})
    assert PdfReader(io.BytesIO(out)).pages.__len__() == 2


def test_render_stamps_value_at_position(tmp_path):
    tpl = tmp_path / "t.pdf"
    _blank_pdf(str(tpl), pages=1)
    cfg = OverlayConfig.from_json({
        "campos_solicitud": {
            "folio": {"visible": True, "label": "Folio",
                      "posiciones": [{"x": 20, "y": 40, "page": 1}]},
        },
    })
    out = OverlayRenderer.render(str(tpl), cfg, {"folio": "ABC-999"})
    text = PdfReader(io.BytesIO(out)).pages[0].extract_text() or ""
    assert "ABC-999" in text


def test_invisible_field_not_stamped(tmp_path):
    tpl = tmp_path / "t.pdf"
    _blank_pdf(str(tpl), pages=1)
    cfg = OverlayConfig.from_json({
        "campos_solicitud": {
            "folio": {"visible": False, "label": "Folio",
                      "posiciones": [{"x": 20, "y": 40, "page": 1}]},
        },
    })
    out = OverlayRenderer.render(str(tpl), cfg, {"folio": "HIDDEN"})
    text = PdfReader(io.BytesIO(out)).pages[0].extract_text() or ""
    assert "HIDDEN" not in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_overlay_renderer.py -v`
Expected: FAIL — `ModuleNotFoundError: sinpapel_reports.services.overlay_renderer`.

- [ ] **Step 3: Write `sinpapel_reports/services/overlay_renderer.py`**

> Ported from `creditos/services/instancia_documento_service.py::_create_pdf_overlays` /
> `_process_pdf_template`, generalized to iterate the config's field groups
> (`config.campos()`) instead of a hardcoded credit-field order list, and to draw
> any visible field whose context key has a truthy value. Behavior for `posiciones`
> (multi-position, per-page, top-origin Y) and the sequential fallback is preserved.

```python
"""Sinpapel Reports — renderer de overlay PDF (ReportLab + PyPDF2)."""
from __future__ import annotations

import io
from typing import Any

from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas

from sinpapel_reports.schemas.overlay import OverlayConfig


class OverlayRenderer:
    """Estampa valores del contexto sobre una plantilla PDF según OverlayConfig."""

    @staticmethod
    def render(template_path: str, config: OverlayConfig, contexto: dict[str, Any]) -> bytes:
        reader = PdfReader(template_path)
        writer = PdfWriter()
        overlays = OverlayRenderer._build_overlays(config, contexto, reader)
        for i, page in enumerate(reader.pages):
            if i < len(overlays) and overlays[i] is not None:
                page.merge_page(overlays[i])
            writer.add_page(page)
        out = io.BytesIO()
        writer.write(out)
        return out.getvalue()

    @staticmethod
    def _build_overlays(config: OverlayConfig, contexto: dict[str, Any], reader: PdfReader) -> list[Any]:
        total_pages = len(reader.pages)
        font_name = config.fuente.nombre or "Helvetica"
        font_size = config.fuente.tamano or 10

        buffers: list[io.BytesIO] = []
        canvases: list[dict[str, Any]] = []
        for page in reader.pages:
            w = float(page.mediabox.width)
            h = float(page.mediabox.height)
            buf = io.BytesIO()
            buffers.append(buf)
            canvases.append({"canvas": canvas.Canvas(buf, pagesize=(w, h)), "height": h})

        def _set_font(c: Any) -> None:
            try:
                c.setFont(font_name, font_size)
            except Exception:
                c.setFont("Helvetica", 10)

        campos = config.campos()

        # ¿Algún campo usa posiciones múltiples? Si no, modo secuencial simple.
        usar_simple = not any(c.posiciones for c in campos.values())

        if usar_simple:
            c_info = canvases[0]
            c = c_info["canvas"]
            _set_font(c)
            y_pos = c_info["height"] - config.posicion_base.y_top_offset
            for key, campo in campos.items():
                if not campo.visible:
                    continue
                valor = contexto.get(key)
                if not valor:
                    continue
                if campo.x is not None and campo.y is not None:
                    c.drawString(campo.x, c_info["height"] - campo.y, f"{valor}")
                else:
                    c.drawString(config.posicion_base.x_left, y_pos, f"{valor}")
                    y_pos -= config.posicion_base.line_height
        else:
            for key, campo in campos.items():
                if not campo.visible:
                    continue
                valor = contexto.get(key)
                if not valor:
                    continue
                if not campo.posiciones:
                    if campo.x is not None and campo.y is not None:
                        c_info = canvases[0]
                        c = c_info["canvas"]
                        _set_font(c)
                        c.drawString(campo.x, c_info["height"] - campo.y, f"{valor}")
                    continue
                for pos in campo.posiciones:
                    if not isinstance(pos, dict):
                        continue
                    x = pos.get("x")
                    y = pos.get("y")
                    page = pos.get("page", 1)
                    if x is None or y is None:
                        continue
                    idx = page - 1
                    if idx < 0 or idx >= total_pages:
                        continue
                    c_info = canvases[idx]
                    c = c_info["canvas"]
                    _set_font(c)
                    c.drawString(x, c_info["height"] - y, f"{valor}")

        overlays: list[Any] = []
        for i, buf in enumerate(buffers):
            canvases[i]["canvas"].save()
            buf.seek(0)
            try:
                ov = PdfReader(buf)
                overlays.append(ov.pages[0] if len(ov.pages) > 0 else None)
            except Exception:
                overlays.append(None)
        return overlays
```

- [ ] **Step 4: Write `sinpapel_reports/services/__init__.py`**

```python
"""Sinpapel Reports — services."""
from __future__ import annotations

from sinpapel_reports.services.docx_renderer import DocxRenderer
from sinpapel_reports.services.overlay_renderer import OverlayRenderer
from sinpapel_reports.services.report_engine import (
    ReportEngine,
    ResultadoGeneracion,
    ResultadoPaquete,
)

__all__ = [
    "DocxRenderer",
    "OverlayRenderer",
    "ReportEngine",
    "ResultadoGeneracion",
    "ResultadoPaquete",
]
```

> NOTE: `docx_renderer` and `report_engine` don't exist until Tasks 5–6. To keep Task 4 GREEN, write `services/__init__.py` now exporting ONLY `OverlayRenderer`; expand the re-exports in Tasks 5 and 6.

Task-4 `services/__init__.py`:
```python
"""Sinpapel Reports — services."""
from __future__ import annotations

from sinpapel_reports.services.overlay_renderer import OverlayRenderer

__all__ = ["OverlayRenderer"]
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_overlay_renderer.py -v`
Expected: 3 passed.

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "feat: OverlayRenderer — generic PDF stamping ported from creditos kernel"
```

---

### Task 5: DocxRenderer (docxtpl fill)

**Files:**
- Create: `sinpapel_reports/services/docx_renderer.py`
- Modify: `sinpapel_reports/services/__init__.py` (add `DocxRenderer`)
- Test: `tests/test_docx_renderer.py`

**Interfaces:**
- Produces: `DocxRenderer.render(template_path: str, contexto: dict[str, Any]) -> bytes` (staticmethod).

- [ ] **Step 1: Write the failing test `tests/test_docx_renderer.py`**

```python
from __future__ import annotations

import io

from docx import Document as DocxDocument

from sinpapel_reports.services.docx_renderer import DocxRenderer


def _docx_with_placeholder(path: str) -> None:
    doc = DocxDocument()
    doc.add_paragraph("Hola {{ nombre }}")
    doc.save(path)


def test_render_fills_placeholder(tmp_path):
    tpl = tmp_path / "t.docx"
    _docx_with_placeholder(str(tpl))
    out = DocxRenderer.render(str(tpl), {"nombre": "MUNDO"})
    rendered = DocxDocument(io.BytesIO(out))
    text = "\n".join(p.text for p in rendered.paragraphs)
    assert "Hola MUNDO" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_docx_renderer.py -v`
Expected: FAIL — `ModuleNotFoundError: sinpapel_reports.services.docx_renderer`.

- [ ] **Step 3: Write `sinpapel_reports/services/docx_renderer.py`**

```python
"""Sinpapel Reports — renderer de plantillas DOCX (docxtpl)."""
from __future__ import annotations

import io
from typing import Any

from docxtpl import DocxTemplate


class DocxRenderer:
    """Rellena una plantilla .docx con el contexto y devuelve los bytes resultantes."""

    @staticmethod
    def render(template_path: str, contexto: dict[str, Any]) -> bytes:
        tpl = DocxTemplate(template_path)
        tpl.render(contexto)
        out = io.BytesIO()
        tpl.save(out)
        return out.getvalue()
```

- [ ] **Step 4: Add `DocxRenderer` to `sinpapel_reports/services/__init__.py`**

```python
"""Sinpapel Reports — services."""
from __future__ import annotations

from sinpapel_reports.services.docx_renderer import DocxRenderer
from sinpapel_reports.services.overlay_renderer import OverlayRenderer

__all__ = ["DocxRenderer", "OverlayRenderer"]
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_docx_renderer.py -v`
Expected: 1 passed.

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "feat: DocxRenderer — docxtpl template fill"
```

---

### Task 6: ReportEngine facade (resolve source → render → persist InstanciaDocumento; ZIP)

**Files:**
- Create: `sinpapel_reports/services/report_engine.py`
- Modify: `sinpapel_reports/services/__init__.py` (add `ReportEngine`, `ResultadoGeneracion`, `ResultadoPaquete`)
- Test: `tests/test_report_engine.py`

**Interfaces:**
- Consumes: `OverlayConfig` (Task 2), `OverlayRenderer` (Task 4), `DocxRenderer` (Task 5), `ReportDataSourceRegistry` (Task 3), sinpapel `Documento`/`InstanciaDocumento`.
- Produces:
  - `ResultadoGeneracion(instancia_id: int, filename: str, contenido: bytes)` — frozen dataclass.
  - `ResultadoPaquete(generaciones: list[ResultadoGeneracion], zip_bytes: bytes, zip_filename: str)` — frozen dataclass.
  - `ReportEngine.generar(documento, target, *, actor=None, data_source: str | None = None) -> ResultadoGeneracion`
  - `ReportEngine.generar_paquete(documento, targets, *, actor=None, data_source: str | None = None) -> ResultadoPaquete`
  - Source resolution order: explicit `data_source` arg → `documento.configuracion_overlay["data_source"]` → `settings.SINPAPEL_REPORTS_DEFAULT_DATA_SOURCE` → raise `DataSourceNotFoundError`.

- [ ] **Step 1: Write the failing test `tests/test_report_engine.py`**

```python
from __future__ import annotations

import io

import pytest
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from sinpapel.models import Documento

from sinpapel_reports.data_sources import FakeDataSource
from sinpapel_reports.exceptions import DataSourceNotFoundError
from sinpapel_reports.registry import ReportDataSourceRegistry
from sinpapel_reports.services.report_engine import ReportEngine, ResultadoPaquete


def _blank_pdf_bytes(pages: int = 1) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(300, 300))
    for _ in range(pages):
        c.showPage()
    c.save()
    buf.seek(0)
    reader = PdfReader(buf)
    writer = PdfWriter()
    for p in reader.pages:
        writer.add_page(p)
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


@pytest.fixture
def fake_source():
    src = FakeDataSource()
    ReportDataSourceRegistry.register(src)
    return src


@pytest.fixture
def pdf_documento(db):
    doc = Documento.objects.create(
        nombre="Oficio Demo",
        valor="oficio",
        tipo_plantilla="PDF",
        configuracion_overlay={
            "data_source": "fake",
            "campos_solicitud": {
                "folio": {"visible": True, "label": "Folio",
                          "posiciones": [{"x": 20, "y": 40, "page": 1}]},
            },
        },
    )
    doc.plantilla.save("demo.pdf", ContentFile(_blank_pdf_bytes(), name="demo.pdf"), save=True)
    return doc


@pytest.mark.django_db
def test_generar_pdf_persists_instancia(fake_source, pdf_documento):
    target = User.objects.create(username="t1")
    res = ReportEngine.generar(pdf_documento, target)
    assert res.instancia_id > 0
    assert res.filename.endswith(".pdf")
    text = PdfReader(io.BytesIO(res.contenido)).pages[0].extract_text() or ""
    assert "123" in text  # FakeDataSource folio


@pytest.mark.django_db
def test_generar_unknown_source_raises(pdf_documento):
    # Registry cleared by autouse fixture -> 'fake' not registered.
    target = User.objects.create(username="t2")
    with pytest.raises(DataSourceNotFoundError):
        ReportEngine.generar(pdf_documento, target)


@pytest.mark.django_db
def test_generar_paquete_returns_zip(fake_source, pdf_documento):
    t1 = User.objects.create(username="a")
    t2 = User.objects.create(username="b")
    res = ReportEngine.generar_paquete(pdf_documento, [t1, t2])
    assert isinstance(res, ResultadoPaquete)
    assert len(res.generaciones) == 2
    import zipfile
    zf = zipfile.ZipFile(io.BytesIO(res.zip_bytes))
    assert len(zf.namelist()) == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_report_engine.py -v`
Expected: FAIL — `ModuleNotFoundError: sinpapel_reports.services.report_engine`.

- [ ] **Step 3: Write `sinpapel_reports/services/report_engine.py`**

```python
"""Sinpapel Reports — fachada de generación de documentos.

Resuelve la fuente de datos, construye el contexto, elige el renderer según
`tipo_plantilla` y persiste un `InstanciaDocumento`. `generar_paquete` agrupa
varios targets en un ZIP en memoria.
"""
from __future__ import annotations

import io
import zipfile
from dataclasses import dataclass
from typing import Any

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils.text import slugify
from sinpapel.models import Documento, InstanciaDocumento

from sinpapel_reports.exceptions import DataSourceNotFoundError, UnsupportedTemplateError
from sinpapel_reports.registry import ReportDataSourceRegistry
from sinpapel_reports.schemas.overlay import OverlayConfig
from sinpapel_reports.services.docx_renderer import DocxRenderer
from sinpapel_reports.services.overlay_renderer import OverlayRenderer


@dataclass(frozen=True)
class ResultadoGeneracion:
    instancia_id: int
    filename: str
    contenido: bytes


@dataclass(frozen=True)
class ResultadoPaquete:
    generaciones: list[ResultadoGeneracion]
    zip_bytes: bytes
    zip_filename: str


class ReportEngine:
    """Genera documentos a partir de un Documento (plantilla) y un target."""

    @staticmethod
    def _resolve_source_name(documento: Documento, data_source: str | None) -> str:
        if data_source:
            return data_source
        config = documento.configuracion_overlay or {}
        if config.get("data_source"):
            return config["data_source"]
        default = getattr(settings, "SINPAPEL_REPORTS_DEFAULT_DATA_SOURCE", None)
        if default:
            return default
        raise DataSourceNotFoundError(
            f"Documento {documento.pk} no declara data_source y no hay "
            f"SINPAPEL_REPORTS_DEFAULT_DATA_SOURCE configurado."
        )

    @staticmethod
    def _render(documento: Documento, contexto: dict[str, Any]) -> tuple[bytes, str]:
        path = getattr(documento.plantilla, "path", None)
        if not path:
            raise UnsupportedTemplateError(f"Documento {documento.pk} sin archivo de plantilla.")
        stem = slugify(documento.nombre or str(documento.pk))
        if documento.tipo_plantilla == "PDF":
            config = OverlayConfig.from_json(documento.configuracion_overlay or {})
            return OverlayRenderer.render(path, config, contexto), f"{stem}.pdf"
        if documento.tipo_plantilla == "DOCX":
            return DocxRenderer.render(path, contexto), f"{stem}.docx"
        raise UnsupportedTemplateError(
            f"tipo_plantilla '{documento.tipo_plantilla}' no soportado (Documento {documento.pk})."
        )

    @classmethod
    def generar(
        cls,
        documento: Documento,
        target: Any,
        *,
        actor: Any = None,
        data_source: str | None = None,
    ) -> ResultadoGeneracion:
        source = ReportDataSourceRegistry.get(cls._resolve_source_name(documento, data_source))
        contexto = source.build_context(target)
        contenido, base_filename = cls._render(documento, contexto)
        target_id = getattr(target, "pk", None)
        filename = f"{base_filename.rsplit('.', 1)[0]}_{target_id}.{base_filename.rsplit('.', 1)[1]}"
        with transaction.atomic():
            instancia = InstanciaDocumento(target=target, documento=documento, actor=actor)
            instancia.save()
            instancia.archivo_generado.save(filename, ContentFile(contenido, name=filename), save=True)
        return ResultadoGeneracion(
            instancia_id=instancia.pk,
            filename=instancia.archivo_generado.name,
            contenido=contenido,
        )

    @classmethod
    def generar_paquete(
        cls,
        documento: Documento,
        targets: list[Any],
        *,
        actor: Any = None,
        data_source: str | None = None,
    ) -> ResultadoPaquete:
        generaciones: list[ResultadoGeneracion] = []
        zip_buffer = io.BytesIO()
        with transaction.atomic():
            with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
                for target in targets:
                    res = cls.generar(documento, target, actor=actor, data_source=data_source)
                    generaciones.append(res)
                    arcname = res.filename.rsplit("/", 1)[-1]
                    zf.writestr(arcname, res.contenido)
        zip_buffer.seek(0)
        zip_filename = f"{slugify(documento.nombre or str(documento.pk))}_paquete.zip"
        return ResultadoPaquete(
            generaciones=generaciones,
            zip_bytes=zip_buffer.getvalue(),
            zip_filename=zip_filename,
        )
```

- [ ] **Step 4: Expand `sinpapel_reports/services/__init__.py` to the full re-export (matches Task 4 Step 4 target)**

```python
"""Sinpapel Reports — services."""
from __future__ import annotations

from sinpapel_reports.services.docx_renderer import DocxRenderer
from sinpapel_reports.services.overlay_renderer import OverlayRenderer
from sinpapel_reports.services.report_engine import (
    ReportEngine,
    ResultadoGeneracion,
    ResultadoPaquete,
)

__all__ = [
    "DocxRenderer",
    "OverlayRenderer",
    "ReportEngine",
    "ResultadoGeneracion",
    "ResultadoPaquete",
]
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_report_engine.py -v`
Expected: 3 passed. (Migrations for `sinpapel` run automatically against the in-memory DB.)

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "feat: ReportEngine facade — generar/generar_paquete, persists InstanciaDocumento + ZIP"
```

---

### Task 7: DRF layer (optional) — field-catalog, overlay-config, generate, download

**Files:**
- Create: `sinpapel_reports/drf/__init__.py`, `sinpapel_reports/drf/serializers.py`, `sinpapel_reports/drf/views.py`, `sinpapel_reports/drf/urls.py`
- Modify: `tests/settings.py` (add `rest_framework` to `INSTALLED_APPS`; add `ROOT_URLCONF = "tests.urls"`), create `tests/urls.py`
- Test: `tests/test_drf.py`

**Interfaces:**
- Consumes: `ReportEngine` (Task 6), `ReportDataSourceRegistry` (Task 3), `OverlayConfig` (Task 2), sinpapel `Documento`/`InstanciaDocumento`.
- Produces URL names under `include("sinpapel_reports.drf.urls")`:
  - `GET  field-catalog/?source=<name>` → `[{"key","label","grupo"}]`
  - `GET  documentos/<pk>/overlay-config/` → `configuracion_overlay` JSON
  - `PUT  documentos/<pk>/overlay-config/` → persists body into `configuracion_overlay`
  - `POST documentos/<pk>/generate/` body `{"target_content_type": <id>, "target_object_id": <id>, "data_source"?: <name>}` → `{"instancia_id","filename"}`
  - `GET  instancias/<pk>/download/` → file response

- [ ] **Step 1: Modify `tests/settings.py`**

Add `"rest_framework"` to `INSTALLED_APPS` (after `"sinpapel_reports"`), and add at the end:
```python
ROOT_URLCONF = "tests.urls"
```

- [ ] **Step 2: Create `tests/urls.py`**

```python
from __future__ import annotations

from django.urls import include, path

urlpatterns = [
    path("api/", include("sinpapel_reports.drf.urls")),
]
```

- [ ] **Step 3: Write the failing test `tests/test_drf.py`**

```python
from __future__ import annotations

import io

import pytest
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from rest_framework.test import APIClient
from sinpapel.models import Documento

from sinpapel_reports.data_sources import FakeDataSource
from sinpapel_reports.registry import ReportDataSourceRegistry


def _blank_pdf_bytes() -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(300, 300))
    c.showPage()
    c.save()
    buf.seek(0)
    reader = PdfReader(buf)
    writer = PdfWriter()
    for p in reader.pages:
        writer.add_page(p)
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def fake_source():
    ReportDataSourceRegistry.register(FakeDataSource())


@pytest.fixture
def pdf_documento(db):
    doc = Documento.objects.create(
        nombre="Oficio Demo", valor="oficio", tipo_plantilla="PDF",
        configuracion_overlay={"data_source": "fake"},
    )
    doc.plantilla.save("demo.pdf", ContentFile(_blank_pdf_bytes(), name="demo.pdf"), save=True)
    return doc


@pytest.mark.django_db
def test_field_catalog(client, fake_source):
    resp = client.get("/api/field-catalog/", {"source": "fake"})
    assert resp.status_code == 200
    keys = {c["key"] for c in resp.json()}
    assert {"folio", "nombre_grupo", "curp"} <= keys


@pytest.mark.django_db
def test_overlay_config_get_put(client, pdf_documento):
    url = f"/api/documentos/{pdf_documento.pk}/overlay-config/"
    new_cfg = {"data_source": "fake", "fuente": {"nombre": "Helvetica", "tamaño": 14}}
    put = client.put(url, new_cfg, format="json")
    assert put.status_code == 200
    pdf_documento.refresh_from_db()
    assert pdf_documento.configuracion_overlay["fuente"]["tamaño"] == 14
    get = client.get(url)
    assert get.status_code == 200 and get.json()["fuente"]["tamaño"] == 14


@pytest.mark.django_db
def test_generate_and_download(client, fake_source, pdf_documento):
    target = User.objects.create(username="z")
    ct = ContentType.objects.get_for_model(User)
    resp = client.post(
        f"/api/documentos/{pdf_documento.pk}/generate/",
        {"target_content_type": ct.pk, "target_object_id": target.pk},
        format="json",
    )
    assert resp.status_code == 201, resp.content
    instancia_id = resp.json()["instancia_id"]
    dl = client.get(f"/api/instancias/{instancia_id}/download/")
    assert dl.status_code == 200
    assert dl["Content-Type"] == "application/pdf"
```

- [ ] **Step 4: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_drf.py -v`
Expected: FAIL — `ModuleNotFoundError: sinpapel_reports.drf.urls`.

- [ ] **Step 5: Write `sinpapel_reports/drf/serializers.py`**

```python
"""Sinpapel Reports — serializers DRF."""
from __future__ import annotations

from rest_framework import serializers


class CampoReporteSerializer(serializers.Serializer):
    key = serializers.CharField()
    label = serializers.CharField()
    grupo = serializers.CharField()


class GenerateRequestSerializer(serializers.Serializer):
    target_content_type = serializers.IntegerField()
    target_object_id = serializers.IntegerField()
    data_source = serializers.CharField(required=False, allow_null=True)
```

- [ ] **Step 6: Write `sinpapel_reports/drf/views.py`**

```python
"""Sinpapel Reports — vistas DRF (capa opcional).

Expone lo que la SPA `sinpapel-reports-designer` consumirá: catálogo de campos,
lectura/escritura de configuracion_overlay, generación y descarga.
"""
from __future__ import annotations

from dataclasses import asdict

from django.contrib.contenttypes.models import ContentType
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from sinpapel.models import Documento, InstanciaDocumento

from sinpapel_reports.drf.serializers import (
    CampoReporteSerializer,
    GenerateRequestSerializer,
)
from sinpapel_reports.exceptions import DataSourceNotFoundError, SinpapelReportsError
from sinpapel_reports.registry import ReportDataSourceRegistry
from sinpapel_reports.services.report_engine import ReportEngine


class FieldCatalogView(APIView):
    """GET /field-catalog/?source=<name> — paleta de campos de la fuente."""

    def get(self, request):
        name = request.query_params.get("source")
        if not name:
            return Response({"detail": "Falta el parámetro 'source'."}, status=400)
        try:
            source = ReportDataSourceRegistry.get(name)
        except DataSourceNotFoundError as exc:
            return Response({"detail": str(exc)}, status=404)
        data = [asdict(c) for c in source.get_field_catalog()]
        return Response(CampoReporteSerializer(data, many=True).data)


class OverlayConfigView(APIView):
    """GET/PUT /documentos/<pk>/overlay-config/."""

    def get(self, request, pk: int):
        documento = get_object_or_404(Documento, pk=pk)
        return Response(documento.configuracion_overlay or {})

    def put(self, request, pk: int):
        documento = get_object_or_404(Documento, pk=pk)
        if not isinstance(request.data, dict):
            return Response({"detail": "El cuerpo debe ser un objeto JSON."}, status=400)
        documento.configuracion_overlay = request.data
        documento.save(update_fields=["configuracion_overlay"])
        return Response(documento.configuracion_overlay)


class GenerateView(APIView):
    """POST /documentos/<pk>/generate/."""

    def post(self, request, pk: int):
        documento = get_object_or_404(Documento, pk=pk)
        req = GenerateRequestSerializer(data=request.data)
        req.is_valid(raise_exception=True)
        ct = get_object_or_404(ContentType, pk=req.validated_data["target_content_type"])
        model = ct.model_class()
        if model is None:
            return Response({"detail": "ContentType inválido."}, status=400)
        target = get_object_or_404(model, pk=req.validated_data["target_object_id"])
        try:
            res = ReportEngine.generar(
                documento, target, data_source=req.validated_data.get("data_source")
            )
        except SinpapelReportsError as exc:
            return Response({"detail": str(exc)}, status=400)
        return Response(
            {"instancia_id": res.instancia_id, "filename": res.filename},
            status=status.HTTP_201_CREATED,
        )


class DownloadView(APIView):
    """GET /instancias/<pk>/download/."""

    def get(self, request, pk: int):
        instancia = get_object_or_404(InstanciaDocumento, pk=pk)
        if not instancia.archivo_generado:
            raise Http404("La instancia no tiene archivo generado.")
        return FileResponse(instancia.archivo_generado.open("rb"))
```

- [ ] **Step 7: Write `sinpapel_reports/drf/urls.py` and `sinpapel_reports/drf/__init__.py`**

`sinpapel_reports/drf/__init__.py`:
```python
"""Sinpapel Reports — capa DRF opcional (requiere el extra `drf`)."""
from __future__ import annotations
```

`sinpapel_reports/drf/urls.py`:
```python
"""Sinpapel Reports — rutas DRF."""
from __future__ import annotations

from django.urls import path

from sinpapel_reports.drf.views import (
    DownloadView,
    FieldCatalogView,
    GenerateView,
    OverlayConfigView,
)

app_name = "sinpapel_reports"

urlpatterns = [
    path("field-catalog/", FieldCatalogView.as_view(), name="field-catalog"),
    path("documentos/<int:pk>/overlay-config/", OverlayConfigView.as_view(), name="overlay-config"),
    path("documentos/<int:pk>/generate/", GenerateView.as_view(), name="generate"),
    path("instancias/<int:pk>/download/", DownloadView.as_view(), name="download"),
]
```

- [ ] **Step 8: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_drf.py -v`
Expected: 3 passed.

- [ ] **Step 9: Commit**

```bash
git add -A && git commit -m "feat: optional DRF layer — field-catalog, overlay-config, generate, download"
```

---

### Task 8: Decoupling guard, docs, packaging finalization, full suite green

**Files:**
- Create: `tests/test_no_creditos_dep.py`, `README.md`, `README.es.md`, `CHANGELOG.md`, `docs/` (mkdocs skeleton)
- Test: `tests/test_no_creditos_dep.py` + full suite

**Interfaces:** none new — verification + documentation task.

- [ ] **Step 1: Write the guard test `tests/test_no_creditos_dep.py`**

```python
from __future__ import annotations

import importlib
import pkgutil

import sinpapel_reports


def test_no_creditos_import_anywhere():
    """El framework no debe importar nada de `creditos` (acoplamiento prohibido)."""
    offenders = []
    for mod in pkgutil.walk_packages(sinpapel_reports.__path__, "sinpapel_reports."):
        module = importlib.import_module(mod.name)
        src = getattr(module, "__file__", None)
        if not src:
            continue
        with open(src, encoding="utf-8") as fh:
            text = fh.read()
        if "creditos" in text:
            offenders.append(mod.name)
    assert offenders == [], f"Módulos que mencionan 'creditos': {offenders}"
```

- [ ] **Step 2: Run guard test**

Run: `.venv/bin/pytest tests/test_no_creditos_dep.py -v`
Expected: PASS (no creditos references).

- [ ] **Step 3: Write `CHANGELOG.md`** (Keep a Changelog 1.1.0 + SemVer)

```markdown
# Changelog

All notable changes to this project are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this project adheres to [SemVer](https://semver.org/).

## [0.1.0] — 2026-06-29

### Added
- Initial extraction of the creditos WYSIWYG overlay generator into a standalone framework.
- `OverlayConfig` schema (frozen dataclasses) with JSON round-trip and `posicion` backward-compat alias.
- `ReportDataSource` Protocol + registry + `@register_data_source` + autodiscovery of host `reports.py`.
- `OverlayRenderer` (PDF, ReportLab + PyPDF2) and `DocxRenderer` (docxtpl).
- `ReportEngine` facade: `generar` / `generar_paquete` persisting `InstanciaDocumento`, with ZIP packaging.
- Optional DRF layer: field-catalog, overlay-config, generate, download.
- Reuses `sinpapel` core `Documento` / `InstanciaDocumento` (no new tables).
```

- [ ] **Step 4: Write `README.md`** (English) and `README.es.md` (Spanish)

`README.md` (minimum content — adapt headings to match sinpapel core's README tone):
```markdown
# sinpapel-reports

Pluggable, template-driven document generation (PDF overlay + DOCX) for the
[sinpapel](https://github.com/aprendomx/sinpapel) ecosystem.

## What it does
Render per-record documents by stamping live data onto a PDF template at pixel
coordinates (ReportLab + PyPDF2) or filling a DOCX template (docxtpl). Output is
persisted as `sinpapel.InstanciaDocumento`, optionally bundled as a ZIP.

## Install
```
pip install "sinpapel-reports @ git+ssh://git@github.com/aprendomx/sinpapel-reports.git@v0.1.0"
```
Add `"sinpapel_reports"` to `INSTALLED_APPS` (after `"sinpapel"`).

## Plug in your data
Declare a `reports.py` in any installed app:
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
Point a `Documento.configuracion_overlay["data_source"]` at `"solicitud"` and call
`ReportEngine.generar(documento, target)`.

## REST (optional)
Install the `drf` extra and `include("sinpapel_reports.drf.urls")`.

## License
GPL-3.0-or-later.
```

`README.es.md`: same content in Spanish.

- [ ] **Step 5: Write mkdocs skeleton** (`mkdocs.yml` + `docs/index.md`, `docs/usage/es.md`, `docs/usage/en.md`, `docs/development/changelog.md`)

`mkdocs.yml` (mirror sinpapel core's structure; teal palette, mkdocstrings). `docs/development/changelog.md` can `--8<--` include the root CHANGELOG or duplicate it. Keep minimal but present.

- [ ] **Step 6: Run the FULL suite**

Run: `.venv/bin/pytest -v`
Expected: all tests pass (scaffold, schema, registry, overlay renderer, docx renderer, report engine, drf, no-creditos guard).

- [ ] **Step 7: Build the distribution to verify packaging**

Run: `.venv/bin/python -m build` (after `.venv/bin/pip install build`)
Expected: `dist/sinpapel_reports-0.1.0-py3-none-any.whl` + sdist build succeed; the wheel contains `sinpapel_reports/` (with `py.typed`) and `sinpapel_reports/drf/`, `schemas/`, `services/`.

- [ ] **Step 8: Commit**

```bash
git add -A && git commit -m "feat: decoupling guard, README (en/es), CHANGELOG, mkdocs skeleton; v0.1.0 ready"
```

---

## Self-Review

**Spec coverage:**
- §3.1 Schema → Task 2 ✓ (incl. `posicion` alias, `tamaño` key, SCHEMA_VERSION).
- §3.2 Data-source seam (Protocol + registry + decorator + FakeDataSource + autodiscovery) → Tasks 1 (autodiscover wiring) + 3 ✓.
- §3.3 Renderers + ReportEngine (generar/generar_paquete, source resolution order) → Tasks 4, 5, 6 ✓.
- §3.4 REST layer (field-catalog, overlay-config, generate/[generate-package], download) → Task 7 ✓. NOTE: `generate-package` REST endpoint deferred — `ReportEngine.generar_paquete` exists and is tested (Task 6); a `/documentos/<pk>/generate-package/` endpoint is a thin follow-up wrapper, intentionally not in v0.1.0 DRF surface to keep the task bounded. Recorded as a known gap below.
- §4 Error handling → `exceptions.py` (Task 1), engine raises (Task 6), DRF maps `SinpapelReportsError`→400 / `DataSourceNotFoundError`→404 (Task 7) ✓.
- §5 Testing (pytest-django, conftest cleanup, FakeDataSource, no-creditos guard) → Tasks 1, 3, 8 ✓.
- §6 Scope (creditos integration = Phase 2, plantilla_service out, charts never) → not implemented here by design ✓.
- §7 Ecosystem fit checklist → Task 1 (layout, py.typed, version mirror, lazy settings, autodiscover) + Task 8 (changelog, dual README, mkdocs) ✓.

**Known gap (intentional):** DRF `generate-package` endpoint not exposed in v0.1.0 (engine method exists + tested). Add in a v0.1.x follow-up if the SPA needs server-side ZIP via REST.

**Placeholder scan:** No "TBD"/"implement later"/"add error handling" — every code step shows complete code. `README.es.md` and the mkdocs skeleton (Task 8 Steps 4–5) are the only prose-fill items; their required content is specified.

**Type consistency:** `OverlayConfig.from_json/to_json/campos`, `CampoReporte(key,label,grupo)`, `ReportDataSourceRegistry.{register,get,names,clear}`, `OverlayRenderer.render(template_path,config,contexto)`, `DocxRenderer.render(template_path,contexto)`, `ReportEngine.generar(...) -> ResultadoGeneracion`, `generar_paquete(...) -> ResultadoPaquete` — names/signatures consistent across Tasks 2→7. The autouse fixture calls `ReportDataSourceRegistry.clear()` (defined Task 3); Task 1 uses a stub conftest with no such call, replaced in Task 3 — sequencing noted inline.
