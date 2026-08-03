def get_alert_level(weather_code: int, rain_probability: float, wind_speed: float) -> str:
	# DARK RED: very high risk — cyclonic / extreme
	if weather_code in (65, 67, 82, 96, 99) or rain_probability >= 90 or wind_speed >= 62:
		return "dark_red"

	# LIGHT RED: high risk
	if weather_code in (63, 66, 80, 81, 95) or rain_probability >= 70 or wind_speed >= 45:
		return "light_red"

	# ORANGE: risk
	if weather_code in (51, 53, 55, 56, 57, 61, 85, 86) or rain_probability >= 50 or wind_speed >= 30:
		return "orange"

	# YELLOW: low risk
	if rain_probability >= 20 or wind_speed >= 15 or weather_code in (2, 3, 45, 48):
		return "yellow"

	# GREEN: safe
	return "green"