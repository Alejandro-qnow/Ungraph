"""Smoke de empaquetado e imports públicos (CI: installation-test + unit job)."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


def test_ungraph_import_and_configure() -> None:
    import ungraph

    assert hasattr(ungraph, "configure")
    assert callable(ungraph.configure)


def test_get_settings_returns_singleton() -> None:
    from ungraph.core.configuration import get_settings, reset_configuration

    reset_configuration()
    a = get_settings()
    b = get_settings()
    assert a is b
    reset_configuration()


def test_create_bulk_ingest_factory_smoke() -> None:
    from ungraph.application.dependencies import create_bulk_ingest_documents_use_case
    from ungraph.core.configuration import reset_configuration

    reset_configuration()
    uc = create_bulk_ingest_documents_use_case()
    try:
        assert uc is not None
    finally:
        uc.close()
    reset_configuration()
