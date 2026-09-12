"""add persistent mentoring alerts

Revision ID: 8d4f2a1c9b77
Revises: 1a5544ce8e39
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "8d4f2a1c9b77"
down_revision: Union[str, Sequence[str], None] = "1a5544ce8e39"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("recipient_id", sa.Integer(), nullable=False),
        sa.Column("flag_id", sa.Integer(), nullable=True),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("channel", sa.String(length=20), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actioned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recipient_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["flag_id"], ["flags.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_alerts_student_id", "alerts", ["student_id"])
    op.create_index("ix_alerts_recipient_id", "alerts", ["recipient_id"])
    op.create_index("ix_alerts_flag_id", "alerts", ["flag_id"])
    op.create_index("ix_alerts_severity", "alerts", ["severity"])
    op.create_index("ix_alerts_created_at", "alerts", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_alerts_created_at", table_name="alerts")
    op.drop_index("ix_alerts_severity", table_name="alerts")
    op.drop_index("ix_alerts_flag_id", table_name="alerts")
    op.drop_index("ix_alerts_recipient_id", table_name="alerts")
    op.drop_index("ix_alerts_student_id", table_name="alerts")
    op.drop_table("alerts")
