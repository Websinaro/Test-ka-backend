from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from utils.password import passwordValidator

from database.database import get_db
from model import model
from scheme import scheme
from security.hashing import hashPass, verifyPass
from security.jwt import create_access_token
from security.oauth2 import get_current_user

router = APIRouter()

@router.post("/register", response_model=scheme.UserOut)
def register(user: scheme.UserCreate, db: Session = Depends(get_db)):
	existing = db.query(model.User).filter(model.User.email == user.email).first()
	if existing:
		raise HTTPException(status_code=400, detail="Email Already Registered")

	validation_result = passwordValidator(user.password)
	if validation_result != "Strong Password":
		raise HTTPException(status_code=400, detail=validation_result)

	new_user = model.User(
		name=user.name,
		email=user.email,
		phone=user.phone,
		password=hashPass(user.password),
		district=user.district,
		role="user",
		created_time=str(datetime.utcnow())
	)

	db.add(new_user)
	db.commit()
	db.refresh(new_user)
	return new_user

@router.post("/login", response_model=scheme.Token)
def login(form_data: scheme.LoginForm = Depends(), db: Session = Depends(get_db)):
	user = db.query(model.User).filter(model.User.email == form_data.username).first()

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
