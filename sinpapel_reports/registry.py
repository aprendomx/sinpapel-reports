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
        self._sources: dict[str, ReportDataSource] = {}

    def register(self, source: ReportDataSource) -> None:
        """Registra una fuente bajo source.name. Idempotente para el mismo objeto."""
        existing = self._sources.get(source.name)
        if existing is not None and existing is source:
            return
        self._sources[source.name] = source

    def get(self, name: str) -> ReportDataSource:
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
