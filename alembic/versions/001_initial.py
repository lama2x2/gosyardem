"""Initial schema

Revision ID: 001
Revises:
Create Date: 2025-01-01 00:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "request_types",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_request_types_slug"), "request_types", ["slug"], unique=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=True),
        sa.Column("username", sa.String(255), nullable=True),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("role", sa.Enum("citizen", "operator", "executor", "superuser", name="userrole"), nullable=False),
        sa.Column("source", sa.Enum("telegram", "api", name="usersource"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_telegram_id"), "users", ["telegram_id"], unique=True)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)

    op.create_table(
        "requests",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("type_id", sa.Integer(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("created", "in_progress", "proof_under_review", "completed", "rejected", name="requeststatus"),
            nullable=False,
        ),
        sa.Column("assigned_operator_id", sa.Integer(), nullable=True),
        sa.Column("assigned_executor_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("address", sa.String(512), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("citizen_confirmed", sa.Boolean(), nullable=True),
        sa.Column("citizen_review", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["assigned_executor_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["assigned_operator_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["type_id"], ["request_types.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_requests_user_id"), "requests", ["user_id"], unique=False)
    op.create_index(op.f("ix_requests_type_id"), "requests", ["type_id"], unique=False)
    op.create_index(op.f("ix_requests_assigned_operator_id"), "requests", ["assigned_operator_id"], unique=False)
    op.create_index(op.f("ix_requests_assigned_executor_id"), "requests", ["assigned_executor_id"], unique=False)

    op.create_table(
        "proofs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("request_id", sa.Integer(), nullable=False),
        sa.Column("executor_id", sa.Integer(), nullable=False),
        sa.Column("operator_id", sa.Integer(), nullable=True),
        sa.Column("file_ref", sa.String(512), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("pending", "approved", "rejected", name="proofstatus"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["executor_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["operator_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["request_id"], ["requests.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_proofs_request_id"), "proofs", ["request_id"], unique=False)
    op.create_index(op.f("ix_proofs_executor_id"), "proofs", ["executor_id"], unique=False)
    op.create_index(op.f("ix_proofs_operator_id"), "proofs", ["operator_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_proofs_operator_id"), table_name="proofs")
    op.drop_index(op.f("ix_proofs_executor_id"), table_name="proofs")
    op.drop_index(op.f("ix_proofs_request_id"), table_name="proofs")
    op.drop_table("proofs")
    op.drop_index(op.f("ix_requests_assigned_executor_id"), table_name="requests")
    op.drop_index(op.f("ix_requests_assigned_operator_id"), table_name="requests")
    op.drop_index(op.f("ix_requests_type_id"), table_name="requests")
    op.drop_index(op.f("ix_requests_user_id"), table_name="requests")
    op.drop_table("requests")
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_index(op.f("ix_users_telegram_id"), table_name="users")
    op.drop_table("users")
    op.drop_index(op.f("ix_request_types_slug"), table_name="request_types")
    op.drop_table("request_types")
    op.execute("DROP TYPE IF EXISTS proofstatus")
    op.execute("DROP TYPE IF EXISTS requeststatus")
    op.execute("DROP TYPE IF EXISTS usersource")
    op.execute("DROP TYPE IF EXISTS userrole")
