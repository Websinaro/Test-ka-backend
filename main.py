from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware

from database.database import Base, engine
from routes import auth, weather,map as kerala_map,version
from routes import safety_contacts, sos, device_token
from middleware.encryption_middleware import EncryptionMiddleware
from middleware.version_middleware import VersionCheckMiddleware

from alembic.config import Config
from alembic import command

def run_migrations():
	alembic_cfg = Config("alembic.ini")
	command.upgrade(alembic_cfg, "head")

run_migrations()

Base.metadata.create_all(bind=engine)

app = FastAPI()

# Middleware order matters here. Starlette wraps outermost-last: whichever
# middleware is added *last* runs first on the way in and last on the way
# out. Encryption must produce its final encrypted+base64 body before
# GZip compresses it - if GZip ran first, EncryptionMiddleware would try
# to json.loads() raw gzip bytes, fail, and silently fall back to
# returning the *unencrypted*, mislabeled response. So: Encryption and
# VersionCheck are added first (inner), GZip is added last (outermost) so
# it always compresses the already-encrypted final payload.
app.add_middleware(EncryptionMiddleware)
app.add_middleware(VersionCheckMiddleware)

# Compresses responses over ~500 bytes. The encryption middleware wraps
# every JSON body in base64 (33% larger than raw bytes), so gzip here
# claws back real bandwidth/latency on slower mobile connections.
app.add_middleware(GZipMiddleware, minimum_size=500)

app.include_router(auth.router, tags=["Auth"])
app.include_router(weather.router, tags=["Weather"])
app.include_router(kerala_map.router,tags=["Map"])
app.include_router(version.router, tags=["Version"])
app.include_router(safety_contacts.router, tags=["Safety Contacts"])
app.include_router(sos.router, tags=["SOS"])
app.include_router(device_token.router, tags=["Device Token"])

@app.get("/")
def home():
	return {
		"message": "Kerala Disaster Management App By Websinaro Is Running"
	}

@app.get("/health")
def health():
	"""Cheap, unencrypted, unauthenticated liveness check.

	Two jobs:
	1. Load balancers / uptime monitors can hit this without paying the
	   encryption-middleware overhead.
	2. If you're on a hosting tier that sleeps the service when idle (see
	   KEEP_ALIVE.md), point an external cron/uptime pinger at this URL
	   every 5-10 minutes so the backend is never cold when a real SOS
	   comes in.
	"""
	return {"status": "ok"}
