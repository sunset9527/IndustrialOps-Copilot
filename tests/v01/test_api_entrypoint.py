from __future__ import annotations

from api.app import app

from industrialops.app_metadata import PRODUCT_NAME


def test_asgi_entrypoint_exposes_the_industrialops_application() -> None:
    assert app.title == PRODUCT_NAME
