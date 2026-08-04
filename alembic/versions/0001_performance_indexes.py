"""add performance indexes for fast SOS + auth lookups

Revision ID: 0001_performance_indexes
Revises:
Create Date: 2026-08-04

These indexes target the exact query patterns that were causing slow SOS
sends and slow protector polling:
  - users.phone / users.email: looked up per safety-contact when matching
    protectors (previously a full table scan every time).
  - safety_contacts.user_id / phone / email: joined/filtered on every SOS
    create and every incoming-alert poll.
  - sos_alerts(user_id, status) and sos_alerts(status): the two hottest
    filters in routes/sos.py ("my active alert" and "all active alerts").
  - device_tokens.user_id: looked up per protector to fan out push
    notifications.

Uses IF NOT EXISTS / checks so it's safe to run against a DB that already
has some of these (e.g. one created fresh via Base.metadata.create_all,
which will already have picked up the index=True columns).
"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "0001_performance_indexes"
down_revision = None
branch_labels = None
depends_on = None


INDEXES = [
	("ix_users_phone", "users", ["phone"]),
	("ix_users_email", "users", ["email"]),
	("ix_safety_contacts_user_id", "safety_contacts", ["user_id"]),
	("ix_safety_contacts_phone", "safety_contacts", ["phone"]),
	("ix_safety_contacts_email", "safety_contacts", ["email"]),
	("ix_sos_alerts_user_id", "sos_alerts", ["user_id"]),
	("ix_sos_alerts_status", "sos_alerts", ["status"]),
	("ix_sos_alerts_user_status", "sos_alerts", ["user_id", "status"]),
	("ix_device_tokens_user_id", "device_tokens", ["user_id"]),
]


def upgrade() -> None:
	bind = op.get_bind()
	inspector = __import__("sqlalchemy").inspect(bind)

	for index_name, table_name, columns in INDEXES:
		if table_name not in inspector.get_table_names():
			continue
		existing = {ix["name"] for ix in inspector.get_indexes(table_name)}
		if index_name in existing:
			continue
		op.create_index(index_name, table_name, columns)


def downgrade() -> None:
	bind = op.get_bind()
	inspector = __import__("sqlalchemy").inspect(bind)

	for index_name, table_name, _columns in INDEXES:
		if table_name not in inspector.get_table_names():
			continue
		existing = {ix["name"] for ix in inspector.get_indexes(table_name)}
		if index_name in existing:
			op.drop_index(index_name, table_name=table_name)
