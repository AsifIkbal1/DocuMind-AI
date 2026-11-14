import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.core.config import settings

# Ensure storage directories exist
os.makedirs(settings.STORAGE_DIR, exist_ok=True)
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.PROCESSED_DIR, exist_ok=True)

database_url = settings.DATABASE_URL

# Provide reliable fallback if postgres is specified but not yet reachable locally
connect_args = {}
if database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

try:
    engine = create_engine(
        database_url,
        echo=False,
        connect_args=connect_args,
        pool_pre_ping=True,
    )
    # Quick probe
    with engine.connect() as conn:
        pass
except Exception as e:
    # Fallback to local SQLite if configured postgres is not running
    fallback_sqlite = f"sqlite:///{os.path.abspath(os.path.join(settings.STORAGE_DIR, 'documind.db'))}"
    engine = create_engine(
        fallback_sqlite,
        echo=False,
        connect_args={"check_same_thread": False},
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
