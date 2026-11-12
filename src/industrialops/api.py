"""Minimal FastAPI application factory for IndustrialOps v0.1."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from typing import Annotated, Callable
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from starlette.exceptions import HTTPException as StarletteHTTPException

from industrialops.app_metadata import PRODUCT_NAME
from industrialops.config import Settings
from industrialops.diagnosis.response import diagnosis_json_response
from industrialops.diagnosis.runtime import build_default_workflow
from industrialops.diagnosis.schemas import DiagnosisRequest, DiagnosisResult
from industrialops.middleware.request_size import RequestBodyLimitMiddleware
from industrialops.models.user import User
from industrialops.services.auth import authenticate_user
from industrialops.services.auth_sessions import create_auth_session, resolve_active_session


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=255)


class PublicUser(BaseModel):
    username: str
    role: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    user: PublicUser


SessionFactory = Callable[[], Session]


def create_app(
    settings: Settings,
    *,
    diagnosis_workflow: object | None = None,
    session_factory: SessionFactory | None = None,
) -> FastAPI:
    """Create the domain-neutral v0.1 application."""

    app = FastAPI(title=PRODUCT_NAME)
    app.state.settings = settings
    if session_factory is None:
        engine = create_engine(settings.database_url, pool_pre_ping=True)
        session_factory = sessionmaker(bind=engine)
    app.state.session_factory = session_factory
    # Loading a frozen pack verifies its content hash and can be expensive. Keep
    # application import and non-diagnosis endpoints independent from that work.
    app.state.diagnosis_workflow = diagnosis_workflow
    app.add_middleware(RequestBodyLimitMiddleware, max_bytes=settings.request_max_bytes)

    @app.exception_handler(StarletteHTTPException)
    def handle_http_exception(_, exception: StarletteHTTPException) -> JSONResponse:
        if exception.status_code == 401:
            return _error_response(401, "unauthorized", "Authentication is required")
        if exception.status_code == 404:
            return JSONResponse(
                status_code=404,
                content={"error": {"code": "not_found", "message": "Resource not found"}},
            )
        return JSONResponse(
            status_code=exception.status_code,
            content={"error": {"code": "http_error", "message": "Request could not be completed"}},
        )

    def get_db() -> Session:
        db = app.state.session_factory()
        try:
            yield db
        finally:
            db.close()

    def current_user(
        authorization: Annotated[str | None, Header()] = None,
        db: Session = Depends(get_db),
    ) -> User:
        token = _parse_bearer_token(authorization)
        session = resolve_active_session(db, token) if token is not None else None
        user = db.get(User, session.user_id) if session is not None else None
        if user is None:
            raise HTTPException(status_code=401)
        return user

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "product": PRODUCT_NAME}

    @app.get("/ready")
    def ready() -> dict[str, object]:
        return {"status": "ready", "dependencies": []}

    @app.post("/api/auth/login", response_model=LoginResponse)
    def login(request: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse | JSONResponse:
        user, error = authenticate_user(db, request.username, request.password)
        if user is None:
            return _error_response(401, "invalid_credentials", error or "Invalid username or password")
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=settings.auth_session_ttl_seconds)
        token, _ = create_auth_session(db, user, expires_at=expires_at)
        db.commit()
        return LoginResponse(
            access_token=token,
            expires_at=expires_at,
            user=PublicUser(username=user.username, role=user.role),
        )

    @app.get("/api/auth/me", response_model=PublicUser)
    def auth_me(user: User = Depends(current_user)) -> PublicUser:
        return PublicUser(username=user.username, role=user.role)

    @app.post("/api/diagnosis/query", response_model=DiagnosisResult)
    def diagnosis_query(request: DiagnosisRequest) -> JSONResponse:
        workflow = app.state.diagnosis_workflow
        if workflow is None:
            workflow = build_default_workflow(settings)
            app.state.diagnosis_workflow = workflow
        result = workflow.invoke({"request_id": str(uuid4()), **request.model_dump()})
        return diagnosis_json_response(result)

    return app


def _parse_bearer_token(authorization: str | None) -> str | None:
    if authorization is None:
        return None
    scheme, _, token = authorization.partition(" ")
    return token if scheme.lower() == "bearer" and token else None


def _error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": {"code": code, "message": message}})
