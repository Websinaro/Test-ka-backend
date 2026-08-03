import asyncio
from fastapi import APIRouter
from services.weather_service import fetch_current_only
from data.kerala_districts import KERALA_DISTRICTS
from data.weather_codes import get_weather_info
from data.severity import get_alert_level
from utils.time_index import get_current_hour_index

router = APIRouter()

_semaphore = asyncio.Semaphore(5)  # max 5 in-flight requests at once

async def _district_weather(name: str, coords: dict):
	async with _semaphore:
		for attempt in range(2):  # one retry on transient failure
			try:
				data = await fetch_current_only(coords["lat"], coords["lon"])
				break
			except Exception:
				if attempt == 1:
					return None
				await asyncio.sleep(1)

	current = data["current"]
	hour_index = get_current_hour_index(data["hourly"]["time"])
	rain_prob = data["hourly"]["precipitation_probability"][hour_index] or 0

	alert_level = get_alert_level(
		weather_code=current["weather_code"],
		rain_probability=rain_prob,
		wind_speed=current["wind_speed_10m"],
	)

	return {
		"district": name,
		"latitude": coords["lat"],
		"longitude": coords["lon"],
		"temperature": current["temperature_2m"],
		"humidity": current["relative_humidity_2m"],
		"rain_probability": rain_prob,
		"weather_code": current["weather_code"],
		"weather_label": get_weather_info(current["weather_code"])["label"],
		"wind_speed": current["wind_speed_10m"],
		"wind_direction": current["wind_direction_10m"],
		"wind_gusts": current["wind_gusts_10m"],
		"alert_level": alert_level,
	}

@router.get("/weather/kerala-map")
async def get_kerala_map():
	tasks = [_district_weather(name, coords) for name, coords in KERALA_DISTRICTS.items()]
	results = await asyncio.gather(*tasks)
	districts = [r for r in results if r is not None]

	return {"districts": districts, "total": len(KERALA_DISTRICTS), "loaded": len(districts)}
