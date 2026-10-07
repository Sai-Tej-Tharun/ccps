from datetime import datetime, timedelta, timezone
from decimal import Decimal

from models import Card, Transaction


def _naive_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _add_txn(db, user_id, card_id, amount, status="SUCCESS", created_at=None, ref=None):
    created_at = created_at or _naive_now()
    db.add(
        Transaction(
            user_id=user_id, card_id=card_id, amount=Decimal(amount), currency="USD",
            status=status, reference=ref, created_at=created_at, updated_at=created_at,
        )
    )
    db.commit()


def test_summary_requires_jwt(client):
    assert client.get("/dashboard/summary").status_code == 401


def test_summary_rejects_bad_token(client):
    r = client.get("/dashboard/summary", headers={"Authorization": "Bearer not-a-real-token"})
    assert r.status_code == 401


def test_summary_empty_user(client, auth_headers, test_card):
    r = client.get("/dashboard/summary", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["total_transactions"] == 0
    assert Decimal(data["total_amount_spent"]) == 0
    assert Decimal(data["current_month_spending"]) == 0
    assert Decimal(data["available_credit_limit"]) == Decimal("5000.00")
    assert data["last_5_transactions"] == []


def test_summary_totals_and_last_5(client, db_session, auth_headers, test_user, test_card):
    now = _naive_now()
    last_month = now.replace(day=1) - timedelta(days=3)
    _add_txn(db_session, test_user.id, test_card.id, "100.00", created_at=last_month, ref="old")
    for i in range(6):
        _add_txn(db_session, test_user.id, test_card.id, "10.00", created_at=now - timedelta(minutes=10 - i), ref=f"t{i}")
    _add_txn(db_session, test_user.id, test_card.id, "999.00", status="FAILED", ref="failed")

    data = client.get("/dashboard/summary", headers=auth_headers).json()
    assert data["total_transactions"] == 8                      # all rows
    assert Decimal(data["total_amount_spent"]) == Decimal("160.00")      # 100 + 6*10, FAILED excluded
    assert Decimal(data["current_month_spending"]) == Decimal("60.00")   # old one excluded
    assert Decimal(data["available_credit_limit"]) == Decimal("4940.00")
    assert len(data["last_5_transactions"]) == 5
    first = data["last_5_transactions"][0]
    assert first["masked_card_number"] == "**** **** **** 4242"
    assert set(first) == {"amount", "currency", "masked_card_number", "date", "status"}


def test_summary_only_counts_own_data(client, db_session, auth_headers, test_user, other_user, test_card):
    other_card = Card(
        id=9, user_id=other_user.id, brand="VISA", masked_number="**** **** **** 1111", last4="1111",
        cardholder_name="Bob", expiry_month=12, expiry_year=2030, created_at=_naive_now(),
    )
    db_session.add(other_card)
    db_session.commit()
    _add_txn(db_session, other_user.id, other_card.id, "500.00", ref="bobs")

    data = client.get("/dashboard/summary", headers=auth_headers).json()
    assert data["total_transactions"] == 0
    assert Decimal(data["total_amount_spent"]) == 0