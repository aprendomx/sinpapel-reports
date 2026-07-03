"""sinpapel-reports — pytest fixtures comunes."""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _clear_report_registry_each_test():
    from sinpapel_reports.registry import ReportDataSourceRegistry
    ReportDataSourceRegistry.clear()
    yield
    ReportDataSourceRegistry.clear()
