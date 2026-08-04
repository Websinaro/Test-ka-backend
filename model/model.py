from sqlalchemy import Column, Integer, String, Float, ForeignKey, Index
from database.database import Base

class User(Base):
	__tablename__ = "users"

	id = Column(Integer, primary_key=True, index=True)
	name = Column(String(100), nullable=False)
	email = Column(String(150), unique=True, nullable=False, index=True)
	# Indexed: SOS protector-matching looks users up by phone on every SOS
	# send/list call. Without this it was a full table scan per contact.
	phone = Column(String(20), nullable=False, index=True)
	password = Column(String(255), nullable=False)
	district = Column(String(50), nullable=False)
	role = Column(String(40), default="user", nullable=False)
	created_time = Column(String(50), nullable=False)


class SafetyContact(Base):
	__tablename__ = "safety_contacts"

	id = Column(Integer, primary_key=True, index=True)
	user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
	name = Column(String(100), nullable=False)
	relationship = Column(String(50), nullable=True)
	phone = Column(String(20), nullable=False, index=True)
	email = Column(String(150), nullable=True, index=True)
	address = Column(String(255), nullable=True)
	created_time = Column(String(50), nullable=False)


class SosAlert(Base):
	__tablename__ = "sos_alerts"

	id = Column(Integer, primary_key=True, index=True)
	user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
	latitude = Column(Float, nullable=False)
	longitude = Column(Float, nullable=False)
	status = Column(String(20), default="active", nullable=False)  # active | resolved
	message = Column(String(255), nullable=True)
	created_time = Column(String(50), nullable=False)
	resolved_time = Column(String(50), nullable=True)

	# The hot path is "give me this user's active alert" and "give me every
	# active alert" - a composite index on (user_id, status) covers both the
	# per-user lookup and, combined with the partial scan below, the
	# system-wide active list used for protector polling.
	__table_args__ = (
		Index("ix_sos_alerts_user_status", "user_id", "status"),
		Index("ix_sos_alerts_status", "status"),
	)


class DeviceToken(Base):
	__tablename__ = "device_tokens"

	id = Column(Integer, primary_key=True, index=True)
	user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
	fcm_token = Column(String(255), nullable=False, unique=True)
	platform = Column(String(20), nullable=True)
	updated_time = Column(String(50), nullable=False)