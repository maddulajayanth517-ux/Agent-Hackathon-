"""add institutional mentoring policy

Revision ID: e4a9d3c6b220
Revises: c3e891d2a110
"""
from alembic import op
import sqlalchemy as sa

revision = "e4a9d3c6b220"
down_revision = "c3e891d2a110"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mentoring_policy",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("required_frequency_days", sa.Integer(), nullable=False),
        sa.Column("reminder_days_before", sa.Integer(), nullable=False),
        sa.Column("updated_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("mentoring_policy")
