"""add operational escalation queues

Revision ID: a7c1e9f4d660
Revises: f5b8e4d7c330
"""
from alembic import op
import sqlalchemy as sa

revision = "a7c1e9f4d660"
down_revision = "f5b8e4d7c330"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table("service_queues", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("code", sa.String(50), nullable=False, unique=True), sa.Column("name", sa.String(150), nullable=False), sa.Column("recipient_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")), sa.Column("recipient_email", sa.String(255)), sa.Column("is_active", sa.Boolean(), nullable=False))
    op.add_column("escalations", sa.Column("destination", sa.String(150), nullable=False, server_default="Mentor"))
    op.add_column("escalations", sa.Column("queue_id", sa.Integer(), sa.ForeignKey("service_queues.id", ondelete="SET NULL")))

def downgrade() -> None:
    op.drop_column("escalations", "queue_id")
    op.drop_column("escalations", "destination")
    op.drop_table("service_queues")
