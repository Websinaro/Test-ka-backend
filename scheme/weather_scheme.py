from pydantic import BaseModel
from typing import List, Optional

class CurrentWeather(BaseModel):
	temperature: float
	feels_like: float
	humidity: float
	precipitation: float
	rain: float
	weather_code: int
	weather_label: Optional[str] = None
	weather_icon: Optional[str] = None
	cloud_cover: float
	pressure: float
	wind_speed: float
	wind_direction: float
	wind_gusts: float
	uv_index: Optional[float] = None
	is_day: int

class AirQuality(BaseModel):
	aqi: Optional[float] = None
	pm2_5: Optional[float] = None
	pm10: Optional[float] = None
	ozone: Optional[float] = None
	carbon_monoxide: Optional[float] = None

class HourlyForecast(BaseModel):
	time: List[str]
	temperature: List[float]
	feels_like: List[float]
	humidity: List[float]
	rain_probability: List[Optional[float]]
	precipitation: List[float]
	wind_speed: List[float]
	wind_gusts: List[float]
	uv_index: List[Optional[float]]
	dew_point: List[float]
	visibility: List[Optional[float]]
	weather_code: List[int]

class DailyForecast(BaseModel):
	date: List[str]
	temp_max: List[float]
	temp_min: List[float]
	feels_like_max: List[float]
	feels_like_min: List[float]
	sunrise: List[str]
	sunset: List[str]
	uv_index_max: List[Optional[float]]
	rain_probability_max: List[Optional[float]]
	precipitation_sum: List[float]
	wind_speed_max: List[float]
	wind_gusts_max: List[float]
	weather_code: List[int]

class WeatherResponse(BaseModel):
	location_name: Optional[str] = None
	latitude: float
	longitude: float
	alert_level: str
	current: CurrentWeather
	air_quality: Optional[AirQuality] = None
	hourly: HourlyForecast
	daily: DailyForecast
