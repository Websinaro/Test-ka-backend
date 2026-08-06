"""normalize existing phone/email values so protector matching works
for accounts and contacts created before normalization was added

Revision ID: 0002_normalize_phone_email
Revises: 0001_performance_indexes
Create Date: 2026-08-06

Every phone number entered before this migration may be stored in
whatever format the user typed (with/without +91, with spaces or
dashes, a leading 0, etc). Since SOS protector matching is an exact
string comparison between users.phone and safety_contacts.phone, two
representations of the same number never matched each other. This
backfills every existing row to the same '+91XXXXXXXXXX' canonical
form the app now writes going forward, and lowercases existing emails
for the same reason.

Rows that don't look like a valid 10-digit Indian mobile number after
stripping formatting are left untouched and printed, rather than
crashing the migration or guessing - a bad phone number should be
fixed by the user re-entering it, not silently mangled here.
"""
import re
from alembic import op
import sqlalchemy as sa


revision = "0002_normalize_phone_email"
down_revision = "0001_performance_indexes"
branch_labels = None
depends_on = None


def _normalize_phone(phone):
	if not phone:
		return None
	digits = re.sub(r"[^\d]", "", phone)
	if digits.startswith("0") and len(digits) == 11:
		digits = digits[1:]
	elif digits.startswith("91") and len(digits) == 12:
		digits = digits[2:]
	if len(digits) != 10 or digits[0] not in "6789":
		return None
	return f"+91{digits}"


def _backfill(table_name, has_email):
	bind = op.get_bind()
	inspector = sa.inspect(bind)
	if table_name not in inspector.get_table_names():
		return

	columns = "id, phone, email" if has_email else "id, phone"
	rows = bind.execute(sa.text(f"SELECT {columns} FROM {table_name}")).fetchall()

	for row in rows:
		updates = {}
		normalized_phone = _normalize_phone(row.phone)
		if normalized_phone and normalized_phone != row.phone:
			updates["phone"] = normalized_phone
		elif not normalized_phone:
			print(f"[0002_normalize_phone_email] {table_name}.id={row.id}: "
				  f"could not normalize phone '{row.phone}', left as-is - ask user to re-save it")

		if has_email and row.email:
			lowered = row.email.strip().lower()
			if lowered != row.email:
				updates["email"] = lowered

		if updates:
			set_clause = ", ".join(f"{col} = :{col}" for col in updates)
			updates["row_id"] = row.id
			bind.execute(sa.text(f"UPDATE {table_name} SET {set_clause} WHERE id = :row_id"), updates)


def _backfill_district(table_name):
	bind = op.get_bind()
	inspector = sa.inspect(bind)
	if table_name not in inspector.get_table_names():
		return

	rows = bind.execute(sa.text(f"SELECT id, district FROM {table_name}")).fetchall()
	for row in rows:
		if not row.district:
			continue
		normalized = row.district.strip().lower()
		if normalized != row.district:
			bind.execute(
				sa.text(f"UPDATE {table_name} SET district = :d WHERE id = :row_id"),
				{"d": normalized, "row_id": row.id},
			)


def upgrade() -> None:
	_backfill("users", has_email=True)
	_backfill("safety_contacts", has_email=True)
	_backfill_district("users")
	_backfill_district("official_alerts")


def downgrade() -> None:
	# Normalization isn't reversible (we don't know the original
	# formatting), so downgrade is a no-op.
	pass
