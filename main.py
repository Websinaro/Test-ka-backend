from fastapi import FastAPI

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

app.add_middleware(EncryptionMiddleware)
app.add_middleware(VersionCheckMiddleware)  

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
