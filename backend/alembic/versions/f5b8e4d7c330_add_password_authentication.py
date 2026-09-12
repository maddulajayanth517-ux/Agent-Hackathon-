"""add password authentication

Revision ID: f5b8e4d7c330
Revises: e4a9d3c6b220
"""
from alembic import op
import sqlalchemy as sa

revision = "f5b8e4d7c330"
down_revision = "e4a9d3c6b220"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("password_hash", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "password_hash")
