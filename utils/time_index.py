from datetime import datetime
from zoneinfo import ZoneInfo

def get_current_hour_index(hourly_times: list) -> int:
	now_key = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%dT%H:00")
	try:
		return hourly_times.index(now_key)
	except ValueError:
		return 0
