from fastapi import APIRouter, Query
from services.weather_service import fetch_weather
from scheme.weather_scheme import WeatherResponse
from data.weather_codes import get_weather_info
from data.severity import get_alert_level
from utils.time_index import get_current_hour_index

router = APIRouter()

@router.get("/weather", response_model=WeatherResponse)
async def get_weather(
	lat: float = Query(..., ge=-90, le=90),
	lon: float = Query(..., ge=-180, le=180)
):
	result = await fetch_weather(lat, lon)
	data = result["weather"]
	air = result["air"]

	response = {
		"location_name": result["place_name"],
		"latitude": lat,
		"longitude": lon,
		"current": {
			"temperature": data["current"]["temperature_2m"],
			"feels_like": data["current"]["apparent_temperature"],
			"humidity": data["current"]["relative_humidity_2m"],
			"precipitation": data["current"]["precipitation"],
			"rain": data["current"]["rain"],
			"weather_code": data["current"]["weather_code"],
			"cloud_cover": data["current"]["cloud_cover"],
			"pressure": data["current"]["pressure_msl"],
			"wind_speed": data["current"]["wind_speed_10m"],
			"wind_direction": data["current"]["wind_direction_10m"],
			"wind_gusts": data["current"]["wind_gusts_10m"],
			"uv_index": data["current"].get("uv_index"),
			"is_day": data["current"]["is_day"],
		},
		"air_quality": None,
		"hourly": {
			"time": data["hourly"]["time"],
			"temperature": data["hourly"]["temperature_2m"],
			"feels_like": data["hourly"]["apparent_temperature"],
			"humidity": data["hourly"]["relative_humidity_2m"],
			"rain_probability": data["hourly"]["precipitation_probability"],
			"precipitation": data["hourly"]["precipitation"],
			"wind_speed": data["hourly"]["wind_speed_10m"],
			"wind_gusts": data["hourly"]["wind_gusts_10m"],
			"uv_index": data["hourly"]["uv_index"],
			"dew_point": data["hourly"]["dew_point_2m"],
			"visibility": data["hourly"]["visibility"],
			"weather_code": data["hourly"]["weather_code"],
		},
		"daily": {
			"date": data["daily"]["time"],
			"temp_max": data["daily"]["temperature_2m_max"],
			"temp_min": data["daily"]["temperature_2m_min"],
			"feels_like_max": data["daily"]["apparent_temperature_max"],
			"feels_like_min": data["daily"]["apparent_temperature_min"],
			"sunrise": data["daily"]["sunrise"],
			"sunset": data["daily"]["sunset"],
			"uv_index_max": data["daily"]["uv_index_max"],
			"rain_probability_max": data["daily"]["precipitation_probability_max"],
			"precipitation_sum": data["daily"]["precipitation_sum"],
			"wind_speed_max": data["daily"]["wind_speed_10m_max"],
			"wind_gusts_max": data["daily"]["wind_gusts_10m_max"],
			"weather_code": data["daily"]["weather_code"],
		}
	}

	if air:
		response["air_quality"] = {
			"aqi": air["current"].get("us_aqi"),
			"pm2_5": air["current"].get("pm2_5"),
			"pm10": air["current"].get("pm10"),
			"ozone": air["current"].get("ozone"),
			"carbon_monoxide": air["current"].get("carbon_monoxide"),
		}

	response["current"]["weather_label"] = get_weather_info(response["current"]["weather_code"])["label"]
	response["current"]["weather_icon"] = get_weather_info(response["current"]["weather_code"])["icon"]

	hour_index = get_current_hour_index(response["hourly"]["time"])
	response["alert_level"] = get_alert_level(
		weather_code=response["current"]["weather_code"],
		rain_probability=response["hourly"]["rain_probability"][hour_index] or 0,
		wind_speed=response["current"]["wind_speed"]
	)

	return response
	return response
