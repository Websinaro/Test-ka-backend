import os
import base64
import json
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from config.config import AES_SECRET_KEY

AES_KEY = base64.b64decode(AES_SECRET_KEY)

def encrypt_payload(data: dict) -> str:
	aesgcm = AESGCM(AES_KEY)
	nonce = os.urandom(12)
	plaintext = json.dumps(data).encode("utf-8")
	ciphertext = aesgcm.encrypt(nonce, plaintext, None)
	return base64.b64encode(nonce + ciphertext).decode("utf-8")

def decrypt_payload(token: str) -> dict:
	aesgcm = AESGCM(AES_KEY)
	raw = base64.b64decode(token)
	nonce, ciphertext = raw[:12], raw[12:]
	plaintext = aesgcm.decrypt(nonce, ciphertext, None)
	return json.loads(plaintext.decode("utf-8"))
