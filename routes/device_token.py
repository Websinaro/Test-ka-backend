from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.database import get_db
from model import model
from scheme import sos_scheme
from security.oauth2 import get_current_user

router = APIRouter()

@router.post("/device-token")
def register_device_token(
	payload: sos_scheme.DeviceTokenCreate,
	db: Session = Depends(get_db),
	current_user: model.User = Depends(get_current_user),
):
	existing = db.query(model.DeviceToken).filter(model.DeviceToken.fcm_token == payload.fcm_token).first()
	if existing:
		existing.user_id = current_user.id
		existing.platform = payload.platform
		existing.updated_time = str(datetime.utcnow())
	else:
		db.add(model.DeviceToken(
			user_id=current_user.id,
			fcm_token=payload.fcm_token,
			platform=payload.platform,
			updated_time=str(datetime.utcnow()),
		))
	db.commit()
	return {"message": "Device token registered"}