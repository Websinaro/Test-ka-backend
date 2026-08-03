from fastapi import Form
from typing import Annotated
from pydantic import BaseModel, EmailStr, ConfigDict

class UserCreate(BaseModel):
	name: str
	email: EmailStr
	phone: str
	password: str
	district: str

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
