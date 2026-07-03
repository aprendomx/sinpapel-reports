"""Sinpapel Reports — capa DRF opcional (requiere el extra `drf`).

Seguridad / autenticación
-------------------------
Las vistas de este módulo (``FieldCatalogView``, ``OverlayConfigView``,
``GenerateView``, ``DownloadView``) NO definen ``permission_classes`` propias.
Delegan completamente la autenticación y autorización a la configuración
``DEFAULT_PERMISSION_CLASSES`` del proyecto anfitrión.

El proyecto anfitrión DEBE configurar un ``DEFAULT_PERMISSION_CLASSES`` apropiado
(por ejemplo ``[IsAuthenticated]``) o envolver el ``include(...)`` con sus propios
permisos. Sin esa configuración, las vistas sirven y mutan documentos por pk
secuencial sin ninguna restricción de acceso.
"""
from __future__ import annotations
