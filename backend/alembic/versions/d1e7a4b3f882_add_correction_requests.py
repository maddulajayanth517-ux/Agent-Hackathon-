"""add student correction requests

Revision ID: d1e7a4b3f882
Revises: b2d6f0a1c9e4
"""
from alembic import op
import sqlalchemy as sa

revision = "d1e7a4b3f882"
down_revision = "b2d6f0a1c9e4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "correction_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("meeting_id", sa.Integer(), sa.ForeignKey("meeting_records.id", ondelete="SET NULL"), nullable=True),
        sa.Column("field_reference", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("OPEN", "REVIEWED", "RESOLVED", "DISMISSED", name="correctionstatus", native_enum=False),
            nullable=False,
        ),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_correction_requests_student_id", "correction_requests", ["student_id"])
    op.create_index("ix_correction_requests_meeting_id", "correction_requests", ["meeting_id"])
    op.create_index("ix_correction_requests_status", "correction_requests", ["status"])


def downgrade() -> None:
    op.drop_table("correction_requests")
