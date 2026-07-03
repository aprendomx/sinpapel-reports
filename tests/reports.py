"""Test host app — registra la FakeDataSource vía autodiscover."""

from __future__ import annotations

from sinpapel_reports.data_sources import FakeDataSource, register_data_source


@register_data_source
class _AutodiscoveredFake(FakeDataSource):
    name = "fake_autodiscovered"
