from django.apps import AppConfig


class TestsConfig(AppConfig):
    """Configuración de la app de tests."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "tests"
