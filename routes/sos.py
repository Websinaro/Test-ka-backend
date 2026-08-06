from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_

from database.database import get_db
from model import model
from scheme import sos_scheme
from security.oauth2 import get_current_user
from services.push_service import send_sos_push

router = APIRouter()

def _find_protector_users(db: Session, contacts: list):
	"""Matches each safety contact to a registered WeBAlert account by
	phone or email, if one exists. A contact who hasn't installed the app
	simply won't receive a push - there's no SMS fallback wired up yet."""
	matched = []
	for contact in contacts:
		user = db.query(model.User).filter(
			or_(model.User.phone == contact.phone, model.User.email == contact.email)
		).first()
		if user:
			matched.append(user)
	return matched

@router.post("/sos", response_model=sos_scheme.SosOut)
def create_sos(
	payload: sos_scheme.SosCreate,
	db: Session = Depends(get_db),
	current_user: model.User = Depends(get_current_user),
):
	existing_active = db.query(model.SosAlert).filter(
		model.SosAlert.user_id == current_user.id,
		model.SosAlert.status == "active",
	).first()
	if existing_active:
		raise HTTPException(status_code=400, detail="You already have an active SOS alert.")

	alert = model.SosAlert(
		user_id=current_user.id,
		latitude=payload.latitude,
		longitude=payload.longitude,
		message=payload.message,
		status="active",
		created_time=str(datetime.utcnow()),
	)
	db.add(alert)
	db.commit()
	db.refresh(alert)

	contacts = db.query(model.SafetyContact).filter(model.SafetyContact.user_id == current_user.id).all()
	protectors = _find_protector_users(db, contacts)

	for protector in protectors:
		tokens = db.query(model.DeviceToken).filter(model.DeviceToken.user_id == protector.id).all()
		for token_row in tokens:
			send_sos_push(
				fcm_token=token_row.fcm_token,
				sos_id=alert.id,
				sender_name=current_user.name,
				latitude=alert.latitude,
				longitude=alert.longitude,
			)

	return alert

@router.get("/sos/{sos_id}", response_model=sos_scheme.SosOut)
def get_sos(
	sos_id: int,
	db: Session = Depends(get_db),
	current_user: model.User = Depends(get_current_user),
):
	alert = db.query(model.SosAlert).filter(model.SosAlert.id == sos_id).first()
	if not alert:
		raise HTTPException(status_code=404, detail="SOS alert not found")

	if alert.user_id != current_user.id:
		contacts = db.query(model.SafetyContact).filter(model.SafetyContact.user_id == alert.user_id).all()
		protectors = _find_protector_users(db, contacts)
		if current_user.id not in [p.id for p in protectors]:
			raise HTTPException(status_code=403, detail="You are not authorized to view this alert")

	return alert

@router.patch("/sos/{sos_id}/location", response_model=sos_scheme.SosOut)
def update_sos_location(
	sos_id: int,
	payload: sos_scheme.SosLocationUpdate,
	db: Session = Depends(get_db),
	current_user: model.User = Depends(get_current_user),
):
	alert = db.query(model.SosAlert).filter(
		model.SosAlert.id == sos_id,
		model.SosAlert.user_id == current_user.id,
	).first()
	if not alert:
		raise HTTPException(status_code=404, detail="SOS alert not found")
	if alert.status != "active":
		raise HTTPException(status_code=400, detail="This SOS alert is no longer active")

	alert.latitude = payload.latitude
	alert.longitude = payload.longitude
	db.commit()
	db.refresh(alert)
	return alert

@router.post("/sos/{sos_id}/resolve", response_model=sos_scheme.SosOut)
def resolve_sos(
	sos_id: int,
	db: Session = Depends(get_db),
	current_user: model.User = Depends(get_current_user),
):
	alert = db.query(model.SosAlert).filter(
		model.SosAlert.id == sos_id,
		model.SosAlert.user_id == current_user.id,
	).first()
	if not alert:
		raise HTTPException(status_code=404, detail="SOS alert not found")

	alert.status = "resolved"
	alert.resolved_time = str(datetime.utcnow())
	db.commit()
	db.refresh(alert)
	return alert

@router.get("/sos/active/incoming", response_model=list[sos_scheme.SosOut])
def list_incoming_active_sos(
	db: Session = Depends(get_db),
	current_user: model.User = Depends(get_current_user),
):
	"""All currently-active SOS alerts where the logged-in user is a
	registered protector for the sender. Lets the protector's app poll for
	incoming emergencies even before push notifications are wired up."""
	all_active = db.query(model.SosAlert).filter(model.SosAlert.status == "active").all()
	result = []
	for alert in all_active:
		contacts = db.query(model.SafetyContact).filter(model.SafetyContact.user_id == alert.user_id).all()
		protectors = _find_protector_users(db, contacts)
		if current_user.id in [p.id for p in protectors]:
			result.append(alert)
	return result

@router.get("/sos/mine/active", response_model=Optional[sos_scheme.SosOut])
def get_my_active_sos(
	db: Session = Depends(get_db),
	current_user: model.User = Depends(get_current_user),
):
	"""Lets the app check on launch whether the logged-in user already has
	an active SOS running (e.g. app was closed and reopened mid-emergency),
	so the SOS button can correctly show 'ACTIVE' instead of resetting."""
	alert = db.query(model.SosAlert).filter(
		model.SosAlert.user_id == current_user.id,
		model.SosAlert.status == "active",
	).first()
	return alert