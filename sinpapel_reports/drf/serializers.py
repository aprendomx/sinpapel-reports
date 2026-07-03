"""Sinpapel Reports — serializers DRF."""
from __future__ import annotations

from rest_framework import serializers


class CampoReporteSerializer(serializers.Serializer):
    key = serializers.CharField()
    label = serializers.CharField()
    grupo = serializers.CharField()


class GenerateRequestSerializer(serializers.Serializer):
    target_content_type = serializers.IntegerField()
    target_object_id = serializers.IntegerField()
    data_source = serializers.CharField(required=False, allow_null=True)
