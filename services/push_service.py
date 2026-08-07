import base64
import json
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

def send_sos_push(fcm_token: str, sos_id: int, sender_name: str, latitude: float, longitude: float):
	"""Sends a data-only message (no 'notification' block) so the client
	app has full control over how it's displayed - required for the
	custom high-priority sound and full-screen alert rather than a
	default system notification."""
	_ensure_initialized()

	message = messaging.Message(
		token=fcm_token,
		data={
			"type": "sos_alert",
			"sos_id": str(sos_id),
			"sender_name": sender_name,
			"latitude": str(latitude),
			"longitude": str(longitude),
		},
		android=messaging.AndroidConfig(
			priority="high",
			ttl=86400,  # 24 hours - FCM queues the message server-side while the
			            # protector's device is offline and delivers it the
			            # moment they reconnect, as long as it's within this TTL.
		),
	)

	try:
		messaging.send(message)
	except Exception as e:
		print(f"[SOS PUSH ERROR] token={fcm_token} error={e}")