"""Minimal FastAPI application factory for IndustrialOps v0.1."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from threading import RLock
from typing import Annotated, Callable, Literal
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from starlette.exceptions import HTTPException as StarletteHTTPException

from industrialops.app_metadata import PRODUCT_NAME
from industrialops.checkpoint import SQLAlchemyCheckpointSaver
from industrialops.config import Settings
from industrialops.diagnosis.response import diagnosis_json_response
from industrialops.diagnosis.runtime import build_default_workflow
from industrialops.diagnosis.schemas import DiagnosisRequest, DiagnosisResult
from industrialops.middleware.request_size import RequestBodyLimitMiddleware
from industrialops.models.user import User
from industrialops.models.audit import AuditEvent
from industrialops.models.work_order import ApprovalDecision, WorkOrder, WorkOrderTransition
from industrialops.domain.work_orders import WorkOrderAction, WorkOrderTransitionError
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
from industrialops.services.audit import record_audit_event
from industrialops.services.work_order_drafts import WorkOrderDraftNotAllowedError, create_work_order_draft
from industrialops.services.work_orders import (
    ApprovalAlreadyDecidedError,
    AssigneeNotFoundError,
    WorkOrderNotFoundError,
    WorkOrderVersionConflictError,
    apply_approval_decision,
    get_work_order,
    list_work_orders,
    transition_existing_work_order,
)
from industrialops.workflow.approval import build_approval_workflow


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


class ApprovalRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=1000)


class RejectWorkOrderRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=1000)


class WorkOrderTransitionRequest(BaseModel):
    action: Literal["assign", "start", "complete", "close", "cancel"]
    expected_version: int = Field(ge=1)
    assignee_username: str | None = Field(default=None, min_length=1, max_length=50)
    reason: str | None = Field(default=None, max_length=1000)


class WorkOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    work_order_id: str
    asset_id: str
    diagnosis_request_id: str
    thread_id: str
    title: str
    description: str
    priority: str
    status: str
    assigned_to_user_id: int | None
    inspection_steps_snapshot: list[str]
    safety_prerequisites_snapshot: list[str]
    citations_snapshot: list[dict[str, object]]
    version: int


class ApprovalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    decision: str
    reason: str | None
    decided_by_user_id: int


class WorkOrderTransitionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    action: str
    from_status: str
    to_status: str
    actor_user_id: int | None
    reason: str | None


class WorkOrderDetailResponse(WorkOrderResponse):
    approval: ApprovalResponse | None
    transitions: list[WorkOrderTransitionResponse]
    audit_actions: list[str]


class WorkOrderListResponse(BaseModel):
    items: list[WorkOrderResponse]
    total: int
    limit: int
    offset: int


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
    # SQLite ignores SELECT ... FOR UPDATE.  One per-app lock keeps concurrent
    # approval resumes deterministic in the supported SQLite test deployment;
    # MySQL row locks and the unique decision constraints remain the cross-
    # process protection in production.
    app.state.approval_decision_lock = RLock()
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

    def require_approver(user: User = Depends(current_user)) -> User:
        if user.role not in {"approver", "admin"}:
            raise HTTPException(status_code=403)
        return user

    def interrupt_draft_workflow(db: Session, draft: WorkOrder) -> None:
        saver = SQLAlchemyCheckpointSaver(app.state.session_factory)
        workflow = build_approval_workflow(saver)
        with saver.bind_session(db):
            workflow.invoke(
                {
                    "work_order_id": draft.work_order_id,
                    "safety_summary": draft.safety_prerequisites_snapshot,
                    "citations": draft.citations_snapshot,
                },
                {"configurable": {"thread_id": draft.thread_id}},
            )

    def resume_approval_workflow(db: Session, work_order: WorkOrder, decision: str) -> None:
        from langgraph.types import Command

        saver = SQLAlchemyCheckpointSaver(app.state.session_factory)
        workflow = build_approval_workflow(saver)
        with saver.bind_session(db):
            resumed = workflow.invoke(
                Command(resume={"decision": decision}),
                {"configurable": {"thread_id": work_order.thread_id}},
            )
        if resumed.get("approval_outcome") != decision:
            raise ValueError("approval workflow did not return the submitted decision")

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
            record_audit_event(
                db,
                actor_user_id=None,
                action="auth.login_failed",
                subject_type="auth",
                subject_id="login",
                detail='{"reason":"invalid_credentials"}',
            )
            db.commit()
            return _error_response(401, "invalid_credentials", error or "Invalid username or password")
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=settings.auth_session_ttl_seconds)
        token, _ = create_auth_session(db, user, expires_at=expires_at)
        record_audit_event(
            db,
            actor_user_id=user.id,
            action="auth.login_succeeded",
            subject_type="user",
            subject_id=user.username,
            detail='{"reason":"password_verified"}',
        )
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
        user: User = Depends(require_admin),
        db: Session = Depends(get_db),
    ) -> AssetResponse | JSONResponse:
        try:
            asset = create_asset(db, **request.model_dump())
            record_audit_event(
                db, actor_user_id=user.id, action="asset.created", subject_type="asset",
                subject_id=asset.asset_id, detail=f'{{"equipment_model_id":"{asset.equipment_model_id}"}}',
            )
            db.commit()
        except EquipmentModelNotFoundError:
            db.rollback()
            return _error_response(404, "equipment_model_not_found", "Equipment model was not found")
        return AssetResponse.model_validate(asset)

    @app.patch("/api/equipment/assets/{asset_id}", response_model=AssetResponse)
    def assets_update(
        asset_id: str,
        request: AssetUpdateRequest,
        user: User = Depends(require_admin),
        db: Session = Depends(get_db),
    ) -> AssetResponse | JSONResponse:
        try:
            asset = update_asset(db, asset_id, **request.model_dump(exclude_none=True))
            record_audit_event(
                db, actor_user_id=user.id, action="asset.updated", subject_type="asset",
                subject_id=asset.asset_id, detail=f'{{"version":{asset.version},"status":"{asset.status}"}}',
            )
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
            record_audit_event(
                db, actor_user_id=user.id, action="work_order.draft_created", subject_type="work_order",
                subject_id=draft.work_order_id, detail=f'{{"thread_id":"{draft.thread_id}","status":"draft"}}',
            )
            record_audit_event(
                db, actor_user_id=user.id, action="work_order.approval_requested", subject_type="work_order",
                subject_id=draft.work_order_id, detail=f'{{"thread_id":"{draft.thread_id}"}}',
            )
            interrupt_draft_workflow(db, draft)
            record_audit_event(
                db, actor_user_id=user.id, action="workflow.interrupted", subject_type="work_order",
                subject_id=draft.work_order_id, detail=f'{{"thread_id":"{draft.thread_id}"}}',
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

    @app.get("/api/work-orders", response_model=WorkOrderListResponse)
    def work_orders_list(
        _: User = Depends(current_user),
        db: Session = Depends(get_db),
        asset_id: str | None = None,
        work_order_status: str | None = Query(default=None, alias="status"),
        created_by_user_id: int | None = None,
        decided_by_user_id: int | None = None,
        limit: int = Query(default=50, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
    ) -> WorkOrderListResponse:
        work_orders, total = list_work_orders(
            db, asset_id=asset_id, status=work_order_status, created_by_user_id=created_by_user_id,
            decided_by_user_id=decided_by_user_id, limit=limit, offset=offset,
        )
        return WorkOrderListResponse(
            items=[WorkOrderResponse.model_validate(work_order) for work_order in work_orders],
            total=total, limit=limit, offset=offset,
        )

    @app.get("/api/work-orders/{work_order_id}", response_model=WorkOrderDetailResponse)
    def work_order_detail(
        work_order_id: str,
        _: User = Depends(current_user),
        db: Session = Depends(get_db),
    ) -> WorkOrderDetailResponse | JSONResponse:
        try:
            work_order = get_work_order(db, work_order_id)
        except WorkOrderNotFoundError:
            return _error_response(404, "work_order_not_found", "Work order was not found")
        approval = db.scalar(select(ApprovalDecision).where(ApprovalDecision.work_order_id == work_order_id))
        transitions = list(db.scalars(
            select(WorkOrderTransition).where(WorkOrderTransition.work_order_id == work_order_id).order_by(WorkOrderTransition.id)
        ))
        audit_actions = list(db.scalars(
            select(AuditEvent.action).where(
                AuditEvent.subject_type == "work_order", AuditEvent.subject_id == work_order_id,
            ).order_by(AuditEvent.id)
        ))
        response = WorkOrderResponse.model_validate(work_order).model_dump()
        return WorkOrderDetailResponse(
            **response,
            approval=ApprovalResponse.model_validate(approval) if approval else None,
            transitions=[WorkOrderTransitionResponse.model_validate(item) for item in transitions],
            audit_actions=audit_actions,
        )

    def decide_work_order(
        work_order_id: str,
        decision: Literal["approved", "rejected"],
        reason: str | None,
        user: User,
        db: Session,
    ) -> WorkOrderResponse | JSONResponse:
        with app.state.approval_decision_lock:
            return _decide_work_order(work_order_id, decision, reason, user, db)

    def _decide_work_order(
        work_order_id: str,
        decision: Literal["approved", "rejected"],
        reason: str | None,
        user: User,
        db: Session,
    ) -> WorkOrderResponse | JSONResponse:
        try:
            work_order = get_work_order(db, work_order_id, lock=True)
            existing = db.scalar(select(ApprovalDecision).where(ApprovalDecision.work_order_id == work_order_id))
            if existing is not None:
                if existing.decision != decision:
                    return _error_response(409, "approval_already_decided", "Approval has already been decided")
                return WorkOrderResponse.model_validate(work_order)
            resume_approval_workflow(db, work_order, decision)
            record_audit_event(
                db, actor_user_id=user.id, action="workflow.resumed", subject_type="work_order",
                subject_id=work_order_id, detail=f'{{"thread_id":"{work_order.thread_id}","decision":"{decision}"}}',
            )
            work_order, _ = apply_approval_decision(
                db, work_order_id=work_order_id, actor=user, decision=decision, reason=reason,
            )
            db.commit()
            return WorkOrderResponse.model_validate(work_order)
        except WorkOrderNotFoundError:
            db.rollback()
            return _error_response(404, "work_order_not_found", "Work order was not found")
        except ApprovalAlreadyDecidedError:
            db.rollback()
            return _error_response(409, "approval_already_decided", "Approval has already been decided")
        except WorkOrderTransitionError:
            db.rollback()
            return _error_response(409, "invalid_work_order_transition", "The requested work-order transition is not allowed")
        except Exception:
            db.rollback()
            record_audit_event(
                db,
                actor_user_id=user.id,
                action="workflow.resume_failed",
                subject_type="work_order",
                subject_id=work_order_id,
                detail='{"reason":"workflow_resume_failed"}',
            )
            db.commit()
            return _error_response(500, "workflow_resume_failed", "Approval could not be resumed")

    @app.post("/api/work-orders/{work_order_id}/approve", response_model=WorkOrderResponse)
    def work_order_approve(
        work_order_id: str,
        request: ApprovalRequest,
        user: User = Depends(require_approver),
        db: Session = Depends(get_db),
    ) -> WorkOrderResponse | JSONResponse:
        return decide_work_order(work_order_id, "approved", request.reason, user, db)

    @app.post("/api/work-orders/{work_order_id}/reject", response_model=WorkOrderResponse)
    def work_order_reject(
        work_order_id: str,
        request: RejectWorkOrderRequest,
        user: User = Depends(require_approver),
        db: Session = Depends(get_db),
    ) -> WorkOrderResponse | JSONResponse:
        return decide_work_order(work_order_id, "rejected", request.reason, user, db)

    @app.post("/api/work-orders/{work_order_id}/transitions", response_model=WorkOrderResponse)
    def work_order_transition(
        work_order_id: str,
        request: WorkOrderTransitionRequest,
        user: User = Depends(current_user),
        db: Session = Depends(get_db),
    ) -> WorkOrderResponse | JSONResponse:
        try:
            work_order = transition_existing_work_order(
                db, work_order_id=work_order_id, actor=user, action=WorkOrderAction(request.action),
                expected_version=request.expected_version, reason=request.reason, assignee_username=request.assignee_username,
            )
            db.commit()
            return WorkOrderResponse.model_validate(work_order)
        except WorkOrderNotFoundError:
            db.rollback()
            return _error_response(404, "work_order_not_found", "Work order was not found")
        except AssigneeNotFoundError:
            db.rollback()
            return _error_response(404, "assignee_not_found", "Assignee was not found")
        except WorkOrderVersionConflictError:
            db.rollback()
            return _error_response(409, "stale_resource_version", "Work order has changed since it was read")
        except WorkOrderTransitionError:
            db.rollback()
            return _error_response(409, "invalid_work_order_transition", "The requested work-order transition is not allowed")

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
