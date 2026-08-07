from fastapi import Form
from typing import Annotated, Optional
from pydantic import BaseModel, EmailStr, ConfigDict

class UserCreate(BaseModel):
	name: str
	email: EmailStr
	phone: str
	password: str
	district: str
	access_code: Optional[str] = None  # required to register as "president"

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
