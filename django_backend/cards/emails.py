"""
Customer e-mail notifications sent by the Django service.

Sending never raises: a mail-server outage must not turn a successful
admin action (e.g. blocking a card) into a 500 response. Failures are
logged instead.
"""

import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def send_card_blocked_email(card) -> bool:
    """Tell the card's owner that the card has been blocked. Returns True if sent."""
    owner = card.user
    if not owner.email:
        return False

    name = " ".join((owner.first_name or "").split())
    greeting = f"Hi {name}," if name else "Hello,"
    subject = f"Security alert: your {card.brand} card ending {card.last4} has been blocked"
    body = "\n".join(
        [
            greeting,
            "",
            f"Your {card.brand} card ending {card.last4} has been blocked and can no longer be used for payments.",
            "",
            "If you were not expecting this, please contact support so we can help you restore access.",
            "",
            "- LedgerPay Security",
        ]
    )

    try:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [owner.email], fail_silently=False)
    except Exception:  # noqa: BLE001 - notification failure must never break the caller
        logger.exception("Could not send card-blocked email for card id=%s", card.pk)
        return False
    return True