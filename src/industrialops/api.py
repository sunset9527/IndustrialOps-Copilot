"""Minimal FastAPI application factory for IndustrialOps v0.1."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from industrialops.app_metadata import PRODUCT_NAME
from industrialops.config import Settings


def create_app(settings: Settings) -> FastAPI:
    """Create the domain-neutral v0.1 application."""

    app = FastAPI(title=PRODUCT_NAME)
    app.state.settings = settings

    @app.exception_handler(StarletteHTTPException)
    def handle_http_exception(_, exception: StarletteHTTPException) -> JSONResponse:
        if exception.status_code == 404:
            return JSONResponse(
                status_code=404,
                content={"error": {"code": "not_found", "message": "Resource not found"}},
            )
        return JSONResponse(
            status_code=exception.status_code,
            content={"error": {"code": "http_error", "message": "Request could not be completed"}},
        )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "product": PRODUCT_NAME}

    @app.get("/ready")
    def ready() -> dict[str, object]:
        return {"status": "ready", "dependencies": []}

    return app
