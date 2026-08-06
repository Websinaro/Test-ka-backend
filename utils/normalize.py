import re

def normalize_phone(phone: str) -> str:
	"""Collapses any way a 10-digit Indian mobile number might be typed
	(with spaces, dashes, a leading 0, a leading 91, or a +91) down to a
	single canonical '+91XXXXXXXXXX' form, so a plain 10-digit number
	entered as a safety contact always matches the same number entered
	(possibly differently) at registration.

	Raises ValueError if it doesn't look like a valid Indian mobile
	number once the formatting noise is stripped, so bad input fails
	loudly at the API boundary instead of silently never matching later.
	"""
	digits = re.sub(r"[^\d]", "", phone or "")

	if digits.startswith("0") and len(digits) == 11:
		digits = digits[1:]
	elif digits.startswith("91") and len(digits) == 12:
		digits = digits[2:]

	if len(digits) != 10 or digits[0] not in "6789":
		raise ValueError("Enter a valid 10-digit mobile number")

	return f"+91{digits}"

def normalize_email(email: str) -> str:
	"""Emails are case-insensitive for matching purposes (RFC allows
	case-sensitive local parts in theory, but no real provider enforces
	that) - lowercase consistently wherever one is stored."""
	return (email or "").strip().lower()
