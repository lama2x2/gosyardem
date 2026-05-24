"""Add photo_file_id to requests

Revision ID: 002
Revises: 001
Create Date: 2026-05-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("requests", sa.Column("photo_file_id", sa.String(512), nullable=True))


def downgrade() -> None:
    op.drop_column("requests", "photo_file_id")
