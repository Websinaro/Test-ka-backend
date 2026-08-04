from datetime import datetime
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_

from database.database import get_db
from model import model
from scheme import sos_scheme
from security.oauth2 import get_current_user
from services.push_service import send_sos_push_batch
from typing import Optional

router = APIRouter()


def _protector_ids_query(db: Session, sender_user_id: int):
	"""Single JOIN query returning every registered user who protects
	`sender_user_id` (i.e. is listed as one of their safety contacts and has
	an account matching by phone or email).

	Replaces the old approach of looping over every safety contact and
	issuing a separate `SELECT ... FROM users WHERE phone = ? OR email = ?`
	per contact (an N+1 query pattern - slow, and gets worse the more
	emergency contacts a user has).
	"""
	return (
		db.query(model.User)
		.join(
			model.SafetyContact,
			or_(
				model.SafetyContact.phone == model.User.phone,
				model.SafetyContact.email == model.User.email,
			),
		)
		.filter(model.SafetyContact.user_id == sender_user_id)
		.distinct()
	)


def _find_protector_users(db: Session, sender_user_id: int) -> list:
	return _protector_ids_query(db, sender_user_id).all()


@router.post("/sos", response_model=sos_scheme.SosOut)
def create_sos(
	payload: sos_scheme.SosCreate,
	background_tasks: BackgroundTasks,
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

	# Push notifications are fanned out AFTER the response is returned to
	# the sender. Previously this loop of blocking FCM calls ran inline, so
	# the person hitting SOS had to wait for every protector's push to be
	# delivered (or time out) before their app even knew the alert was
	# saved. Now the alert is confirmed back to the sender in one fast
	# round trip, and delivery to protectors happens right after in the
	# background - it no longer adds to the sender's wait time.
	protector_ids = [p.id for p in _find_protector_users(db, current_user.id)]
	if protector_ids:
		tokens = [
			row.fcm_token
			for row in db.query(model.DeviceToken)
			.filter(model.DeviceToken.user_id.in_(protector_ids))
			.all()
		]
		if tokens:
			background_tasks.add_task(
				send_sos_push_batch,
				fcm_tokens=tokens,
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
		is_protector = (
			_protector_ids_query(db, alert.user_id)
			.filter(model.User.id == current_user.id)
			.first()
			is not None
		)
		if not is_protector:
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
	incoming emergencies even before push notifications are wired up.

	Rewritten as a single JOIN query. The previous version fetched every
	active alert in the system and then, for each one, ran a fresh query to
	look up that sender's safety contacts and match them to accounts -
	classic N+1 (O(active_alerts * contacts_per_alert) queries per poll).
	With protectors polling every few seconds during an active disaster,
	that alone could saturate the DB connection pool.
	"""
	alert_ids = (
		db.query(model.SosAlert.id)
		.join(
			model.SafetyContact,
			model.SafetyContact.user_id == model.SosAlert.user_id,
		)
		.join(
			model.User,
			or_(
				model.User.phone == model.SafetyContact.phone,
				model.User.email == model.SafetyContact.email,
			),
		)
		.filter(
			model.SosAlert.status == "active",
			model.User.id == current_user.id,
		)
		.distinct()
		.all()
	)
	ids = [row[0] for row in alert_ids]
	if not ids:
		return []

	return (
		db.query(model.SosAlert)
		.filter(model.SosAlert.id.in_(ids))
		.all()
	)


@router.get("/sos/mine/active", response_model=Optional[sos_scheme.SosOut])
def get_my_active_sos(
	db: Session = Depends(get_db),
	current_user: model.User = Depends(get_current_user),
):
	alert = db.query(model.SosAlert).filter(
		model.SosAlert.user_id == current_user.id,
		model.SosAlert.status == "active",
	).first()
	return alert
