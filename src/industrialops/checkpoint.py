"""Synchronous SQLAlchemy-backed persistence for LangGraph checkpoints."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from threading import RLock
from typing import Any

from langgraph.checkpoint.base import (
    WRITES_IDX_MAP,
    BaseCheckpointSaver,
    CheckpointTuple,
    get_checkpoint_id,
    get_checkpoint_metadata,
)
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker

from industrialops.models.checkpoint import LangGraphCheckpoint, LangGraphCheckpointWrite


class SQLAlchemyCheckpointSaver(BaseCheckpointSaver):
    """Persist complete LangGraph checkpoints and pending writes in the application database.

    Channel values are deliberately stored inside the typed checkpoint payload.  This keeps
    the schema compact while retaining all state needed to resume a paused approval graph.
    """

    def __init__(self, session_factory: sessionmaker[Session], **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._session_factory = session_factory
        self._lock = RLock()
        self._bound_session: Session | None = None

    @contextmanager
    def bind_session(self, session: Session) -> Iterator["SQLAlchemyCheckpointSaver"]:
        """Use an outer service transaction without committing it from the saver."""

        with self._lock:
            if self._bound_session is not None:
                raise RuntimeError("a checkpoint saver may only bind one session at a time")
            self._bound_session = session
        try:
            yield self
        finally:
            with self._lock:
                self._bound_session = None

    @contextmanager
    def _session(self) -> Iterator[Session]:
        # LangGraph may invoke saver operations from worker threads.  Serializing each
        # database operation keeps SQLite's single StaticPool connection valid in tests
        # and avoids interleaving writes for one configured application saver.
        with self._lock:
            session = self._bound_session or self._session_factory()
            owns_session = session is not self._bound_session
            try:
                yield session
                if owns_session:
                    session.commit()
                else:
                    session.flush()
            except Exception:
                if owns_session:
                    session.rollback()
                raise
            finally:
                if owns_session:
                    session.close()

    @staticmethod
    def _identity(config: dict[str, Any]) -> tuple[str, str, str | None]:
        configurable = config["configurable"]
        return (
            configurable["thread_id"],
            configurable.get("checkpoint_ns", ""),
            configurable.get("checkpoint_id"),
        )

    def _tuple_from_row(self, session: Session, row: LangGraphCheckpoint) -> CheckpointTuple:
        writes = session.scalars(
            select(LangGraphCheckpointWrite)
            .where(
                LangGraphCheckpointWrite.thread_id == row.thread_id,
                LangGraphCheckpointWrite.checkpoint_ns == row.checkpoint_ns,
                LangGraphCheckpointWrite.checkpoint_id == row.checkpoint_id,
            )
            .order_by(LangGraphCheckpointWrite.task_id, LangGraphCheckpointWrite.write_index)
        ).all()
        return CheckpointTuple(
            config={
                "configurable": {
                    "thread_id": row.thread_id,
                    "checkpoint_ns": row.checkpoint_ns,
                    "checkpoint_id": row.checkpoint_id,
                }
            },
            checkpoint=self.serde.loads_typed((row.checkpoint_type, row.checkpoint_blob)),
            metadata=self.serde.loads_typed((row.metadata_type, row.metadata_blob)),
            parent_config=(
                {
                    "configurable": {
                        "thread_id": row.thread_id,
                        "checkpoint_ns": row.checkpoint_ns,
                        "checkpoint_id": row.parent_checkpoint_id,
                    }
                }
                if row.parent_checkpoint_id
                else None
            ),
            pending_writes=[
                (write.task_id, write.channel, self.serde.loads_typed((write.value_type, write.value_blob)))
                for write in writes
            ],
        )

    def get_tuple(self, config: dict[str, Any]) -> CheckpointTuple | None:
        thread_id, checkpoint_ns, checkpoint_id = self._identity(config)
        with self._session() as session:
            statement = select(LangGraphCheckpoint).where(
                LangGraphCheckpoint.thread_id == thread_id,
                LangGraphCheckpoint.checkpoint_ns == checkpoint_ns,
            )
            if checkpoint_id:
                statement = statement.where(LangGraphCheckpoint.checkpoint_id == checkpoint_id)
            else:
                statement = statement.order_by(LangGraphCheckpoint.checkpoint_id.desc()).limit(1)
            row = session.scalar(statement)
            return self._tuple_from_row(session, row) if row else None

    def list(
        self,
        config: dict[str, Any] | None,
        *,
        filter: dict[str, Any] | None = None,
        before: dict[str, Any] | None = None,
        limit: int | None = None,
    ) -> Iterator[CheckpointTuple]:
        with self._session() as session:
            statement = select(LangGraphCheckpoint).order_by(LangGraphCheckpoint.checkpoint_id.desc())
            if config:
                thread_id, checkpoint_ns, checkpoint_id = self._identity(config)
                statement = statement.where(LangGraphCheckpoint.thread_id == thread_id)
                if checkpoint_ns is not None:
                    statement = statement.where(LangGraphCheckpoint.checkpoint_ns == checkpoint_ns)
                if checkpoint_id:
                    statement = statement.where(LangGraphCheckpoint.checkpoint_id == checkpoint_id)
            if before and (before_checkpoint_id := get_checkpoint_id(before)):
                statement = statement.where(LangGraphCheckpoint.checkpoint_id < before_checkpoint_id)

            rows = session.scalars(statement).all()
            yielded = 0
            for row in rows:
                checkpoint_tuple = self._tuple_from_row(session, row)
                if filter and not all(
                    value == checkpoint_tuple.metadata.get(key) for key, value in filter.items()
                ):
                    continue
                if limit is not None and yielded >= limit:
                    break
                yielded += 1
                yield checkpoint_tuple

    def put(
        self,
        config: dict[str, Any],
        checkpoint: dict[str, Any],
        metadata: dict[str, Any],
        new_versions: dict[str, Any],
    ) -> dict[str, Any]:
        del new_versions  # The complete typed checkpoint includes the current channel values.
        thread_id, checkpoint_ns, parent_checkpoint_id = self._identity(config)
        checkpoint_id = checkpoint["id"]
        checkpoint_type, checkpoint_blob = self.serde.dumps_typed(checkpoint)
        metadata_type, metadata_blob = self.serde.dumps_typed(get_checkpoint_metadata(config, metadata))

        with self._session() as session:
            row = session.get(LangGraphCheckpoint, (thread_id, checkpoint_ns, checkpoint_id))
            if row is None:
                row = LangGraphCheckpoint(
                    thread_id=thread_id,
                    checkpoint_ns=checkpoint_ns,
                    checkpoint_id=checkpoint_id,
                    parent_checkpoint_id=parent_checkpoint_id,
                    checkpoint_type=checkpoint_type,
                    checkpoint_blob=checkpoint_blob,
                    metadata_type=metadata_type,
                    metadata_blob=metadata_blob,
                )
                session.add(row)
            else:
                row.parent_checkpoint_id = parent_checkpoint_id
                row.checkpoint_type = checkpoint_type
                row.checkpoint_blob = checkpoint_blob
                row.metadata_type = metadata_type
                row.metadata_blob = metadata_blob

        return {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns,
                "checkpoint_id": checkpoint_id,
            }
        }

    def put_writes(
        self,
        config: dict[str, Any],
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        thread_id, checkpoint_ns, checkpoint_id = self._identity(config)
        if checkpoint_id is None:
            raise ValueError("checkpoint_id is required to persist pending writes")

        with self._session() as session:
            for index, (channel, value) in enumerate(writes):
                write_index = WRITES_IDX_MAP.get(channel, index)
                row = session.get(
                    LangGraphCheckpointWrite,
                    (thread_id, checkpoint_ns, checkpoint_id, task_id, write_index),
                )
                if row is not None and write_index >= 0:
                    continue
                value_type, value_blob = self.serde.dumps_typed(value)
                if row is None:
                    session.add(
                        LangGraphCheckpointWrite(
                            thread_id=thread_id,
                            checkpoint_ns=checkpoint_ns,
                            checkpoint_id=checkpoint_id,
                            task_id=task_id,
                            write_index=write_index,
                            channel=channel,
                            value_type=value_type,
                            value_blob=value_blob,
                            task_path=task_path,
                        )
                    )
                else:
                    row.channel = channel
                    row.value_type = value_type
                    row.value_blob = value_blob
                    row.task_path = task_path

    def delete_thread(self, thread_id: str) -> None:
        with self._session() as session:
            session.execute(delete(LangGraphCheckpointWrite).where(LangGraphCheckpointWrite.thread_id == thread_id))
            session.execute(delete(LangGraphCheckpoint).where(LangGraphCheckpoint.thread_id == thread_id))
