"""add point-in-time institutional snapshots to meeting records

Revision ID: b2d6f0a1c9e4
Revises: a7c1e9f4d660
"""
from alembic import op
import sqlalchemy as sa

revision = "b2d6f0a1c9e4"
down_revision = "a7c1e9f4d660"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("meeting_records", sa.Column("attendance_pct_snapshot", sa.Numeric(5, 2), nullable=True))
    op.add_column("meeting_records", sa.Column("cgpa_snapshot", sa.Numeric(4, 2), nullable=True))
    op.add_column("meeting_records", sa.Column("backlog_count_snapshot", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("meeting_records", "backlog_count_snapshot")
    op.drop_column("meeting_records", "cgpa_snapshot")
    op.drop_column("meeting_records", "attendance_pct_snapshot")
