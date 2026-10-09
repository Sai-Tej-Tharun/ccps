"""
Rule-based fraud evaluation, run right after a payment is resolved.

Rule 1  HIGH_VALUE_BURST  FRAUD_HIGH_VALUE_COUNT (3) or more attempts of at least
                          FRAUD_HIGH_VALUE_AMOUNT (2000) by one user within
                          FRAUD_WINDOW_MINUTES (10); the newest attempt is one of them.
Rule 2  MULTI_SOURCE      Attempts by one user within the window that come from
                          FRAUD_SOURCE_COUNT (2) or more different devices or IP
                          addresses (the IP address stands in for "location").

A flagged transaction gets fraud_status = FLAGGED, one adminpanel_fraudlog row per
rule that fired, and e-mail alerts to the cardholder and to FRAUD_ALERT_RECIPIENTS
(comma separated stakeholders). Evaluation never raises: a bug here must not
break a payment.
"""

import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation

from sqlalchemy.orm import Session

from models import Card, FraudLog, Transaction, User
from notifications import EmailAlert, _clean, _money

logger = logging.getLogger("ccps.fraud")


def _env_int(name: str, default: int) -> int:
    try:
        value = int(os.environ.get(name, default))
        return value if value > 0 else default
    except ValueError:
        return default


def _env_decimal(name: str, default: str) -> Decimal:
    try:
        value = Decimal(os.environ.get(name, default))
        return value if value.is_finite() and value > 0 else Decimal(default)
    except InvalidOperation:
        return Decimal(default)


HIGH_VALUE_AMOUNT = _env_decimal("FRAUD_HIGH_VALUE_AMOUNT", "2000")
HIGH_VALUE_COUNT = _env_int("FRAUD_HIGH_VALUE_COUNT", 3)
WINDOW_MINUTES = _env_int("FRAUD_WINDOW_MINUTES", 10)
SOURCE_COUNT = _env_int("FRAUD_SOURCE_COUNT", 2)


@dataclass(frozen=True)
class FraudFinding:
    rule: str
    severity: str
    details: str


def _recipients() -> list[str]:
    raw = os.environ.get("FRAUD_ALERT_RECIPIENTS", "")
    return [r.strip() for r in raw.split(",") if "@" in r]


def _source_key(txn: Transaction) -> str | None:
    if not txn.ip_address and not txn.device_hash:
        return None  # older rows without metadata can't be compared
    return f"{txn.ip_address or '-'}|{txn.device_hash or '-'}"


def evaluate(db: Session, txn: Transaction) -> list[FraudFinding]:
    """Pure rule check. Looks at this user's attempts inside the window, including `txn`."""
    since = txn.created_at - timedelta(minutes=WINDOW_MINUTES)
    recent = (
        db.query(Transaction)
        .filter(Transaction.user_id == txn.user_id, Transaction.created_at >= since, Transaction.created_at <= txn.created_at)
        .all()
    )
    findings: list[FraudFinding] = []

    high_value = [t for t in recent if Decimal(str(t.amount)) >= HIGH_VALUE_AMOUNT]
    # Only the payments that are themselves high-value can complete a burst.
    if Decimal(str(txn.amount)) >= HIGH_VALUE_AMOUNT and len(high_value) >= HIGH_VALUE_COUNT:
        total = sum((Decimal(str(t.amount)) for t in high_value), Decimal("0"))
        findings.append(
            FraudFinding(
                "HIGH_VALUE_BURST",
                "HIGH",
                f"{len(high_value)} payments of {HIGH_VALUE_AMOUNT} or more ({total} in total) within {WINDOW_MINUTES} minutes.",
            )
        )

    sources = {k for k in (_source_key(t) for t in recent) if k}
    if len(sources) >= SOURCE_COUNT:
        findings.append(
            FraudFinding(
                "MULTI_SOURCE",
                "MEDIUM",
                f"{len(recent)} payments from {len(sources)} different devices or IP addresses within {WINDOW_MINUTES} minutes.",
            )
        )
    return findings


def _alerts(user: User, card: Card, txn: Transaction, findings: list[FraudFinding]) -> list[EmailAlert]:
    reasons = "\n".join(f"  - {_clean(f.details)}" for f in findings)
    customer_body = (
        f"Hello {_clean(user.first_name) or 'there'},\n\n"
        f"We noticed unusual activity on your {_clean(card.brand)} card ending {_clean(card.last4)}.\n"
        f"Payment {_clean(txn.reference)} of {_money(txn.amount, txn.currency)} was flagged for review:\n{reasons}\n\n"
        "If this was you, no action is needed. If not, contact support straight away so the card can be blocked.\n"
    )
    alerts = [EmailAlert(to=user.email, subject="Unusual activity on your LedgerPay card", body=customer_body)]

    staff_body = (
        f"Transaction {_clean(txn.reference)} was flagged.\n"
        f"User: {_clean(user.email)}\nCard: {_clean(card.brand)} ending {_clean(card.last4)}\n"
        f"Amount: {_money(txn.amount, txn.currency)}\nStatus: {_clean(txn.status)}\n"
        f"Source IP: {_clean(txn.ip_address) or 'unknown'}\n\nRules triggered:\n{reasons}\n\n"
        "Review it in the admin panel under Security > Fraud alerts.\n"
    )
    alerts += [EmailAlert(to=r, subject="[Fraud alert] Transaction flagged for review", body=staff_body) for r in _recipients()]
    return [a for a in alerts if a.to]


def evaluate_and_record(db: Session, user: User, card: Card, txn: Transaction) -> list[EmailAlert]:
    """Flag + log + build alerts. Returns the e-mails to send (after the response)."""
    try:
        findings = evaluate(db, txn)
        if not findings:
            return []

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        txn.fraud_status = "FLAGGED"
        for f in findings:
            db.add(
                FraudLog(
                    transaction_id=txn.id,
                    user_id=txn.user_id,
                    card_id=txn.card_id,
                    rule=f.rule,
                    severity=f.severity,
                    details=f.details,
                    ip_address=txn.ip_address,
                    device_hash=txn.device_hash or "",
                    created_at=now,
                    reviewed=False,
                    resolution="",
                    review_note="",
                )
            )
        db.commit()
        logger.warning("Fraud rules %s triggered by transaction %s", [f.rule for f in findings], txn.reference)
        return _alerts(user, card, txn, findings)
    except Exception:  # noqa: BLE001 - never let fraud checks break a payment
        db.rollback()
        logger.exception("Fraud evaluation failed for transaction %s", getattr(txn, "reference", "?"))
        return []