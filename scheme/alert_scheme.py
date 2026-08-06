from typing import Optional
from pydantic import BaseModel, ConfigDict, field_validator

from data.kerala_districts import KERALA_DISTRICTS

class OfficialAlertCreate(BaseModel):
	title: str
	message: str
	severity: str = "orange"
	district: Optional[str] = None  # None = state-wide
	expires_in_hours: Optional[int] = 24

	@field_validator("district")
	@classmethod
	def district_must_be_known(cls, v: Optional[str]) -> Optional[str]:
		if v is None:
			return v
		normalized = v.strip().lower()
		if normalized not in KERALA_DISTRICTS:
			raise ValueError(f"'{v}' is not a recognized Kerala district")
		return normalized

class OfficialAlertOut(BaseModel):
	id: int
	title: str
	message: str
	severity: str
	district: Optional[str] = None
	created_time: str
	expires_time: Optional[str] = None

	model_config = ConfigDict(from_attributes=True)