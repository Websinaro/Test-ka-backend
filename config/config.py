import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRES_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRES_MINUTES", 60))
AES_SECRET_KEY = os.getenv("AES_SECRET_KEY")

MIN_SUPPORTED_VERSION = os.getenv("MIN_SUPPORTED_VERSION", "2.2.8")
LATEST_VERSION = os.getenv("LATEST_VERSION", "3.0.1")
FORCE_UPDATE_MESSAGE = "This version of WeBAlert is no longer supported. Please update latest version to continue receiving weather and disaster alerts."
FIREBASE_CREDENTIALS_B64 = os.getenv("FIREBASE_CREDENTIALS_B64")
