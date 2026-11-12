"""Minimal FastAPI application factory for IndustrialOps v0.1."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from typing import Annotated, Callable
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
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
from industrialops.services.assets import (
    AssetNotFoundError,
    AssetVersionConflictError,
    EquipmentModelNotFoundError,
    create_asset,
    list_assets,
    update_asset,
)
from industrialops.services.diagnosis_records import record_diagnosis
from industrialops.services.work_order_drafts import WorkOrderDraftNotAllowedError, create_work_order_draft


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


class AssetCreateRequest(BaseModel):
    asset_id: str = Field(min_length=1, max_length=120)
    equipment_model_id: str = Field(min_length=1, max_length=120)
    display_name: str = Field(min_length=1, max_length=200)
    site: str | None = Field(default=None, max_length=160)
    line: str | None = Field(default=None, max_length=160)
    location: str | None = Field(default=None, max_length=160)
    status: str = Field(default="available", pattern="^(available|maintenance|out_of_service)$")


class AssetUpdateRequest(BaseModel):
    expected_version: int = Field(ge=1)
    display_name: str | None = Field(default=None, min_length=1, max_length=200)
    site: str | None = Field(default=None, max_length=160)
    line: str | None = Field(default=None, max_length=160)
    location: str | None = Field(default=None, max_length=160)
    status: str | None = Field(default=None, pattern="^(available|maintenance|out_of_service)$")


class AssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    asset_id: str
    equipment_model_id: str
    display_name: str
    site: str | None
    line: str | None
    location: str | None
    status: str
    synthetic: bool
    version: int


class AssetListResponse(BaseModel):
    items: list[AssetResponse]
    total: int
    limit: int
    offset: int


class WorkOrderDraftRequest(BaseModel):
    diagnosis_request_id: str = Field(min_length=1, max_length=120)
    asset_id: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=240)
    description: str = Field(min_length=1, max_length=4000)
    priority: str = Field(min_length=1, max_length=32)


class WorkOrderDraftResponse(BaseModel):
    work_order_id: str
    thread_id: str
    status: str
    approval_status: str
    citations_snapshot: list[dict[str, object]]


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
        if exception.status_code == 403:
            return _error_response(403, "forbidden", "The current role is not authorized for this operation")
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

    def require_admin(user: User = Depends(current_user)) -> User:
        if user.role != "admin":
            raise HTTPException(status_code=403)
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

    @app.get("/api/equipment/assets", response_model=AssetListResponse)
    def assets_list(
        _: User = Depends(current_user),
        db: Session = Depends(get_db),
        pack_id: str | None = None,
        equipment_model_id: str | None = None,
        asset_status: str | None = Query(default=None, alias="status"),
        limit: int = Query(default=50, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
    ) -> AssetListResponse:
        assets, total = list_assets(
            db, pack_id=pack_id, equipment_model_id=equipment_model_id, status=asset_status, limit=limit, offset=offset
        )
        return AssetListResponse(
            items=[AssetResponse.model_validate(asset) for asset in assets], total=total, limit=limit, offset=offset
        )

    @app.post("/api/equipment/assets", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
    def assets_create(
        request: AssetCreateRequest,
        _: User = Depends(require_admin),
        db: Session = Depends(get_db),
    ) -> AssetResponse | JSONResponse:
        try:
            asset = create_asset(db, **request.model_dump())
            db.commit()
        except EquipmentModelNotFoundError:
            db.rollback()
            return _error_response(404, "equipment_model_not_found", "Equipment model was not found")
        return AssetResponse.model_validate(asset)

    @app.patch("/api/equipment/assets/{asset_id}", response_model=AssetResponse)
    def assets_update(
        asset_id: str,
        request: AssetUpdateRequest,
        _: User = Depends(require_admin),
        db: Session = Depends(get_db),
    ) -> AssetResponse | JSONResponse:
        try:
            asset = update_asset(db, asset_id, **request.model_dump(exclude_none=True))
            db.commit()
        except AssetNotFoundError:
            db.rollback()
            return _error_response(404, "asset_not_found", "Asset was not found")
        except AssetVersionConflictError:
            db.rollback()
            return _error_response(409, "stale_resource_version", "Asset has changed since it was read")
        return AssetResponse.model_validate(asset)

    @app.post("/api/work-orders/drafts", response_model=WorkOrderDraftResponse, status_code=status.HTTP_202_ACCEPTED)
    def work_order_draft_create(
        request: WorkOrderDraftRequest,
        user: User = Depends(current_user),
        db: Session = Depends(get_db),
    ) -> WorkOrderDraftResponse | JSONResponse:
        try:
            draft = create_work_order_draft(
                db,
                diagnosis_request_id=request.diagnosis_request_id,
                asset_id=request.asset_id,
                created_by_user_id=user.id,
                work_order_id=str(uuid4()),
                thread_id=str(uuid4()),
                title=request.title,
                description=request.description,
                priority=request.priority,
            )
            db.commit()
        except WorkOrderDraftNotAllowedError:
            db.rollback()
            return _error_response(409, "work_order_draft_not_allowed", "The diagnosis cannot create a work-order draft")
        return WorkOrderDraftResponse(
            work_order_id=draft.work_order_id,
            thread_id=draft.thread_id,
            status=draft.status,
            approval_status="pending_approval",
            citations_snapshot=draft.citations_snapshot,
        )

    @app.post("/api/diagnosis/query", response_model=DiagnosisResult)
    def diagnosis_query(request: DiagnosisRequest, db: Session = Depends(get_db)) -> JSONResponse:
        workflow = app.state.diagnosis_workflow
        if workflow is None:
            workflow = build_default_workflow(settings)
            app.state.diagnosis_workflow = workflow
        result = workflow.invoke({"request_id": str(uuid4()), **request.model_dump()})
        record_diagnosis(
            db,
            request_id=result.request_id,
            created_by_user_id=None,
            asset_id=request.asset_id,
            pack_id=request.pack_id,
            model=request.model,
            controller=request.controller,
            status=result.status,
            intent=result.intent,
            request_snapshot=request.model_dump(mode="json"),
            result_snapshot=result.model_dump(mode="json"),
            citations_snapshot=[citation.model_dump(mode="json") for citation in result.citations],
            knowledge_pack_version=request.pack_id,
        )
        db.commit()
        return diagnosis_json_response(result)

    return app


def _parse_bearer_token(authorization: str | None) -> str | None:
    if authorization is None:
        return None
    scheme, _, token = authorization.partition(" ")
    return token if scheme.lower() == "bearer" and token else None


def _error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": {"code": code, "message": message}})
