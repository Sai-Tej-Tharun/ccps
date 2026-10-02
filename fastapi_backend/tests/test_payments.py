from tests.conftest import make_token


def test_pay_requires_authentication(client, test_card):
    response = client.post("/payments/pay", json={"card_id": test_card.id, "amount": "10.00"})
    assert response.status_code == 401


def test_pay_success(client, auth_headers, test_card):
    response = client.post(
        "/payments/pay", json={"card_id": test_card.id, "amount": "25.00"}, headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["failure_reason"] == ""
    assert data["card_last4"] == "4242"


def test_pay_declined_by_magic_last4(client, db_session, test_user, auth_headers):
    from datetime import datetime as dt, timezone as tz

    from models import Card

    decline_card = Card(
        id=2, user_id=test_user.id, brand="VISA", masked_number="**** **** **** 0002",
        last4="0002", cardholder_name="Jane Doe", expiry_month=12, expiry_year=2030,
        created_at=dt.now(tz.utc).replace(tzinfo=None),
    )
    db_session.add(decline_card)
    db_session.commit()

    response = client.post("/payments/pay", json={"card_id": decline_card.id, "amount": "10.00"}, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "FAILED"
    assert "declined" in data["failure_reason"].lower()


def test_pay_declined_over_simulated_limit(client, auth_headers, test_card):
    response = client.post("/payments/pay", json={"card_id": test_card.id, "amount": "5000.01"}, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "FAILED"
    assert "limit" in data["failure_reason"].lower()


def test_pay_rejects_negative_amount(client, auth_headers, test_card):
    response = client.post("/payments/pay", json={"card_id": test_card.id, "amount": "-5.00"}, headers=auth_headers)
    assert response.status_code == 422


def test_pay_rejects_nonexistent_card(client, auth_headers):
    response = client.post("/payments/pay", json={"card_id": 9999, "amount": "10.00"}, headers=auth_headers)
    assert response.status_code == 404


def test_cannot_pay_with_another_users_card(client, auth_headers, db_session, other_user):
    from datetime import datetime as dt, timezone as tz

    from models import Card

    others_card = Card(
        id=3, user_id=other_user.id, brand="VISA", masked_number="**** **** **** 9999",
        last4="9999", cardholder_name="Bob", expiry_month=12, expiry_year=2030,
        created_at=dt.now(tz.utc).replace(tzinfo=None),
    )
    db_session.add(others_card)
    db_session.commit()

    response = client.post("/payments/pay", json={"card_id": others_card.id, "amount": "10.00"}, headers=auth_headers)
    assert response.status_code == 404


def test_invalid_token_rejected(client, test_card):
    response = client.post(
        "/payments/pay",
        json={"card_id": test_card.id, "amount": "10.00"},
        headers={"Authorization": "Bearer not-a-real-token"},
    )
    assert response.status_code == 401


def test_get_payment_scoped_to_owner(client, auth_headers, test_card, db_session, other_user):
    pay_response = client.post("/payments/pay", json={"card_id": test_card.id, "amount": "10.00"}, headers=auth_headers)
    payment_id = pay_response.json()["id"]

    other_token = make_token(other_user.id)
    response = client.get(f"/payments/{payment_id}", headers={"Authorization": f"Bearer {other_token}"})
    assert response.status_code == 404

    own_response = client.get(f"/payments/{payment_id}", headers=auth_headers)
    assert own_response.status_code == 200


def test_list_my_payments(client, auth_headers, test_card):
    client.post("/payments/pay", json={"card_id": test_card.id, "amount": "10.00"}, headers=auth_headers)
    client.post("/payments/pay", json={"card_id": test_card.id, "amount": "20.00"}, headers=auth_headers)

    response = client.get("/payments/", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 2
