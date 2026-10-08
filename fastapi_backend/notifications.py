"""
E-mail alerts raised by the payment service.

  * Large transaction - a payment above ALERT_LARGE_TRANSACTION_AMOUNT
                        (default 5000), whether it succeeded or was declined.
  * Low credit        - available credit falls below ALERT_LOW_CREDIT_PERCENT
                        (default 10) of the user's total limit. Fires once,
                        at the moment the threshold is crossed, not on every
                        later payment.

The third alert ("card blocked") is sent by Django when an admin blocks a
card - see django_backend/cards/emails.py.

Messages are BUILT while the request's DB session is still open; only the
SMTP delivery runs later, in a FastAPI background task. A mail failure is
logged and never raised, so an unreachable mail server can never fail or
slow down a payment.
"""

import logging
import os
import smtplib
import ssl
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from email.message import EmailMessage

from sqlalchemy import func
from sqlalchemy.orm import Session

from models import Card, Transaction, User

logger = logging.getLogger("ccps.notifications")


def _env_decimal(name: str, default: str) -> Decimal:
    try:
        value = Decimal(os.environ.get(name, default))
        if not value.is_finite() or value <= 0:
            raise InvalidOperation
        return value
    except InvalidOperation:
        logger.warning("Invalid value for %s; using %s", name, default)
        return Decimal(default)


LARGE_TRANSACTION_THRESHOLD = _env_decimal("ALERT_LARGE_TRANSACTION_AMOUNT", "5000")
LOW_CREDIT_THRESHOLD_PERCENT = _env_decimal("ALERT_LOW_CREDIT_PERCENT", "10")


@dataclass(frozen=True)
class EmailAlert:
    to: str
    subject: str
    body: str


def _clean(value) -> str:
    """Single line of text - defence in depth against header injection."""
    return " ".join(str(value or "").split())


def _money(amount, currency: str) -> str:
    return f"{currency} {Decimal(amount):,.2f}"


def _greeting(user: User) -> str:
    name = _clean(user.first_name)
    return f"Hi {name}," if name else "Hello,"


def _large_transaction_alert(user: User, card: Card, txn: Transaction) -> EmailAlert:
    outcome = {"SUCCESS": "was completed", "FAILED": "was declined", "PENDING": "is pending"}.get(txn.status, "was processed")
    lines = [
        _greeting(user),
        "",
        f"A transaction of {_money(txn.amount, txn.currency)} on your {_clean(card.brand)} card ending {card.last4} {outcome}.",
        "",
        f"Reference : {txn.reference}",
        f"Date (UTC): {txn.created_at:%d/%m/%Y %H:%M}",
        f"Status    : {txn.status}",
    ]
    if txn.failure_reason:
        lines.append(f"Reason    : {_clean(txn.failure_reason)}")
    lines += [
        "",
        "If you did not make this payment, ask your administrator to block the card and contact support immediately.",
        "",
        "- LedgerPay Security",
    ]
    return EmailAlert(
        to=user.email,
        subject=f"Large transaction alert: {_money(txn.amount, txn.currency)} on card ending {card.last4}",
        body="\n".join(lines),
    )


def _low_credit_alert(user: User, currency: str, available: Decimal, total_limit: Decimal) -> EmailAlert:
    percent = (available / total_limit * 100).quantize(Decimal("0.1"))
    body = "\n".join(
        [
            _greeting(user),
            "",
            f"Your available credit is now {_money(available, currency)} - {percent}% of your total limit of {_money(total_limit, currency)}.",
            "",
            f"This alert is sent when available credit falls below {LOW_CREDIT_THRESHOLD_PERCENT.normalize()}% of your limit.",
            "Payments may be declined if you go over your limit.",
            "",
            "- LedgerPay Security",
        ]
    )
    return EmailAlert(to=user.email, subject="Low available credit on your LedgerPay account", body=body)


def _low_credit_alert_if_crossed(db: Session, user: User, txn: Transaction) -> EmailAlert | None:
    """Same maths as dashboard.py: available = total limit - this month's successful spend."""
    total_limit = Decimal(
        str(db.query(func.coalesce(func.sum(Card.credit_limit), 0)).filter(Card.user_id == user.id).scalar() or 0)
    )
    if total_limit <= 0:
        return None

    month_start = txn.created_at.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    spent_after = Decimal(
        str(
            db.query(func.coalesce(func.sum(Transaction.amount), 0))
            .filter(
                Transaction.user_id == user.id,
                Transaction.status == "SUCCESS",
                Transaction.created_at >= month_start,
            )
            .scalar()
            or 0
        )
    )
    spent_before = spent_after - Decimal(str(txn.amount))

    zero = Decimal("0")
    available_after = max(total_limit - spent_after, zero)
    available_before = max(total_limit - spent_before, zero)
    threshold = total_limit * LOW_CREDIT_THRESHOLD_PERCENT / 100

    if available_before >= threshold and available_after < threshold:
        return _low_credit_alert(user, txn.currency, available_after, total_limit)
    return None


def build_payment_alerts(db: Session, user: User, card: Card, txn: Transaction) -> list[EmailAlert]:
    """Alerts triggered by one resolved payment. Never raises."""
    alerts: list[EmailAlert] = []
    try:
        if not user.email:
            return alerts
        if Decimal(str(txn.amount)) > LARGE_TRANSACTION_THRESHOLD:
            alerts.append(_large_transaction_alert(user, card, txn))
        if txn.status == "SUCCESS":
            low_credit = _low_credit_alert_if_crossed(db, user, txn)
            if low_credit:
                alerts.append(low_credit)
    except Exception:  # noqa: BLE001 - alerts must never break a payment
        logger.exception("Could not build payment alerts for transaction %s", txn.reference)
    return alerts


def send_email(alert: EmailAlert) -> None:
    """Deliver one alert over SMTP. Safe to run as a background task."""
    host = os.environ.get("EMAIL_HOST", "").strip()
    if not host:
        logger.warning("EMAIL_HOST is not set, so this e-mail was not sent.\nTo: %s\nSubject: %s\n\n%s", alert.to, alert.subject, alert.body)
        return

    try:
        message = EmailMessage()
        message["Subject"] = alert.subject
        message["From"] = os.environ.get("DEFAULT_FROM_EMAIL", "LedgerPay Alerts <no-reply@ledgerpay.local>")
        message["To"] = alert.to
        message.set_content(alert.body)

        port = int(os.environ.get("EMAIL_PORT", "587"))
        username = os.environ.get("EMAIL_HOST_USER", "")
        password = os.environ.get("EMAIL_HOST_PASSWORD", "")
        use_ssl = os.environ.get("EMAIL_USE_SSL", "False") == "True"
        use_tls = os.environ.get("EMAIL_USE_TLS", "True") == "True"
        context = ssl.create_default_context()

        server = smtplib.SMTP_SSL(host, port, timeout=10, context=context) if use_ssl else smtplib.SMTP(host, port, timeout=10)
        with server:
            if use_tls and not use_ssl:
                server.starttls(context=context)
            if username:
                server.login(username, password)
            server.send_message(message)
    except Exception:  # noqa: BLE001 - delivery problems are logged, never raised
        logger.exception("Failed to send alert e-mail '%s'", alert.subject)