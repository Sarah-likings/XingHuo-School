"""初始建表：13 张表（12 个核心实体 + 治理表 audit_log）

Revision ID: 0001
Revises:
Create Date: 2026-11-16

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

# 订单状态机 7 状态（与 app/core/enums.py 单一来源保持一致）
_ORDER_STATUSES = (
    "OPEN",
    "ASSIGNED",
    "DELIVERED",
    "COMPLETED",
    "APPEALING",
    "CANCELLED",
    "REFUNDED",
)


def upgrade() -> None:
    # ---- user ----
    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_no", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("password_hash", sa.String(length=128), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("verified", sa.Boolean(), nullable=False),
        sa.Column("banned", sa.Boolean(), nullable=False),
        sa.Column("college", sa.String(length=64), nullable=True),
        sa.Column("major", sa.String(length=64), nullable=True),
        sa.Column("grade", sa.String(length=16), nullable=True),
        sa.Column("credit_score", sa.Integer(), nullable=False),
        sa.Column("avatar_key", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("student_no", name="uq_user_student_no"),
    )
    op.create_index("ix_user_banned", "user", ["banned"])

    # ---- task ----
    op.create_table(
        "task",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("publisher_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("reward", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["publisher_id"], ["user.id"]),
    )
    op.create_index("ix_task_category_status_deadline", "task", ["category", "status", "deadline"])
    op.create_index("ix_task_publisher_id", "task", ["publisher_id"])

    # ---- student_verify ----
    op.create_table(
        "student_verify",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("student_no", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("college", sa.String(length=64), nullable=True),
        sa.Column("major", sa.String(length=64), nullable=True),
        sa.Column("grade", sa.String(length=16), nullable=True),
        sa.Column("image_key", sa.String(length=255), nullable=False),
        sa.Column("reject_reason", sa.String(length=255), nullable=True),
        sa.Column("reviewed_by", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["reviewed_by"], ["user.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.UniqueConstraint("user_id", name="uq_student_verify_user_id"),
    )
    op.create_index("ix_student_verify_status", "student_verify", ["status"])

    # ---- order ----
    op.create_table(
        "order",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("employer_id", sa.Integer(), nullable=False),
        sa.Column("taker_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("reward", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN (%s)" % ", ".join(f"'{s}'" for s in _ORDER_STATUSES),
            name="ck_order_status",
        ),
        sa.ForeignKeyConstraint(["employer_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["taker_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["task_id"], ["task.id"]),
        sa.UniqueConstraint("task_id", name="uq_order_task_id"),
    )
    op.create_index("ix_order_employer_id", "order", ["employer_id"])
    op.create_index("ix_order_taker_status", "order", ["taker_id", "status"])

    # ---- wallet ----
    op.create_table(
        "wallet",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("available", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("frozen", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("available >= 0", name="ck_wallet_available_nonneg"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.UniqueConstraint("user_id", name="uq_wallet_user_id"),
    )

    # ---- order_event ----
    op.create_table(
        "order_event",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("from_status", sa.String(length=16), nullable=False),
        sa.Column("to_status", sa.String(length=16), nullable=False),
        sa.Column("operator_id", sa.Integer(), nullable=True),
        sa.Column("remark", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(["operator_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["order_id"], ["order.id"]),
    )
    op.create_index("ix_order_event_order_id", "order_event", ["order_id"])

    # ---- fund_flow ----
    op.create_table(
        "fund_flow",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=True),
        sa.Column("type", sa.String(length=16), nullable=False),
        sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("balance_after", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(["order_id"], ["order.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
    )
    op.create_index("ix_fund_flow_user_created", "fund_flow", ["user_id", "created_at"])

    # ---- chat_session ----
    op.create_table(
        "chat_session",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("taker_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["taker_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["task_id"], ["task.id"]),
        sa.UniqueConstraint("task_id", "taker_id", name="uq_chat_session_task_taker"),
    )

    # ---- message ----
    op.create_table(
        "message",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("sender_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(length=16), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("image_key", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["sender_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["session_id"], ["chat_session.id"]),
    )
    op.create_index("ix_message_session_id", "message", ["session_id"])

    # ---- review ----
    op.create_table(
        "review",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("from_user", sa.Integer(), nullable=False),
        sa.Column("to_user", sa.Integer(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["from_user"], ["user.id"]),
        sa.ForeignKeyConstraint(["order_id"], ["order.id"]),
        sa.ForeignKeyConstraint(["to_user"], ["user.id"]),
        sa.UniqueConstraint("order_id", "from_user", name="uq_review_order_from"),
    )

    # ---- report ----
    op.create_table(
        "report",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("reporter_id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["order_id"], ["order.id"]),
        sa.ForeignKeyConstraint(["reporter_id"], ["user.id"]),
    )
    op.create_index("ix_report_status", "report", ["status"])

    # ---- post ----
    op.create_table(
        "post",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("audit_status", sa.String(length=16), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["author_id"], ["user.id"]),
    )
    op.create_index("ix_post_audit_created", "post", ["audit_status", "created_at"])

    # ---- audit_log ----
    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("actor_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("target_type", sa.String(length=32), nullable=False),
        sa.Column("target_id", sa.Integer(), nullable=True),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(["actor_id"], ["user.id"]),
    )
    op.create_index("ix_audit_log_actor_created", "audit_log", ["actor_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_audit_log_actor_created", table_name="audit_log")
    op.drop_table("audit_log")
    op.drop_index("ix_post_audit_created", table_name="post")
    op.drop_table("post")
    op.drop_index("ix_report_status", table_name="report")
    op.drop_table("report")
    op.drop_table("review")
    op.drop_index("ix_message_session_id", table_name="message")
    op.drop_table("message")
    op.drop_table("chat_session")
    op.drop_index("ix_fund_flow_user_created", table_name="fund_flow")
    op.drop_table("fund_flow")
    op.drop_index("ix_order_event_order_id", table_name="order_event")
    op.drop_table("order_event")
    op.drop_table("wallet")
    op.drop_index("ix_order_taker_status", table_name="order")
    op.drop_index("ix_order_employer_id", table_name="order")
    op.drop_table("order")
    op.drop_index("ix_student_verify_status", table_name="student_verify")
    op.drop_table("student_verify")
    op.drop_index("ix_task_publisher_id", table_name="task")
    op.drop_index("ix_task_category_status_deadline", table_name="task")
    op.drop_table("task")
    op.drop_index("ix_user_banned", table_name="user")
    op.drop_table("user")
