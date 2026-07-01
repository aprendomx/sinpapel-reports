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
