from datetime import datetime, timezone
from decimal import Decimal
from unittest import mock

from models import Card, Transaction
from notifications import EmailAlert, send_email


def _pay(client, headers, card_id, amount):
    return client.post("/payments/pay", json={"card_id": card_id, "amount": str(amount)}, headers=headers)


def test_large_transaction_sends_alert(client, auth_headers, test_card):
    with mock.patch("payments.send_email") as sender:
        response = _pay(client, auth_headers, test_card.id, "5000.01")
    assert response.status_code == 201
    assert sender.call_count == 1
    alert = sender.call_args.args[0]
    assert alert.to == "jane@example.com"
    assert "5,000.01" in alert.subject
    assert "4242" in alert.body
    assert "FAILED" in alert.body  # amounts over 5000 are declined by the simulator, but still alerted


def test_amount_exactly_at_threshold_does_not_alert(client, auth_headers, test_card):
    with mock.patch("payments.send_email") as sender:
        _pay(client, auth_headers, test_card.id, "5000.00")
    # 5000 is not "more than" 5000 - but it does use up the whole limit, so only the low-credit alert fires.
    subjects = [call.args[0].subject for call in sender.call_args_list]
    assert not any(s.startswith("Large transaction") for s in subjects)


def test_small_payment_sends_nothing(client, auth_headers, test_card):
    with mock.patch("payments.send_email") as sender:
        _pay(client, auth_headers, test_card.id, "25.00")
    sender.assert_not_called()


def test_low_credit_alert_fires_once_when_crossing_ten_percent(client, auth_headers, test_card):
    with mock.patch("payments.send_email") as sender:
        _pay(client, auth_headers, test_card.id, "4400.00")  # 600 left of 5000 = 12%  -> no alert
        assert sender.call_count == 0
        _pay(client, auth_headers, test_card.id, "200.00")  # 400 left = 8%  -> alert
        assert sender.call_count == 1
        assert sender.call_args.args[0].subject.startswith("Low available credit")
        _pay(client, auth_headers, test_card.id, "50.00")  # still low, but already alerted
        assert sender.call_count == 1


def test_failed_payment_does_not_trigger_low_credit(client, db_session, test_user, auth_headers):
    declined = Card(
        id=7, user_id=test_user.id, brand="VISA", masked_number="**** **** **** 0002", last4="0002",
        cardholder_name="Jane", expiry_month=12, expiry_year=2030, credit_limit=Decimal("1000"),
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db_session.add(declined)
    db_session.commit()
    with mock.patch("payments.send_email") as sender:
        _pay(client, auth_headers, declined.id, "990.00")  # FAILED (declined card) -> nothing spent
    sender.assert_not_called()


def test_blocked_card_cannot_pay(client, db_session, auth_headers, test_card):
    test_card.is_blocked = True
    db_session.commit()
    response = _pay(client, auth_headers, test_card.id, "10.00")
    assert response.status_code == 403
    assert "blocked" in response.json()["detail"].lower()
    assert db_session.query(Transaction).count() == 0


def test_alert_failure_never_breaks_payment(client, auth_headers, test_card):
    with mock.patch("notifications._large_transaction_alert", side_effect=RuntimeError("boom")):
        response = _pay(client, auth_headers, test_card.id, "6000.00")
    assert response.status_code == 201


def test_send_email_without_smtp_host_only_logs(monkeypatch):
    monkeypatch.delenv("EMAIL_HOST", raising=False)
    with mock.patch("notifications.smtplib.SMTP") as smtp:
        send_email(EmailAlert(to="a@example.com", subject="s", body="b"))
    smtp.assert_not_called()


def test_send_email_uses_smtp_with_tls_and_login(monkeypatch):
    monkeypatch.setenv("EMAIL_HOST", "smtp.example.com")
    monkeypatch.setenv("EMAIL_HOST_USER", "user")
    monkeypatch.setenv("EMAIL_HOST_PASSWORD", "secret")
    with mock.patch("notifications.smtplib.SMTP") as smtp:
        send_email(EmailAlert(to="a@example.com", subject="Hello", body="Body"))
    server = smtp.return_value
    server.starttls.assert_called_once()
    server.login.assert_called_once_with("user", "secret")
    sent = server.send_message.call_args.args[0]
    assert sent["To"] == "a@example.com" and sent["Subject"] == "Hello"


def test_send_email_swallows_smtp_errors(monkeypatch):
    monkeypatch.setenv("EMAIL_HOST", "smtp.example.com")
    with mock.patch("notifications.smtplib.SMTP", side_effect=OSError("unreachable")):
        send_email(EmailAlert(to="a@example.com", subject="s", body="b"))  # must not raise


def test_header_injection_attempt_is_rejected_not_sent(monkeypatch):
    monkeypatch.setenv("EMAIL_HOST", "smtp.example.com")
    with mock.patch("notifications.smtplib.SMTP") as smtp:
        send_email(EmailAlert(to="a@example.com\nBcc: evil@example.com", subject="s", body="b"))
    smtp.return_value.send_message.assert_not_called()