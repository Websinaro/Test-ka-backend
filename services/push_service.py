import base64
import json
from typing import Iterable

import firebase_admin
from firebase_admin import credentials, messaging

from config.config import FIREBASE_CREDENTIALS_B64

_initialized = False


def _ensure_initialized():
	global _initialized
	if _initialized:
		return
	decoded = base64.b64decode(FIREBASE_CREDENTIALS_B64)
	cred_dict = json.loads(decoded)
	cred = credentials.Certificate(cred_dict)
	firebase_admin.initialize_app(cred)
	_initialized = True


def _build_message(token: str, sos_id: int, sender_name: str, latitude: float, longitude: float) -> messaging.Message:
	"""Data-only message (no 'notification' block) so the client app has
	full control over how it's displayed - required for the custom
	high-priority sound and full-screen alert rather than a default system
	notification."""
	return messaging.Message(
		token=token,
		data={
			"type": "sos_alert",
			"sos_id": str(sos_id),
			"sender_name": sender_name,
			"latitude": str(latitude),
			"longitude": str(longitude),
		},
		android=messaging.AndroidConfig(
			priority="high",
			ttl=86400,
		),
	)


def send_sos_push(fcm_token: str, sos_id: int, sender_name: str, latitude: float, longitude: float):
	"""Single-token send. Kept for backwards compatibility / other callers;
	create_sos now prefers send_sos_push_batch for multi-protector fan-out."""
	_ensure_initialized()
	try:
		messaging.send(_build_message(fcm_token, sos_id, sender_name, latitude, longitude))
	except Exception as e:
		print(f"[SOS PUSH ERROR] token={fcm_token} error={e}")


def send_sos_push_batch(
	fcm_tokens: Iterable[str],
	sos_id: int,
	sender_name: str,
	latitude: float,
	longitude: float,
):
	"""Sends the SOS push to every protector's device in one batched FCM
	call instead of one blocking `messaging.send()` per token in a Python
	loop. For a user with several safety contacts this used to mean the
	request thread sat waiting on N sequential network round trips to
	Firebase; now it's a single batch request, and it's already running as
	a FastAPI background task so it never delays the sender's response.
	"""
	_ensure_initialized()
	tokens = [t for t in dict.fromkeys(fcm_tokens) if t]  # de-dupe, drop empties
	if not tokens:
		return

	messages = [_build_message(token, sos_id, sender_name, latitude, longitude) for token in tokens]

	try:
		response = messaging.send_each(messages)
		if response.failure_count:
			for token, result in zip(tokens, response.responses):
				if not result.success:
					print(f"[SOS PUSH ERROR] token={token} error={result.exception}")
	except Exception as e:
		print(f"[SOS PUSH BATCH ERROR] tokens={len(tokens)} error={e}")
