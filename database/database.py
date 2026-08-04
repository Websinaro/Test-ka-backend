from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

from config.config import DATABASE_URL

# Production connection pooling.
# - pool_pre_ping: drops dead connections instead of raising on first use
#   (critical after the DB or the host has been idle - a stale connection
#   used to mean the *first* request after a lull failed outright).
# - pool_size/max_overflow: previously unset (SQLAlchemy default pool_size=5,
#   max_overflow=10). During a mass SOS event you can easily have more than
#   5 concurrent requests (SOS create + N protector polls), so requests were
#   queuing up waiting for a free connection. Raised for real concurrency.
# - pool_recycle: recycle connections before most managed Postgres providers
#   (Render, Supabase, RDS) forcibly close idle ones, which also used to
#   surface as a slow/failed first request.
engine = create_engine(
	DATABASE_URL,
	pool_pre_ping=True,
	pool_size=20,
	max_overflow=20,
	pool_recycle=1800,
	pool_timeout=10,
)

SessionLocal = sessionmaker(
	autocommit=False,
	autoflush=False,
	bind=engine
)

Base = declarative_base()

def get_db():
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()
