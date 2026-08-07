from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean
from database.database import Base

class User(Base):
	__tablename__ = "users"

	id = Column(Integer, primary_key=True, index=True)
	name = Column(String(100), nullable=False)
	email = Column(String(150), unique=True, nullable=False)
	phone = Column(String(20), nullable=False)
	password = Column(String(255), nullable=False)
	district = Column(String(50), nullable=False)
	role = Column(String(40), default="user", nullable=False)
	created_time = Column(String(50), nullable=False)


class SafetyContact(Base):
	__tablename__ = "safety_contacts"

	id = Column(Integer, primary_key=True, index=True)
	user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
	name = Column(String(100), nullable=False)
	relationship = Column(String(50), nullable=True)
	phone = Column(String(20), nullable=False)
	email = Column(String(150), nullable=True)
	address = Column(String(255), nullable=True)
	created_time = Column(String(50), nullable=False)


class SosAlert(Base):
	__tablename__ = "sos_alerts"

	id = Column(Integer, primary_key=True, index=True)
	user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
	latitude = Column(Float, nullable=False)
	longitude = Column(Float, nullable=False)
	status = Column(String(20), default="active", nullable=False)  # active | resolved
	message = Column(String(255), nullable=True)
	created_time = Column(String(50), nullable=False)
	resolved_time = Column(String(50), nullable=True)


class DeviceToken(Base):
	__tablename__ = "device_tokens"

	id = Column(Integer, primary_key=True, index=True)
	user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
	fcm_token = Column(String(255), nullable=False, unique=True)
	platform = Column(String(20), nullable=True)
	updated_time = Column(String(50), nullable=False)


class Notification(Base):
	"""Admin (president) broadcast alert. `district` is nullable - a null
	district means the alert targets all of Kerala rather than one
	district specifically."""
	__tablename__ = "notifications"

	id = Column(Integer, primary_key=True, index=True)
	title = Column(String(150), nullable=False)
	message = Column(String(1000), nullable=False)
	severity = Column(String(20), default="orange", nullable=False)  # green|yellow|orange|light_red|dark_red
	district = Column(String(50), nullable=True, index=True)  # None = all Kerala
	created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
	created_by_name = Column(String(100), nullable=False)
	active = Column(Boolean, default=True, nullable=False)
	created_time = Column(String(50), nullable=False)
	updated_time = Column(String(50), nullable=False)