from fastapi import Form
from typing import Annotated,Optional
from pydantic import BaseModel, EmailStr, ConfigDict, field_validator

from data.kerala_districts import KERALA_DISTRICTS

class UserCreate(BaseModel):
	name: str
	email: EmailStr
	phone: str
	password: str
	district: str
	access_code: Optional[str] = None

	@field_validator("district")
	@classmethod
	def district_must_be_known(cls, v: str) -> str:
		normalized = v.strip().lower()
		if normalized not in KERALA_DISTRICTS:
			raise ValueError(f"'{v}' is not a recognized Kerala district")
		return normalized

class UserOut(BaseModel):
	id: int
	name: str
	email: EmailStr
	district: str
	role: str

	model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
	access_token: str
	token_type: str

class LoginForm:
	def __init__(
		self,
		email: Annotated[str, Form()],
		password: Annotated[str, Form()],
	):
		self.username = email
		self.password = password
