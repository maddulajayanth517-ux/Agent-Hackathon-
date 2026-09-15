"""add messages and announcements

Revision ID: e8c2f5a71b04
Revises: d1e7a4b3f882
"""
from alembic import op
import sqlalchemy as sa

revision = "e8c2f5a71b04"
down_revision = "d1e7a4b3f882"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sender_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_messages_student_id", "messages", ["student_id"])
    op.create_index("ix_messages_created_at", "messages", ["created_at"])
    op.create_index("ix_messages_student_created", "messages", ["student_id", "created_at"])

    op.create_table(
        "announcements",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("author_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column(
            "scope",
            sa.Enum("ALL", "MENTORS", "STUDENTS", "MY_MENTEES", name="announcementscope", native_enum=False),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_announcements_created_at", "announcements", ["created_at"])


def downgrade() -> None:
    op.drop_table("announcements")
    op.drop_table("messages")
