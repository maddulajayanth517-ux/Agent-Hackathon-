"""complete mentoring workflow records

Revision ID: c3e891d2a110
Revises: 8d4f2a1c9b77
"""
from alembic import op
import sqlalchemy as sa

revision = "c3e891d2a110"
down_revision = "8d4f2a1c9b77"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("allocations", sa.Column("allocation_reason", sa.String(length=500), nullable=False, server_default="INITIAL"))
    op.add_column("allocations", sa.Column("reallocated_from_mentor_id", sa.Integer(), nullable=True))
    op.add_column("allocations", sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key("fk_allocations_reallocated_from_mentor", "allocations", "mentors", ["reallocated_from_mentor_id"], ["id"], ondelete="SET NULL")
    op.add_column("meeting_records", sa.Column("academic_progress", sa.Text(), nullable=True))
    op.add_column("meeting_records", sa.Column("attendance_review", sa.Text(), nullable=True))
    op.add_column("meeting_records", sa.Column("personal_circumstances", sa.Text(), nullable=True))
    op.add_column("meeting_records", sa.Column("career_direction", sa.Text(), nullable=True))
    op.add_column("meeting_records", sa.Column("recording_boundary_acknowledged", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_table(
        "scheduled_meetings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("mentor_id", sa.Integer(), sa.ForeignKey("mentors.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=False),
        sa.Column("mode", sa.Enum("IN_PERSON", "ONLINE", "PHONE", name="meetingmode", native_enum=False), nullable=False),
        sa.Column("agenda", sa.Text(), nullable=True),
        sa.Column("status", sa.Enum("SCHEDULED", "COMPLETED", "CANCELLED", "MISSED", name="scheduledmeetingstatus", native_enum=False), nullable=False),
        sa.Column("completed_meeting_id", sa.Integer(), sa.ForeignKey("meeting_records.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_scheduled_meetings_student_id", "scheduled_meetings", ["student_id"])
    op.create_index("ix_scheduled_meetings_mentor_id", "scheduled_meetings", ["mentor_id"])
    op.create_index("ix_scheduled_meetings_scheduled_for", "scheduled_meetings", ["scheduled_for"])
    op.create_index("ix_scheduled_meetings_status", "scheduled_meetings", ["status"])


def downgrade() -> None:
    op.drop_table("scheduled_meetings")
    op.drop_column("meeting_records", "recording_boundary_acknowledged")
    op.drop_column("meeting_records", "career_direction")
    op.drop_column("meeting_records", "personal_circumstances")
    op.drop_column("meeting_records", "attendance_review")
    op.drop_column("meeting_records", "academic_progress")
    op.drop_constraint("fk_allocations_reallocated_from_mentor", "allocations", type_="foreignkey")
    op.drop_column("allocations", "ended_at")
    op.drop_column("allocations", "reallocated_from_mentor_id")
    op.drop_column("allocations", "allocation_reason")
