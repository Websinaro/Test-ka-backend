def send_sos_push(fcm_token: str, sos_id: int, sender_name: str, latitude: float, longitude: float):
	"""Placeholder - actual Firebase Cloud Messaging integration comes in
	the next stage (push notification setup). For now this just logs, so
	the SOS + protector-matching logic can be tested end-to-end before
	FCM credentials exist."""
	print(f"[SOS PUSH STUB] token={fcm_token} sos_id={sos_id} from={sender_name} at=({latitude},{longitude})")