from __future__ import annotations

import importlib
import pkgutil

import sinpapel_reports


def test_no_creditos_import_anywhere():
    """El framework no debe importar nada de `creditos` (acoplamiento prohibido)."""
    offenders = []
    for mod in pkgutil.walk_packages(sinpapel_reports.__path__, "sinpapel_reports."):
        module = importlib.import_module(mod.name)
        src = getattr(module, "__file__", None)
        if not src:
            continue
        with open(src, encoding="utf-8") as fh:
            text = fh.read()
        if "creditos" in text:
            offenders.append(mod.name)
    assert offenders == [], f"Módulos que mencionan 'creditos': {offenders}"
