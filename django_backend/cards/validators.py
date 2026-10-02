"""
Card number handling: validate → detect brand → mask → discard the real
number. The raw number and any CVV exist only for the duration of a single
request (inside the serializer, see serializers.py) and are never written
anywhere — not to the database, not to logs.
"""

import re

CardValidationError = ValueError


def normalize_card_number(raw: str) -> str:
    """Strips spaces/dashes. Raises if what's left isn't 12-19 digits."""
    digits = re.sub(r"[ -]", "", raw or "")
    if not digits.isdigit() or not (12 <= len(digits) <= 19):
        raise CardValidationError("Card number must be 12-19 digits.")
    return digits


def luhn_is_valid(digits: str) -> bool:
    """Standard Luhn (mod 10) checksum used by all major card networks."""
    total = 0
    reverse_digits = digits[::-1]
    for i, ch in enumerate(reverse_digits):
        n = int(ch)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


def detect_brand(digits: str) -> str:
    if digits.startswith("4"):
        return "VISA"
    if digits[:2] in {"51", "52", "53", "54", "55"} or (2221 <= int(digits[:4]) <= 2720 if digits[:4].isdigit() else False):
        return "MASTERCARD"
    if digits[:2] in {"34", "37"}:
        return "AMEX"
    if digits[:4] == "6011" or digits[:2] == "65":
        return "DISCOVER"
    return "CARD"


def mask_card_number(digits: str) -> str:
    """'4111111111111111' -> '**** **** **** 1111' (last 4 only, ever)."""
    last4 = digits[-4:]
    groups = ["****"] * ((len(digits) - 4) // 4 or 3)
    return " ".join(groups + [last4])


def validate_and_mask(raw_number: str) -> dict:
    """
    Runs the full pipeline and returns only what's safe to persist —
    never the digits themselves.
    """
    digits = normalize_card_number(raw_number)
    if not luhn_is_valid(digits):
        raise CardValidationError("Card number failed validation (invalid number).")
    return {
        "brand": detect_brand(digits),
        "last4": digits[-4:],
        "masked_number": mask_card_number(digits),
    }
