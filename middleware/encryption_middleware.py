import json
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from security.crypto import encrypt_payload, decrypt_payload

# Paths that must stay plain JSON — Swagger/OpenAPI need to read these directly,
# and "/" is a manual health-check people hit in a browser.
EXCLUDED_PATHS = {"/docs", "/redoc", "/openapi.json", "/", "/app/version", "/health"}

class EncryptionMiddleware(BaseHTTPMiddleware):
	async def dispatch(self, request: Request, call_next):
		if request.url.path in EXCLUDED_PATHS:
			return await call_next(request)

		if request.method in ("POST", "PUT", "PATCH") and request.headers.get("content-type", "").startswith("application/json"):
			body_bytes = await request.body()
			if body_bytes:
				try:
					wrapper = json.loads(body_bytes)
					if "data" in wrapper:
						decrypted = decrypt_payload(wrapper["data"])
						new_body = json.dumps(decrypted).encode("utf-8")
						request._body = new_body

						async def receive():
							return {"type": "http.request", "body": new_body, "more_body": False}

						request._receive = receive
				except Exception:
					pass

		response = await call_next(request)

		if 200 <= response.status_code < 300 and response.headers.get("content-type", "").startswith("application/json"):
			body = b""
			async for chunk in response.body_iterator:
				body += chunk
			try:
				data = json.loads(body)
				encrypted = encrypt_payload(data)
				new_body = json.dumps({"data": encrypted}).encode("utf-8")
				return Response(
					content=new_body,
					status_code=response.status_code,
					headers={"content-type": "application/json"},
				)
			except Exception:
				return Response(content=body, status_code=response.status_code, headers=dict(response.headers))

		return response
