"""
This service does NOT own migrations — Django does (see
django_backend/*/migrations/). This connects to the exact same MySQL
database and reads/writes the tables Django's ORM created, via the
mirrored table definitions in models.py. If you change a Django model's
schema, update the mirror here to match.
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DB_ENGINE_URL = os.environ.get(
    "FASTAPI_DATABASE_URL",
    "mysql+pymysql://{user}:{password}@{host}:{port}/{name}".format(
        user=os.environ.get("DB_USER", "ccps_user"),
        password=os.environ.get("DB_PASSWORD", "ccps_password"),
        host=os.environ.get("DB_HOST", "mysql"),
        port=os.environ.get("DB_PORT", "3306"),
        name=os.environ.get("DB_NAME", "ccps_db"),
    ),
)

engine = create_engine(DB_ENGINE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
