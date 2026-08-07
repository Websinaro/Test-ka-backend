"""add notifications table for president/admin broadcast alerts

Revision ID: 0002_notifications_table
Revises: 0001_performance_indexes
Create Date: 2026-08-07

Adds the `notifications` table backing the president's Notification
Center (create/read/update/delete broadcast alerts targeted at a single
district or all of Kerala), plus indexes on the two columns every list
query filters on: `district` (citizen inbox lookups) and `created_by`
(president's "my sent alerts" list).

Uses IF NOT EXISTS-style checks, matching 0001, so it's safe to run
against a DB that already has the table via Base.metadata.create_all.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0002_notifications_table"
down_revision = "0001_performance_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
	bind = op.get_bind()
	inspector = sa.inspect(bind)

	if "notifications" not in inspector.get_table_names():
		op.create_table(
			"notifications",
			sa.Column("id", sa.Integer, primary_key=True, index=True),
			sa.Column("title", sa.String(150), nullable=False),
			sa.Column("message", sa.String(1000), nullable=False),
			sa.Column("severity", sa.String(20), nullable=False, server_default="orange"),
			sa.Column("district", sa.String(50), nullable=True),
			sa.Column("created_by", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
			sa.Column("created_by_name", sa.String(100), nullable=False),
			sa.Column("active", sa.Boolean, nullable=False, server_default=sa.true()),
			sa.Column("created_time", sa.String(50), nullable=False),
			sa.Column("updated_time", sa.String(50), nullable=False),
		)

	inspector = sa.inspect(bind)
	existing_indexes = {ix["name"] for ix in inspector.get_indexes("notifications")}

	if "ix_notifications_district" not in existing_indexes:
		op.create_index("ix_notifications_district", "notifications", ["district"])
	if "ix_notifications_created_by" not in existing_indexes:
		op.create_index("ix_notifications_created_by", "notifications", ["created_by"])


def downgrade() -> None:
	bind = op.get_bind()
	inspector = sa.inspect(bind)
	if "notifications" in inspector.get_table_names():
		op.drop_table("notifications")
