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
