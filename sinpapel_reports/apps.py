"""Sinpapel Reports — App config."""

from __future__ import annotations

from django.apps import AppConfig
from django.utils.module_loading import autodiscover_modules


class SinpapelReportsConfig(AppConfig):
    """Configuración de la app sinpapel_reports."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "sinpapel_reports"
    verbose_name = "Sinpapel — Reportes y Documentos"

    def ready(self) -> None:
        """Autodiscover de módulos `reports.py` en las apps instaladas."""
        # Las apps host declaran sus ReportDataSource en un módulo `reports.py`;
        # autodiscover los importa para que se registren (patrón webhooks/admin).
        autodiscover_modules("reports")
