from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class DistrictStat(BaseModel):
	district: str
	registered_users: int
	active_sos: int
	active_notifications: int


class ActiveSosSummary(BaseModel):
	id: int
	user_id: int
	user_name: str
	district: str
	latitude: float
	longitude: float
	message: Optional[str] = None
	created_time: str

	model_config = ConfigDict(from_attributes=True)


class PresidentDashboard(BaseModel):
	total_users: int
	total_active_sos: int
	total_active_notifications: int
	districts: List[DistrictStat]
	active_sos_alerts: List[ActiveSosSummary]
