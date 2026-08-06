import asyncio
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

def _send_with_retry(message: messaging.Message, attempts: int = 3):
	"""Google's OAuth/network handshake is most likely to hiccup right
	after a cold start (Render free tier spins down when idle) - exactly
	when an SOS is most likely to be the very first request in. A single
	silent failure here means a real emergency alert never arrives."""
	last_error = None
	for attempt in range(attempts):
		try:
			messaging.send(message)
			return
		except Exception as e:
			last_error = e
			if attempt < attempts - 1:
				import time
				time.sleep(0.5)
	print(f"[PUSH ERROR] failed after {attempts} attempts: {last_error}")

async def send_sos_push(fcm_token: str, sos_id: int, sender_name: str, latitude: float, longitude: float):
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
			ttl=86400,
		),
	)

	# messaging.send() is a blocking network call - running it in a thread
	# keeps the async event loop free to handle other requests while it's
	# in flight, instead of freezing the whole backend.
	await asyncio.to_thread(_send_with_retry, message)

async def send_alert_broadcast(fcm_tokens: list[str], title: str, message: str, severity: str):
	"""Sends to up to 500 tokens per Firebase batch call. Data-only, same
	pattern as SOS pushes, so the client controls display consistently."""
	_ensure_initialized()

	if not fcm_tokens:
		return

	messages = [
		messaging.Message(
			token=token,
			data={
				"type": "official_alert",
				"title": title,
				"body": message,
				"severity": severity,
			},
			android=messaging.AndroidConfig(priority="high", ttl=86400),
		)
		for token in fcm_tokens
	]

	def _send_batches():
		for i in range(0, len(messages), 500):
			batch = messages[i:i + 500]
			try:
				messaging.send_each(batch)
			except Exception as e:
				print(f"[ALERT BROADCAST ERROR] batch={i} error={e}")

	await asyncio.to_thread(_send_batches)
