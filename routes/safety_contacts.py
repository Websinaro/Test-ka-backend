from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.database import get_db
from model import model
from scheme import sos_scheme
from security.oauth2 import get_current_user

router = APIRouter()

@router.post("/safety-contacts", response_model=sos_scheme.SafetyContactOut)
def add_safety_contact(
	contact: sos_scheme.SafetyContactCreate,
	db: Session = Depends(get_db),
	current_user: model.User = Depends(get_current_user),
):
	count = db.query(model.SafetyContact).filter(model.SafetyContact.user_id == current_user.id).count()
	if count >= 5:
		raise HTTPException(status_code=400, detail="You can add up to 5 safety contacts only.")

	new_contact = model.SafetyContact(
		user_id=current_user.id,
		name=contact.name,
		relationship=contact.relationship,
		phone=contact.phone,
		email=contact.email,
		address=contact.address,
		created_time=str(datetime.utcnow()),
	)
	db.add(new_contact)
	db.commit()
	db.refresh(new_contact)
	return new_contact

@router.get("/safety-contacts", response_model=list[sos_scheme.SafetyContactOut])
def list_safety_contacts(
	db: Session = Depends(get_db),
	current_user: model.User = Depends(get_current_user),
):
	return db.query(model.SafetyContact).filter(model.SafetyContact.user_id == current_user.id).all()

@router.put("/safety-contacts/{contact_id}", response_model=sos_scheme.SafetyContactOut)
def update_safety_contact(
	contact_id: int,
	contact: sos_scheme.SafetyContactCreate,
	db: Session = Depends(get_db),
	current_user: model.User = Depends(get_current_user),
):
	existing = db.query(model.SafetyContact).filter(
		model.SafetyContact.id == contact_id,
		model.SafetyContact.user_id == current_user.id,
	).first()
	if not existing:
		raise HTTPException(status_code=404, detail="Safety contact not found")

	existing.name = contact.name
	existing.relationship = contact.relationship
	existing.phone = contact.phone
	existing.email = contact.email
	existing.address = contact.address
	db.commit()
	db.refresh(existing)
	return existing

@router.delete("/safety-contacts/{contact_id}")
def delete_safety_contact(
	contact_id: int,
	db: Session = Depends(get_db),
	current_user: model.User = Depends(get_current_user),
):
	contact = db.query(model.SafetyContact).filter(
		model.SafetyContact.id == contact_id,
		model.SafetyContact.user_id == current_user.id,
	).first()
	if not contact:
		raise HTTPException(status_code=404, detail="Safety contact not found")

	db.delete(contact)
	db.commit()
	return {"message": "Safety contact removed"}