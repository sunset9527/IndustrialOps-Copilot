"""Add v0.4 assets, persisted diagnosis, work-order, and auth-session tables."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "v04_assets_work_orders"
down_revision = "v01_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "equipment_models",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("equipment_model_id", sa.String(length=120), nullable=False),
        sa.Column("pack_id", sa.String(length=120), nullable=False),
        sa.Column("manufacturer", sa.String(length=120), nullable=False),
        sa.Column("model_name", sa.String(length=120), nullable=False),
        sa.Column("controller_or_firmware_scope", sa.String(length=160), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("equipment_model_id"),
    )
    op.create_index("ix_equipment_models_equipment_model_id", "equipment_models", ["equipment_model_id"])
    op.create_index("ix_equipment_models_pack_id", "equipment_models", ["pack_id"])
    op.create_table(
        "assets",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("asset_id", sa.String(length=120), nullable=False),
        sa.Column("equipment_model_id", sa.String(length=120), nullable=False),
        sa.Column("display_name", sa.String(length=200), nullable=False),
        sa.Column("site", sa.String(length=160), nullable=True),
        sa.Column("line", sa.String(length=160), nullable=True),
        sa.Column("location", sa.String(length=160), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="available"),
        sa.Column("synthetic", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["equipment_model_id"], ["equipment_models.equipment_model_id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("asset_id"),
    )
    op.create_index("ix_assets_asset_id", "assets", ["asset_id"])
    op.create_index("ix_assets_equipment_model_id", "assets", ["equipment_model_id"])
    op.create_index("ix_assets_status", "assets", ["status"])
    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("ix_auth_sessions_token_hash", "auth_sessions", ["token_hash"])
    op.create_index("ix_auth_sessions_user_id", "auth_sessions", ["user_id"])
    op.create_index("ix_auth_sessions_expires_at", "auth_sessions", ["expires_at"])
    op.create_table(
        "diagnosis_records",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("request_id", sa.String(length=120), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("asset_id", sa.String(length=120), nullable=True),
        sa.Column("pack_id", sa.String(length=120), nullable=False),
        sa.Column("model", sa.String(length=120), nullable=True),
        sa.Column("controller", sa.String(length=120), nullable=True),
        sa.Column("status", sa.String(length=48), nullable=False),
        sa.Column("intent", sa.String(length=48), nullable=False),
        sa.Column("request_snapshot", sa.JSON(), nullable=False),
        sa.Column("result_snapshot", sa.JSON(), nullable=False),
        sa.Column("citations_snapshot", sa.JSON(), nullable=False),
        sa.Column("knowledge_pack_version", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.asset_id"], ondelete="SET NULL"),
        sa.UniqueConstraint("request_id"),
    )
    op.create_index("ix_diagnosis_records_request_id", "diagnosis_records", ["request_id"])
    op.create_index("ix_diagnosis_records_asset_id", "diagnosis_records", ["asset_id"])
    op.create_index("ix_diagnosis_records_pack_id", "diagnosis_records", ["pack_id"])
    op.create_index("ix_diagnosis_records_status", "diagnosis_records", ["status"])
    op.create_table(
        "work_orders",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("work_order_id", sa.String(length=120), nullable=False),
        sa.Column("asset_id", sa.String(length=120), nullable=False),
        sa.Column("diagnosis_request_id", sa.String(length=120), nullable=False),
        sa.Column("thread_id", sa.String(length=160), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("description", sa.String(length=4000), nullable=False),
        sa.Column("priority", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("assigned_to_user_id", sa.Integer(), nullable=True),
        sa.Column("diagnosis_snapshot", sa.JSON(), nullable=False),
        sa.Column("inspection_steps_snapshot", sa.JSON(), nullable=False),
        sa.Column("safety_prerequisites_snapshot", sa.JSON(), nullable=False),
        sa.Column("citations_snapshot", sa.JSON(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.asset_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["diagnosis_request_id"], ["diagnosis_records.request_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["assigned_to_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("work_order_id"),
        sa.UniqueConstraint("thread_id"),
    )
    op.create_index("ix_work_orders_work_order_id", "work_orders", ["work_order_id"])
    op.create_index("ix_work_orders_asset_id", "work_orders", ["asset_id"])
    op.create_index("ix_work_orders_diagnosis_request_id", "work_orders", ["diagnosis_request_id"])
    op.create_index("ix_work_orders_thread_id", "work_orders", ["thread_id"])
    op.create_index("ix_work_orders_status", "work_orders", ["status"])
    op.create_index("ix_work_orders_assigned_to_user_id", "work_orders", ["assigned_to_user_id"])
    op.create_index("ix_work_orders_created_by_user_id", "work_orders", ["created_by_user_id"])
    op.create_table(
        "approval_decisions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("work_order_id", sa.String(length=120), nullable=False),
        sa.Column("thread_id", sa.String(length=160), nullable=False),
        sa.Column("decision", sa.String(length=16), nullable=False),
        sa.Column("reason", sa.String(length=1000), nullable=True),
        sa.Column("decided_by_user_id", sa.Integer(), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["work_order_id"], ["work_orders.work_order_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["decided_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("work_order_id"),
        sa.UniqueConstraint("thread_id"),
    )
    op.create_index("ix_approval_decisions_work_order_id", "approval_decisions", ["work_order_id"])
    op.create_index("ix_approval_decisions_thread_id", "approval_decisions", ["thread_id"])
    op.create_index("ix_approval_decisions_decided_by_user_id", "approval_decisions", ["decided_by_user_id"])
    op.create_table(
        "work_order_transitions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("work_order_id", sa.String(length=120), nullable=False),
        sa.Column("action", sa.String(length=32), nullable=False),
        sa.Column("from_status", sa.String(length=32), nullable=False),
        sa.Column("to_status", sa.String(length=32), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("reason", sa.String(length=1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["work_order_id"], ["work_orders.work_order_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_work_order_transitions_work_order_id", "work_order_transitions", ["work_order_id"])
    op.create_index("ix_work_order_transitions_actor_user_id", "work_order_transitions", ["actor_user_id"])
    op.create_table(
        "langgraph_checkpoints",
        sa.Column("thread_id", sa.String(length=160), nullable=False),
        sa.Column("checkpoint_ns", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("checkpoint_id", sa.String(length=160), nullable=False),
        sa.Column("parent_checkpoint_id", sa.String(length=160), nullable=True),
        sa.Column("checkpoint_type", sa.String(length=64), nullable=False),
        sa.Column("checkpoint_blob", sa.LargeBinary(), nullable=False),
        sa.Column("metadata_type", sa.String(length=64), nullable=False),
        sa.Column("metadata_blob", sa.LargeBinary(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("thread_id", "checkpoint_ns", "checkpoint_id"),
    )
    op.create_index("ix_langgraph_checkpoints_thread_id", "langgraph_checkpoints", ["thread_id"])
    op.create_table(
        "langgraph_checkpoint_writes",
        sa.Column("thread_id", sa.String(length=160), nullable=False),
        sa.Column("checkpoint_ns", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("checkpoint_id", sa.String(length=160), nullable=False),
        sa.Column("task_id", sa.String(length=160), nullable=False),
        sa.Column("write_index", sa.Integer(), nullable=False),
        sa.Column("channel", sa.String(length=160), nullable=False),
        sa.Column("value_type", sa.String(length=64), nullable=False),
        sa.Column("value_blob", sa.LargeBinary(), nullable=False),
        sa.Column("task_path", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("thread_id", "checkpoint_ns", "checkpoint_id", "task_id", "write_index"),
    )
    op.create_index("ix_langgraph_checkpoint_writes_thread_id", "langgraph_checkpoint_writes", ["thread_id"])


def downgrade() -> None:
    op.drop_index("ix_langgraph_checkpoint_writes_thread_id", table_name="langgraph_checkpoint_writes")
    op.drop_table("langgraph_checkpoint_writes")
    op.drop_index("ix_langgraph_checkpoints_thread_id", table_name="langgraph_checkpoints")
    op.drop_table("langgraph_checkpoints")
    op.drop_index("ix_work_order_transitions_actor_user_id", table_name="work_order_transitions")
    op.drop_index("ix_work_order_transitions_work_order_id", table_name="work_order_transitions")
    op.drop_table("work_order_transitions")
    op.drop_index("ix_approval_decisions_decided_by_user_id", table_name="approval_decisions")
    op.drop_index("ix_approval_decisions_thread_id", table_name="approval_decisions")
    op.drop_index("ix_approval_decisions_work_order_id", table_name="approval_decisions")
    op.drop_table("approval_decisions")
    op.drop_index("ix_work_orders_created_by_user_id", table_name="work_orders")
    op.drop_index("ix_work_orders_assigned_to_user_id", table_name="work_orders")
    op.drop_index("ix_work_orders_status", table_name="work_orders")
    op.drop_index("ix_work_orders_thread_id", table_name="work_orders")
    op.drop_index("ix_work_orders_diagnosis_request_id", table_name="work_orders")
    op.drop_index("ix_work_orders_asset_id", table_name="work_orders")
    op.drop_index("ix_work_orders_work_order_id", table_name="work_orders")
    op.drop_table("work_orders")
    op.drop_index("ix_diagnosis_records_status", table_name="diagnosis_records")
    op.drop_index("ix_diagnosis_records_pack_id", table_name="diagnosis_records")
    op.drop_index("ix_diagnosis_records_asset_id", table_name="diagnosis_records")
    op.drop_index("ix_diagnosis_records_request_id", table_name="diagnosis_records")
    op.drop_table("diagnosis_records")
    op.drop_index("ix_auth_sessions_expires_at", table_name="auth_sessions")
    op.drop_index("ix_auth_sessions_user_id", table_name="auth_sessions")
    op.drop_index("ix_auth_sessions_token_hash", table_name="auth_sessions")
    op.drop_table("auth_sessions")
    op.drop_index("ix_assets_status", table_name="assets")
    op.drop_index("ix_assets_equipment_model_id", table_name="assets")
    op.drop_index("ix_assets_asset_id", table_name="assets")
    op.drop_table("assets")
    op.drop_index("ix_equipment_models_pack_id", table_name="equipment_models")
    op.drop_index("ix_equipment_models_equipment_model_id", table_name="equipment_models")
    op.drop_table("equipment_models")
