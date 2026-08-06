import asyncio
import httpx

WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/reverse"

async def _get_with_retry(client: httpx.AsyncClient, url: str, params: dict, attempts: int = 2):
	"""The primary weather call is the one thing in this request that must
	not fail silently into a bare 500 - a single dropped packet or a brief
	Open-Meteo hiccup shouldn't surface as 'server hit an error' when a
	near-instant retry would have worked."""
	last_error = None
	for attempt in range(attempts):
		try:
			resp = await client.get(url, params=params)
			resp.raise_for_status()
			return resp
		except (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError) as e:
			last_error = e
			if attempt < attempts - 1:
				await asyncio.sleep(0.6)
	raise last_error

async def fetch_weather(lat: float, lon: float):
	weather_params = {
		"latitude": lat,
		"longitude": lon,
		"current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,rain,weather_code,cloud_cover,pressure_msl,wind_speed_10m,wind_direction_10m,wind_gusts_10m,uv_index,is_day",
		"hourly": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation_probability,precipitation,weather_code,wind_speed_10m,wind_gusts_10m,uv_index,dew_point_2m,visibility",
		"daily": "weather_code,temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min,sunrise,sunset,uv_index_max,precipitation_sum,precipitation_probability_max,wind_speed_10m_max,wind_gusts_10m_max",
		"timezone": "Asia/Kolkata",
		"forecast_days": 7,
	}

	air_params = {
		"latitude": lat,
		"longitude": lon,
		"current": "us_aqi,pm2_5,pm10,ozone,carbon_monoxide",
		"timezone": "Asia/Kolkata",
	}

	geocode_params = {
		"latitude": lat,
		"longitude": lon,
		"language": "en",
	}

	async with httpx.AsyncClient(timeout=15.0) as client:
		weather_resp = await _get_with_retry(client, WEATHER_URL, weather_params)

		place_name = None
		try:
			geo_resp = await client.get(GEOCODE_URL, params=geocode_params)
			geo_resp.raise_for_status()
			geo_data = geo_resp.json()
			if geo_data.get("results"):
				top = geo_data["results"][0]
				place_name = f"{top.get('name', '')}, {top.get('admin1', '')}"
		except Exception:
			place_name = None

		try:
			air_resp = await client.get(AIR_QUALITY_URL, params=air_params)
			air_resp.raise_for_status()
			air_data = air_resp.json()
		except Exception:
			air_data = None

		return {"weather": weather_resp.json(), "air": air_data, "place_name": place_name}

async def fetch_current_only(lat: float, lon: float):
	params = {
		"latitude": lat,
		"longitude": lon,
		"current": "temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m,wind_direction_10m,wind_gusts_10m",
		"hourly": "precipitation_probability",
		"timezone": "Asia/Kolkata",
		"forecast_days": 1,
	}
	async with httpx.AsyncClient(timeout=15.0) as client:
		resp = await _get_with_retry(client, WEATHER_URL, params)
		return resp.json()
