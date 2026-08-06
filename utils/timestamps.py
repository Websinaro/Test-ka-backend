from datetime import datetime

def utc_now_str() -> str:
	"""str(datetime.utcnow()) and datetime.utcnow().isoformat() both drop
	the microseconds field whenever it's exactly zero, which makes
	every timestamp column in this app (all stored as plain strings) an
	inconsistent width. That silently breaks '>' comparisons and
	.desc() sorting right at that boundary - not always, just
	sometimes, which is exactly why it's easy to miss in testing.
	Always emitting all 6 microsecond digits keeps every timestamp the
	same length so string ordering matches chronological ordering.
	"""
	return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")
