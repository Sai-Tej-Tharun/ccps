from decimal import Decimal

from simulation import simulate_payment


def test_normal_card_and_amount_succeeds():
    status, reason = simulate_payment("4242", Decimal("50.00"))
    assert status == "SUCCESS"
    assert reason == ""


def test_magic_decline_last4_fails():
    status, reason = simulate_payment("0002", Decimal("10.00"))
    assert status == "FAILED"
    assert reason


def test_over_limit_amount_fails():
    status, reason = simulate_payment("4242", Decimal("5000.01"))
    assert status == "FAILED"
    assert "limit" in reason.lower()


def test_exactly_at_limit_succeeds():
    status, _ = simulate_payment("4242", Decimal("5000.00"))
    assert status == "SUCCESS"
