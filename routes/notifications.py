from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_

from database.database import get_db
from data.kerala_districts import KERALA_DISTRICTS
from model import model
from scheme import notification_scheme
from security.oauth2 import get_current_user, require_president
from services.push_service import send_admin_alert_push

router = APIRouter()


def _validate_district(district: str | None):
	if district is not None and district not in KERALA_DISTRICTS:
		raise HTTPException(status_code=400, detail="Unknown district")


def _broadcast(db: Session, notification: model.Notification):
	"""Fans the alert out as a push to every device belonging to a user in
	the target district, or every registered device if it's a state-wide
	(all-Kerala) alert. Best-effort - a failed push to one device never
	blocks the others or the API response."""
	users_query = db.query(model.User)
	if notification.district:
		users_query = users_query.filter(model.User.district == notification.district)
	user_ids = [u.id for u in users_query.all()]
	if not user_ids:
		return

	tokens = db.query(model.DeviceToken).filter(model.DeviceToken.user_id.in_(user_ids)).all()
	for token_row in tokens:
		send_admin_alert_push(
			fcm_token=token_row.fcm_token,
			notification_id=notification.id,
			title=notification.title,
			body=notification.message,
			severity=notification.severity,
			district=notification.district,
		)


@router.post("/notifications", response_model=notification_scheme.NotificationOut)
def create_notification(
	payload: notification_scheme.NotificationCreate,
	db: Session = Depends(get_db),
	current_user: model.User = Depends(require_president),
):
	_validate_district(payload.district)

	now = str(datetime.utcnow())
	notification = model.Notification(
		title=payload.title,
		message=payload.message,
		severity=payload.severity,
		district=payload.district,
		created_by=current_user.id,
		created_by_name=current_user.name,
		active=True,
		created_time=now,
		updated_time=now,
	)
	db.add(notification)
	db.commit()
	db.refresh(notification)

	_broadcast(db, notification)

	return notification


@router.get("/notifications", response_model=list[notification_scheme.NotificationOut])
def list_notifications(
	db: Session = Depends(get_db),
	current_user: model.User = Depends(get_current_user),
):
	"""President sees every alert they've ever sent (for managing them).
	Everyone else only sees active alerts that target their own district
	or all of Kerala."""
	query = db.query(model.Notification)
	if current_user.role == "president":
		query = query.filter(model.Notification.created_by == current_user.id)
	else:
		query = query.filter(
			model.Notification.active == True,  # noqa: E712
			or_(
				model.Notification.district == current_user.district,
				model.Notification.district.is_(None),
			),
		)
	return query.order_by(model.Notification.id.desc()).all()


@router.get("/notifications/{notification_id}", response_model=notification_scheme.NotificationOut)
def get_notification(
	notification_id: int,
	db: Session = Depends(get_db),
	current_user: model.User = Depends(get_current_user),
):
	notification = db.query(model.Notification).filter(model.Notification.id == notification_id).first()
	if not notification:
		raise HTTPException(status_code=404, detail="Notification not found")

	if current_user.role != "president":
		if not notification.active:
			raise HTTPException(status_code=404, detail="Notification not found")
		if notification.district is not None and notification.district != current_user.district:
			raise HTTPException(status_code=403, detail="This alert does not target your district")

	return notification


@router.put("/notifications/{notification_id}", response_model=notification_scheme.NotificationOut)
def update_notification(
	notification_id: int,
	payload: notification_scheme.NotificationUpdate,
	db: Session = Depends(get_db),
	current_user: model.User = Depends(require_president),
):
	notification = db.query(model.Notification).filter(model.Notification.id == notification_id).first()
	if not notification:
		raise HTTPException(status_code=404, detail="Notification not found")
	if notification.created_by != current_user.id:
		raise HTTPException(status_code=403, detail="You can only edit alerts you sent")

	if payload.title is not None:
		if not payload.title.strip():
			raise HTTPException(status_code=400, detail="title cannot be empty")
		notification.title = payload.title.strip()
	if payload.message is not None:
		if not payload.message.strip():
			raise HTTPException(status_code=400, detail="message cannot be empty")
		notification.message = payload.message.strip()
	if payload.severity is not None:
		notification.severity = payload.severity
	if payload.clear_district:
		notification.district = None
	elif payload.district is not None:
		_validate_district(payload.district)
		notification.district = payload.district
	if payload.active is not None:
		notification.active = payload.active

	notification.updated_time = str(datetime.utcnow())
	db.commit()
	db.refresh(notification)

	# Re-notify affected districts only when the alert is (re-)activated,
	# e.g. a president correcting a typo and re-sending, not on every edit.
	if payload.active is True:
		_broadcast(db, notification)

	return notification


@router.delete("/notifications/{notification_id}")
def delete_notification(
	notification_id: int,
	db: Session = Depends(get_db),
	current_user: model.User = Depends(require_president),
):
	notification = db.query(model.Notification).filter(model.Notification.id == notification_id).first()
	if not notification:
		raise HTTPException(status_code=404, detail="Notification not found")
	if notification.created_by != current_user.id:
		raise HTTPException(status_code=403, detail="You can only delete alerts you sent")

	db.delete(notification)
	db.commit()
	return {"message": "Notification deleted"}
