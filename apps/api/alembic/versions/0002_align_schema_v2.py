"""对齐设计 V2.0：补字段、改约束、改类型

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-23

依据《数据库设计说明书 V2.0》附录 B 表 B-2「代码待补字段与枚举清单」。
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ---- user ----
    op.add_column(
        "user", sa.Column("account", sa.String(length=64), nullable=False, server_default="")
    )
    op.add_column(
        "user", sa.Column("nickname", sa.String(length=40), nullable=False, server_default="")
    )
    op.add_column("user", sa.Column("ban_reason", sa.String(length=200), nullable=True))
    op.execute(
        "UPDATE \"user\" SET account = COALESCE(student_no, 'user_' || id) WHERE account = ''"
    )
    op.execute("UPDATE \"user\" SET nickname = COALESCE(name, account) WHERE nickname = ''")
    op.create_unique_constraint("uq_user_account", "user", ["account"])
    op.alter_column("user", "student_no", nullable=True)
    op.alter_column("user", "name", nullable=True)

    # ---- student_verify ----
    op.add_column(
        "student_verify",
        sa.Column("submit_count", sa.SmallInteger(), nullable=False, server_default="1"),
    )
    op.create_check_constraint(
        "ck_sv_submit_count", "student_verify", "submit_count >= 1 AND submit_count <= 3"
    )

    # ---- task ----
    op.add_column("task", sa.Column("place", sa.String(length=80), nullable=False, server_default=""))
    op.add_column(
        "task", sa.Column("apply_count", sa.SmallInteger(), nullable=False, server_default="0")
    )
    op.add_column(
        "task", sa.Column("ai_draft", sa.Boolean(), nullable=False, server_default=sa.text("false"))
    )

    # ---- order ----
    op.add_column("order", sa.Column("apply_note", sa.String(length=200), nullable=True))
    op.add_column("order", sa.Column("idem_key", sa.String(length=40), nullable=True))
    op.alter_column("order", "reward", nullable=True)
    op.drop_constraint("uq_order_task_id", "order", type_="unique")
    op.create_index(
        "uq_order_task_traded",
        "order",
        ["task_id"],
        unique=True,
        postgresql_where=sa.text("status != 'OPEN'"),
    )

    # ---- wallet ----
    op.add_column(
        "wallet", sa.Column("total_income", sa.Numeric(10, 2), nullable=False, server_default="0")
    )
    op.add_column("wallet", sa.Column("version", sa.Integer(), nullable=False, server_default="0"))
    op.create_check_constraint("ck_wallet_income_nonneg", "wallet", "total_income >= 0")

    # ---- fund_flow ----
    op.add_column("fund_flow", sa.Column("remark", sa.String(length=200), nullable=True))

    # ---- chat_session ----
    op.add_column("chat_session", sa.Column("employer_id", sa.Integer(), nullable=False))
    op.add_column(
        "chat_session", sa.Column("last_msg_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "chat_session",
        sa.Column("unread_employer", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "chat_session", sa.Column("unread_taker", sa.Integer(), nullable=False, server_default="0")
    )
    op.create_foreign_key(
        "fk_chat_session_employer", "chat_session", "user", ["employer_id"], ["id"]
    )

    # ---- message ----
    op.add_column(
        "message", sa.Column("read_flag", sa.Boolean(), nullable=False, server_default=sa.text("false"))
    )

    # ---- review ----
    op.add_column(
        "review", sa.Column("is_late", sa.Boolean(), nullable=False, server_default=sa.text("false"))
    )

    # ---- report ----
    op.add_column(
        "report", sa.Column("detail", sa.String(length=600), nullable=False, server_default="")
    )
    op.execute("UPDATE report SET detail = reason WHERE detail = ''")
    op.drop_column("report", "reason")
    op.add_column(
        "report", sa.Column("target_type", sa.String(length=12), nullable=False, server_default="TASK")
    )
    op.add_column(
        "report", sa.Column("target_id", sa.Integer(), nullable=False, server_default="0")
    )
    op.add_column(
        "report", sa.Column("type", sa.String(length=16), nullable=False, server_default="OTHER")
    )
    op.add_column("report", sa.Column("evidence_key", sa.String(length=256), nullable=True))
    op.add_column("report", sa.Column("decision", sa.String(length=12), nullable=True))
    op.add_column("report", sa.Column("handled_by", sa.Integer(), nullable=True))
    op.add_column("report", sa.Column("handled_at", sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key("fk_report_handler", "report", "user", ["handled_by"], ["id"])

    # ---- post ----
    op.add_column("post", sa.Column("images", postgresql.ARRAY(sa.String(length=256)), nullable=True))
    op.add_column("post", sa.Column("reject_reason", sa.String(length=200), nullable=True))

    # ---- audit_log ----
    op.alter_column(
        "audit_log",
        "detail",
        type_=postgresql.JSONB(),
        existing_type=sa.Text(),
        postgresql_using="CASE WHEN detail IS NULL THEN NULL ELSE to_jsonb(detail) END",
    )
    op.add_column("audit_log", sa.Column("ip", postgresql.INET(), nullable=True))


def downgrade() -> None:
    # ---- audit_log ----
    op.drop_column("audit_log", "ip")
    op.alter_column(
        "audit_log",
        "detail",
        type_=sa.Text(),
        existing_type=postgresql.JSONB(),
        postgresql_using="detail::text",
    )

    # ---- post ----
    op.drop_column("post", "reject_reason")
    op.drop_column("post", "images")

    # ---- report ----
    op.drop_constraint("fk_report_handler", "report", type_="foreignkey")
    op.drop_column("report", "handled_at")
    op.drop_column("report", "handled_by")
    op.drop_column("report", "decision")
    op.drop_column("report", "evidence_key")
    op.drop_column("report", "type")
    op.drop_column("report", "target_id")
    op.drop_column("report", "target_type")
    op.add_column("report", sa.Column("reason", sa.Text(), nullable=False, server_default=""))
    op.execute("UPDATE report SET reason = detail WHERE reason = ''")
    op.drop_column("report", "detail")

    # ---- review ----
    op.drop_column("review", "is_late")

    # ---- message ----
    op.drop_column("message", "read_flag")

    # ---- chat_session ----
    op.drop_constraint("fk_chat_session_employer", "chat_session", type_="foreignkey")
    op.drop_column("chat_session", "unread_taker")
    op.drop_column("chat_session", "unread_employer")
    op.drop_column("chat_session", "last_msg_at")
    op.drop_column("chat_session", "employer_id")

    # ---- fund_flow ----
    op.drop_column("fund_flow", "remark")

    # ---- wallet ----
    op.drop_constraint("ck_wallet_income_nonneg", "wallet", type_="check")
    op.drop_column("wallet", "version")
    op.drop_column("wallet", "total_income")

    # ---- order ----
    op.drop_index("uq_order_task_traded", table_name="order")
    op.create_unique_constraint("uq_order_task_id", "order", ["task_id"])
    op.execute("UPDATE \"order\" SET reward = 0 WHERE reward IS NULL")
    op.alter_column("order", "reward", nullable=False)
    op.drop_column("order", "idem_key")
    op.drop_column("order", "apply_note")

    # ---- task ----
    op.drop_column("task", "ai_draft")
    op.drop_column("task", "apply_count")
    op.drop_column("task", "place")

    # ---- student_verify ----
    op.drop_constraint("ck_sv_submit_count", "student_verify", type_="check")
    op.drop_column("student_verify", "submit_count")

    # ---- user ----
    op.alter_column("user", "name", nullable=False)
    op.alter_column("user", "student_no", nullable=False)
    op.drop_constraint("uq_user_account", "user", type_="unique")
    op.drop_column("user", "ban_reason")
    op.drop_column("user", "nickname")
    op.drop_column("user", "account")
