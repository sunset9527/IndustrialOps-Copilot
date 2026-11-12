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


def _checkpoint(checkpoint_id: str, value: str) -> dict[str, object]:
    return {
        "v": 1,
        "id": checkpoint_id,
        "ts": "2026-11-12T00:00:00+00:00",
        "channel_values": {"approval": value},
        "channel_versions": {"approval": 1},
        "versions_seen": {},
        "updated_channels": ["approval"],
    }


def test_checkpoint_saver_persists_a_checkpoint_and_pending_writes_across_instances() -> None:
    from industrialops.checkpoint import SQLAlchemyCheckpointSaver

    factory = _session_factory()
    config = {"configurable": {"thread_id": "approval-001", "checkpoint_ns": ""}}
    saver = SQLAlchemyCheckpointSaver(factory)

    saved_config = saver.put(config, _checkpoint("checkpoint-001", "pending"), {"source": "loop"}, {"approval": 1})
    saver.put_writes(saved_config, [("approval", {"decision": "approved"})], "approval-task")

    restored = SQLAlchemyCheckpointSaver(factory).get_tuple({"configurable": {"thread_id": "approval-001"}})

    assert restored is not None
    assert restored.config["configurable"]["checkpoint_id"] == "checkpoint-001"
    assert restored.checkpoint["channel_values"] == {"approval": "pending"}
    assert restored.metadata == {"source": "loop"}
    assert restored.pending_writes == [("approval-task", "approval", {"decision": "approved"})]


def test_checkpoint_saver_lists_newest_first_and_deletes_one_thread() -> None:
    from industrialops.checkpoint import SQLAlchemyCheckpointSaver

    saver = SQLAlchemyCheckpointSaver(_session_factory())
    config = {"configurable": {"thread_id": "approval-002", "checkpoint_ns": ""}}
    saver.put(config, _checkpoint("checkpoint-001", "first"), {"source": "input"}, {"approval": 1})
    saver.put(config, _checkpoint("checkpoint-002", "second"), {"source": "loop"}, {"approval": 2})

    assert [item.config["configurable"]["checkpoint_id"] for item in saver.list(config)] == [
        "checkpoint-002",
        "checkpoint-001",
    ]

    saver.delete_thread("approval-002")

    assert saver.get_tuple({"configurable": {"thread_id": "approval-002"}}) is None


def test_checkpoint_saver_can_join_an_outer_business_transaction() -> None:
    from industrialops.checkpoint import SQLAlchemyCheckpointSaver

    factory = _session_factory()
    saver = SQLAlchemyCheckpointSaver(factory)
    config = {"configurable": {"thread_id": "approval-003", "checkpoint_ns": ""}}
    db = factory()
    try:
        with saver.bind_session(db):
            saver.put(config, _checkpoint("checkpoint-001", "pending"), {"source": "input"}, {"approval": 1})
        db.rollback()
    finally:
        db.close()

    assert SQLAlchemyCheckpointSaver(factory).get_tuple(config) is None
