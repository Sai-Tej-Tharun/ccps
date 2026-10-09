from unittest import mock

import fraud
from models import FraudLog, Transaction


def _pay(client, headers, card_id, amount, device="device-A", category="OTHER"):
    return client.post(
        "/payments/pay",
        json={"card_id": card_id, "amount": str(amount), "category": category},
        headers={**headers, "X-Device-Id": device},
    )


def _txns(db):
    return db.query(Transaction).order_by(Transaction.id).all()


def test_three_high_value_payments_in_a_row_are_flagged(client, auth_headers, test_card, db_session, monkeypatch):
    monkeypatch.setenv("FRAUD_ALERT_RECIPIENTS", "security@example.com, risk@example.com")
    with mock.patch("payments.send_email") as sender:
        for _ in range(3):
            assert _pay(client, auth_headers, test_card.id, "2500.00").status_code == 201

    first, second, third = _txns(db_session)
    assert (first.fraud_status, second.fraud_status, third.fraud_status) == ("CLEAN", "CLEAN", "FLAGGED")

    logs = db_session.query(FraudLog).all()
    assert [(log.rule, log.severity, log.transaction_id, log.reviewed) for log in logs] == [("HIGH_VALUE_BURST", "HIGH", third.id, False)]
    assert "3 payments" in logs[0].details

    fraud_mails = [c.args[0] for c in sender.call_args_list if "nusual activity" in c.args[0].subject or "Fraud alert" in c.args[0].subject]
    assert sorted(m.to for m in fraud_mails) == ["jane@example.com", "risk@example.com", "security@example.com"]
    customer_mail = next(m for m in fraud_mails if m.to == "jane@example.com")
    assert "4242" in customer_mail.body and "5551" not in customer_mail.body


def test_a_small_payment_after_a_burst_is_not_part_of_the_burst(client, auth_headers, test_card, db_session):
    with mock.patch("payments.send_email"):
        for _ in range(3):
            _pay(client, auth_headers, test_card.id, "2500.00")
        _pay(client, auth_headers, test_card.id, "15.00")
    assert [t.fraud_status for t in _txns(db_session)] == ["CLEAN", "CLEAN", "FLAGGED", "CLEAN"]
    assert db_session.query(FraudLog).count() == 1


def test_two_payments_from_different_devices_are_flagged(client, auth_headers, test_card, db_session):
    with mock.patch("payments.send_email"):
        _pay(client, auth_headers, test_card.id, "20.00", device="laptop")
        _pay(client, auth_headers, test_card.id, "20.00", device="phone")

    assert [t.fraud_status for t in _txns(db_session)] == ["CLEAN", "FLAGGED"]
    assert [log.rule for log in db_session.query(FraudLog).all()] == ["MULTI_SOURCE"]


def test_same_device_and_small_amounts_are_not_flagged(client, auth_headers, test_card, db_session):
    with mock.patch("payments.send_email") as sender:
        for _ in range(4):
            _pay(client, auth_headers, test_card.id, "20.00")
    assert {t.fraud_status for t in _txns(db_session)} == {"CLEAN"}
    assert db_session.query(FraudLog).count() == 0
    sender.assert_not_called()


def test_two_high_value_payments_are_below_the_burst_threshold(client, auth_headers, test_card, db_session):
    with mock.patch("payments.send_email"):
        _pay(client, auth_headers, test_card.id, "2500.00")
        _pay(client, auth_headers, test_card.id, "2500.00")
    assert db_session.query(FraudLog).count() == 0


def test_payments_outside_the_time_window_do_not_count(client, auth_headers, test_card, db_session):
    from datetime import timedelta

    with mock.patch("payments.send_email"):
        for _ in range(2):
            _pay(client, auth_headers, test_card.id, "2500.00")
        for txn in _txns(db_session):  # pretend those two happened an hour ago
            txn.created_at = txn.created_at - timedelta(hours=1)
        db_session.commit()
        _pay(client, auth_headers, test_card.id, "2500.00")
    assert db_session.query(FraudLog).count() == 0


def test_other_users_activity_is_not_mixed_in(client, auth_headers, test_card, other_user, db_session):
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    for _ in range(3):
        db_session.add(Transaction(user_id=other_user.id, amount=3000, currency="USD", status="SUCCESS", created_at=now, updated_at=now))
    db_session.commit()
    with mock.patch("payments.send_email"):
        _pay(client, auth_headers, test_card.id, "2500.00")
    assert db_session.query(FraudLog).count() == 0


def test_metadata_is_stored_on_the_transaction(client, auth_headers, test_card, db_session):
    with mock.patch("payments.send_email"):
        _pay(client, auth_headers, test_card.id, "12.00", device="my-browser", category="FOOD")
    txn = _txns(db_session)[0]
    assert txn.category == "FOOD"
    assert txn.ip_address
    assert len(txn.device_hash) == 32 and "my-browser" not in txn.device_hash  # only a hash is kept


def test_invalid_category_is_rejected(client, auth_headers, test_card):
    response = _pay(client, auth_headers, test_card.id, "12.00", category="DRUGS")
    assert response.status_code == 422


def test_a_crash_in_fraud_checks_never_fails_the_payment(client, auth_headers, test_card, db_session):
    with mock.patch.object(fraud, "evaluate", side_effect=RuntimeError("rule bug")), mock.patch("payments.send_email"):
        response = _pay(client, auth_headers, test_card.id, "20.00")
    assert response.status_code == 201
    assert response.json()["status"] == "SUCCESS"