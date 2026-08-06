from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from packaging.version import Version, InvalidVersion

from config.config import MIN_SUPPORTED_VERSION, LATEST_VERSION, FORCE_UPDATE_MESSAGE

EXEMPT_PATHS = {"/", "/docs", "/redoc", "/openapi.json", "/app/version"}

class VersionCheckMiddleware(BaseHTTPMiddleware):
	async def dispatch(self, request: Request, call_next):
		if request.url.path in EXEMPT_PATHS:
			return await call_next(request)

		app_version = request.headers.get("x-app-version")

		if app_version:
			try:
				if Version(app_version) < Version(MIN_SUPPORTED_VERSION):
					return JSONResponse(
						status_code=426,  # 426 Upgrade Required - the correct HTTP status for this
						content={
							"error": "update_required",
							"message": FORCE_UPDATE_MESSAGE,
							"min_supported_version": MIN_SUPPORTED_VERSION,
							"latest_version": LATEST_VERSION,
						},
					)
			except InvalidVersion:
				pass  # malformed header - let it through rather than block a real user

		return await call_next(request)