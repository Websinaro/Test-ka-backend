from typing import Optional
from pydantic import BaseModel, ConfigDict

class OfficialAlertCreate(BaseModel):
	title: str
	message: str
	severity: str = "orange"
	district: Optional[str] = None  # None = state-wide
	expires_in_hours: Optional[int] = 24

class OfficialAlertOut(BaseModel):
	id: int
	title: str
	message: str
	severity: str
	district: Optional[str] = None
	created_time: str
	expires_time: Optional[str] = None

	model_config = ConfigDict(from_attributes=True)