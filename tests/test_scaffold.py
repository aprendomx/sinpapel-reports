from __future__ import annotations

from django.apps import apps


def test_version_exposed():
    """`__version__` y la versión declarada en pyproject.toml no divergen.

    Se compara contra el metadata de la distribución instalada en vez de contra
    una cadena fija: así el test detecta el error real (bumpear un sitio y
    olvidar el otro) sin tener que editarlo en cada release.
    """
    from importlib.metadata import version

    import sinpapel_reports

    assert sinpapel_reports.__version__ == version("sinpapel-reports")


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
