from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from utils.password import passwordValidator
from utils.timestamps import utc_now_str

from database.database import get_db
from model import model
from scheme import scheme
from security.hashing import hashPass, verifyPass
from security.jwt import create_access_token
from security.oauth2 import get_current_user
from config.config import PRESIDENT_ACCESS_CODE
from utils.normalize import normalize_phone, normalize_email

router = APIRouter()

@router.post("/register", response_model=scheme.UserOut)
def register(user: scheme.UserCreate, db: Session = Depends(get_db)):
	normalized_email = normalize_email(user.email)
	try:
		normalized_phone = normalize_phone(user.phone)
	except ValueError as e:
		raise HTTPException(status_code=400, detail=str(e))

	existing = db.query(model.User).filter(model.User.email == normalized_email).first()
	if existing:
		raise HTTPException(status_code=400, detail="Email Already Registered")

	validation_result = passwordValidator(user.password)
	if validation_result != "Strong Password":
		raise HTTPException(status_code=400, detail=validation_result)

	role = "user"
	if user.access_code:
		if not PRESIDENT_ACCESS_CODE or user.access_code != PRESIDENT_ACCESS_CODE:
			raise HTTPException(status_code=400, detail="Invalid access code")
		role = "president"

	new_user = model.User(
		name=user.name,
		email=normalized_email,
		phone=normalized_phone,
		password=hashPass(user.password),
		district=user.district,
		role=role,
		created_time=utc_now_str()
	)

	db.add(new_user)
	db.commit()
	db.refresh(new_user)
	return new_user
	
@router.post("/login", response_model=scheme.Token)
def login(form_data: scheme.LoginForm = Depends(), db: Session = Depends(get_db)):
	user = db.query(model.User).filter(model.User.email == normalize_email(form_data.username)).first()

	if not user or not verifyPass(form_data.password, user.password):
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Incorrect email or password or User not found",
			headers={"WWW-Authenticate": "Bearer"},
		)

	access_token = create_access_token(data={"sub": user.email})
	return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=scheme.UserOut)
def get_me(current_user: model.User = Depends(get_current_user)):
	return current_user
