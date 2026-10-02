"""
Mirrors of the Django-owned tables this service needs to read or write.
Table and column names here must exactly match django_backend's models —
see django_backend/cards/models.py and django_backend/transactions/models.py.
This service only ever INSERTs/UPDATEs Transaction rows and reads
User/Card rows; it never touches auth_user or cards_card's schema.
"""

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, SmallInteger, String
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "auth_user"

    id = Column(Integer, primary_key=True)
    username = Column(String(150))
    email = Column(String(254))
    is_active = Column(Integer)


class Card(Base):
    __tablename__ = "cards_card"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("auth_user.id"))
    brand = Column(String(20))
    masked_number = Column(String(32))
    last4 = Column(String(4))
    cardholder_name = Column(String(150))
    expiry_month = Column(SmallInteger)
    expiry_year = Column(SmallInteger)
    created_at = Column(DateTime)


class Transaction(Base):
    __tablename__ = "transactions_transaction"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("auth_user.id"), nullable=False)
    card_id = Column(Integer, ForeignKey("cards_card.id"), nullable=True)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    status = Column(String(10), default="PENDING", nullable=False)
    reference = Column(String(36), unique=True, nullable=False, default=lambda: uuid.uuid4().hex)
    failure_reason = Column(String(255), default="")
    # NOT DB-defaulted: Django's `auto_now_add=True` / `auto_now=True` are
    # Python-side-only behaviors (Django sets the value at ORM save time,
    # not via a SQL DEFAULT on the column — confirmed against the actual
    # generated migration). Since this service bypasses the Django ORM
    # entirely, payments.py sets both of these explicitly on every insert
    # and update rather than relying on any column-level default here.
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    card = relationship("Card")
