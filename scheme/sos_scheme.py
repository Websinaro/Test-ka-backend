from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict

class SafetyContactCreate(BaseModel):
	name: str
	relationship: Optional[str] = None
	phone: str
	email: Optional[EmailStr] = None
	address: Optional[str] = None

class SafetyContactOut(BaseModel):
	id: int
	name: str
	relationship: Optional[str] = None
	phone: str
	email: Optional[str] = None
	address: Optional[str] = None

	model_config = ConfigDict(from_attributes=True)

class SosCreate(BaseModel):
	latitude: float
	longitude: float
	message: Optional[str] = None

class SosLocationUpdate(BaseModel):
	latitude: float
	longitude: float

class SosOut(BaseModel):
	id: int
	user_id: int
	latitude: float
	longitude: float
	status: str
	message: Optional[str] = None
	created_time: str
	resolved_time: Optional[str] = None

	model_config = ConfigDict(from_attributes=True)

class DeviceTokenCreate(BaseModel):
	fcm_token: str
	platform: Optional[str] = None