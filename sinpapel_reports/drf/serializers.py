"""Sinpapel Reports — serializers DRF."""

from __future__ import annotations

from rest_framework import serializers


class CampoReporteSerializer(serializers.Serializer):
    """Serializa un CampoReporte para la paleta del editor."""

    key = serializers.CharField()
    label = serializers.CharField()
    grupo = serializers.CharField()


class GenerateRequestSerializer(serializers.Serializer):
    """Payload de generación de documento vía API."""

    target_content_type = serializers.IntegerField()
    target_object_id = serializers.IntegerField()
    data_source = serializers.CharField(required=False, allow_null=True)
