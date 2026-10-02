"""
Payment simulation rules. No real payment gateway is used anywhere in this
project (per the task's rules) — this module decides SUCCESS vs FAILED
using fixed, documented, deterministic rules rather than randomness, so
the outcome is both realistic to demo AND reliably testable (a randomized
simulator would make automated payment tests flaky).

The decline-triggering last-4 digits below follow the same convention
Stripe's own published test cards use, so anyone familiar with that
pattern will find this intuitive: pick a Luhn-valid card number ending in
one of these digits to demo/test a decline.
"""

from decimal import Decimal

DECLINE_LAST4 = {
    "0002": "Card declined by simulated issuer.",
    "0069": "Simulated expired card.",
    "0127": "Simulated incorrect CVC.",
}

MAX_SIMULATED_AMOUNT = Decimal("5000.00")


def simulate_payment(card_last4: str, amount: Decimal) -> tuple[str, str]:
    """Returns (status, failure_reason) — failure_reason is "" on success."""
    if card_last4 in DECLINE_LAST4:
        return "FAILED", DECLINE_LAST4[card_last4]
    if amount > MAX_SIMULATED_AMOUNT:
        return "FAILED", f"Amount exceeds simulated processing limit of {MAX_SIMULATED_AMOUNT}."
    return "SUCCESS", ""
