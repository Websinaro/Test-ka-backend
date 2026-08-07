from typing import Optional
from pydantic import BaseModel, ConfigDict, field_validator

ALLOWED_SEVERITIES = {"green", "yellow", "orange", "light_red", "dark_red"}


class NotificationCreate(BaseModel):
	title: str
	message: str
	severity: str = "orange"
	district: Optional[str] = None  # None / omitted = broadcast to all Kerala

	@field_validator("severity")
	@classmethod
	def validate_severity(cls, v: str) -> str:
		if v not in ALLOWED_SEVERITIES:
			raise ValueError(f"severity must be one of {sorted(ALLOWED_SEVERITIES)}")
		return v

	@field_validator("title")
	@classmethod
	def validate_title(cls, v: str) -> str:
		if not v or not v.strip():
			raise ValueError("title is required")
		return v.strip()

	@field_validator("message")
	@classmethod
	def validate_message(cls, v: str) -> str:
		if not v or not v.strip():
			raise ValueError("message is required")
		return v.strip()


class NotificationUpdate(BaseModel):
	title: Optional[str] = None
	message: Optional[str] = None
	severity: Optional[str] = None
	district: Optional[str] = None
	clear_district: bool = False  # explicit flag so "target all Kerala" can be set on update
	active: Optional[bool] = None

	@field_validator("severity")
	@classmethod
	def validate_severity(cls, v: Optional[str]) -> Optional[str]:
		if v is not None and v not in ALLOWED_SEVERITIES:
			raise ValueError(f"severity must be one of {sorted(ALLOWED_SEVERITIES)}")
		return v


class NotificationOut(BaseModel):
	id: int
	title: str
	message: str
	severity: str
	district: Optional[str] = None
	created_by: int
	created_by_name: str
	active: bool
	created_time: str
	updated_time: str

	model_config = ConfigDict(from_attributes=True)
