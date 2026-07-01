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
