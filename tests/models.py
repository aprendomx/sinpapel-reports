"""Modelos auxiliares para tests."""

from __future__ import annotations

from django.contrib.auth.models import User
from django.db import models


class OwnedThing(models.Model):
    """Modelo de ejemplo con campo `owner` para tests de ownership."""

    name = models.CharField(max_length=50)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
