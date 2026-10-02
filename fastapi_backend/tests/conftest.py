"""
Tests run against an isolated in-memory SQLite database (NOT the real
MySQL Django owns) so this service's payment logic can be verified in
total isolation, fast and without any external dependency. The mirrored
table definitions in models.py are portable SQL (no MySQL-specific
types), so the same model classes work unchanged against SQLite here.
"""

import os
import sys
from datetime import datetime, timezone

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("JWT_SHARED_SECRET", "test-secret")

from auth import JWT_ALGORITHM, JWT_SHARED_SECRET  # noqa: E402
from database import Base, get_db  # noqa: E402
from main import app  # noqa: E402
from models import Card, User  # noqa: E402

TEST_DB_URL = "sqlite://"


@pytest.fixture()
def db_session():
    # StaticPool keeps this engine on exactly ONE underlying connection —
    # required for an in-memory SQLite DB here because Starlette's
    # TestClient executes requests in a different thread than the test
    # function itself, and plain :memory: SQLite keys a fresh (empty)
    # database per thread otherwise, which would make the app's queries
    # silently hit tables that were never created.
    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture()
def test_user(db_session):
    user = User(id=1, username="jane@example.com", email="jane@example.com", is_active=1)
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture()
def other_user(db_session):
    user = User(id=2, username="bob@example.com", email="bob@example.com", is_active=1)
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture()
def test_card(db_session, test_user):
    card = Card(
        id=1, user_id=test_user.id, brand="VISA", masked_number="**** **** **** 4242",
        last4="4242", cardholder_name="Jane Doe", expiry_month=12, expiry_year=2030,
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db_session.add(card)
    db_session.commit()
    return card


def make_token(user_id: int, token_type: str = "access") -> str:
    return jwt.encode({"user_id": user_id, "token_type": token_type}, JWT_SHARED_SECRET, algorithm=JWT_ALGORITHM)


@pytest.fixture()
def auth_headers(test_user):
    token = make_token(test_user.id)
    return {"Authorization": f"Bearer {token}"}
