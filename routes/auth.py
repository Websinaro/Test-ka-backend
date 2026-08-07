from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from utils.password import passwordValidator

from config.config import PRESIDENT_ACCESS_CODE
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

	# A signup only becomes "president" (admin) if it supplies the correct
	# official access code. A wrong/missing code when the toggle was on is
	# rejected outright rather than silently falling back to a normal user,
	# so nobody quietly ends up thinking they registered as an admin.
	role = "user"
	if user.access_code is not None and user.access_code.strip() != "":
		if user.access_code.strip() != PRESIDENT_ACCESS_CODE:
			raise HTTPException(status_code=400, detail="Invalid president access code")
		role = "president"

	new_user = model.User(
		name=user.name,
		email=user.email,
		phone=user.phone,
		password=hashPass(user.password),
		district=user.district,
		role=role,
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
