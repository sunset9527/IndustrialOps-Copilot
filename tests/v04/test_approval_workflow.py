from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from industrialops.database import Base


def _session_factory() -> sessionmaker[Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


def test_approval_graph_interrupts_then_resumes_after_rebuilding_the_workflow() -> None:
    from langgraph.types import Command

    from industrialops.checkpoint import SQLAlchemyCheckpointSaver
    from industrialops.workflow.approval import build_approval_workflow

    factory = _session_factory()
    config = {"configurable": {"thread_id": "approval-001"}}
    initial = build_approval_workflow(SQLAlchemyCheckpointSaver(factory))

    paused = initial.invoke(
        {
            "work_order_id": "wo-001",
            "safety_summary": ["执行前需挂牌上锁"],
            "citations": [{"source_id": "haas-manual", "page_number": 42}],
        },
        config,
    )

    assert paused["__interrupt__"][0].value == {
        "work_order_id": "wo-001",
        "safety_summary": ["执行前需挂牌上锁"],
        "citations": [{"source_id": "haas-manual", "page_number": 42}],
    }

    rebuilt = build_approval_workflow(SQLAlchemyCheckpointSaver(factory))
    resumed = rebuilt.invoke(Command(resume={"decision": "approved"}), config)

    assert resumed["approval_outcome"] == "approved"
    assert "__interrupt__" not in resumed


def test_approval_graph_rejects_an_unrecognized_resume_decision() -> None:
    from langgraph.types import Command

    from industrialops.checkpoint import SQLAlchemyCheckpointSaver
    from industrialops.workflow.approval import build_approval_workflow

    factory = _session_factory()
    config = {"configurable": {"thread_id": "approval-002"}}
    workflow = build_approval_workflow(SQLAlchemyCheckpointSaver(factory))
    workflow.invoke({"work_order_id": "wo-002", "safety_summary": [], "citations": []}, config)

    try:
        workflow.invoke(Command(resume={"decision": "defer"}), config)
    except ValueError as error:
        assert str(error) == "approval decision must be approved or rejected"
    else:
        raise AssertionError("unrecognized approval decision was accepted")
