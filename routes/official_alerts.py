from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_

from database.database import get_db
from model import model
from scheme import alert_scheme
from security.oauth2 import get_current_user, require_president
from services.push_service import send_alert_broadcast
from utils.timestamps import utc_now_str

router = APIRouter()

@router.post("/alerts", response_model=alert_scheme.OfficialAlertOut)
def create_alert(
	payload: alert_scheme.OfficialAlertCreate,
	db: Session = Depends(get_db),
	current_user: model.User = Depends(require_president),
):
	expires_time = None
	if payload.expires_in_hours:
		expires_dt = datetime.utcnow() + timedelta(hours=payload.expires_in_hours)
		expires_time = expires_dt.strftime("%Y-%m-%d %H:%M:%S.%f")

	alert = model.OfficialAlert(
		title=payload.title,
		message=payload.message,
		severity=payload.severity,
		district=payload.district,
		created_by=current_user.id,
		created_time=utc_now_str(),
		expires_time=expires_time,
	)
	db.add(alert)
	db.commit()
	db.refresh(alert)

	# Broadcast to everyone, or just one district if specified.
	users_query = db.query(model.User)
	if payload.district:
		users_query = users_query.filter(model.User.district == payload.district)
	user_ids = [u.id for u in users_query.all()]

	tokens = db.query(model.DeviceToken).filter(model.DeviceToken.user_id.in_(user_ids)).all()
	fcm_tokens = [t.fcm_token for t in tokens]

	send_alert_broadcast(fcm_tokens, alert.title, alert.message, alert.severity)

	return alert

@router.get("/alerts", response_model=list[alert_scheme.OfficialAlertOut])
def list_alerts(
	db: Session = Depends(get_db),
	current_user: model.User = Depends(get_current_user),
):
	now = utc_now_str()
	query = db.query(model.OfficialAlert).filter(
		or_(model.OfficialAlert.expires_time.is_(None), model.OfficialAlert.expires_time > now)
	).filter(
		or_(model.OfficialAlert.district.is_(None), model.OfficialAlert.district == current_user.district)
	).order_by(model.OfficialAlert.created_time.desc())

	return query.all()

@router.delete("/alerts/{alert_id}")
def delete_alert(
	alert_id: int,
	db: Session = Depends(get_db),
	current_user: model.User = Depends(require_president),
):
	alert = db.query(model.OfficialAlert).filter(model.OfficialAlert.id == alert_id).first()
	if not alert:
		raise HTTPException(status_code=404, detail="Alert not found")

	db.delete(alert)
	db.commit()
	return {"message": "Alert removed"}