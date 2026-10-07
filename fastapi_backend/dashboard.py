"""
GET /dashboard/summary - quick usage stats for the logged-in user.

Everything is computed in SQL (SUM / COUNT / LIMIT 5) rather than loading
rows into Python:
  * one aggregate query over transactions_transaction  (count + 2 sums)
  * one SUM over cards_card                            (total credit limit)
  * one LIMIT 5 query joining transactions -> cards    (recent activity)

Rules used:
  * total_amount_spent / current_month_spending only count SUCCESS
    payments (FAILED and PENDING payments did not actually spend money).
  * total_transactions counts every transaction row of the user.
  * available_credit_limit = total limit of the user's cards
                             - this month's spending (never below 0).
"""

from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import and_, case, func
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import Card, Transaction, User
from schemas import DashboardSummary, DashboardTransaction

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def _utcnow() -> datetime:
    # Naive UTC, same convention payments.py uses for the created_at column.
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _dec(value) -> Decimal:
    return Decimal(str(value or 0)).quantize(Decimal("0.01"))


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    now = _utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    is_success = Transaction.status == "SUCCESS"

    # Query 1: COUNT + SUM(amount) + SUM(amount this month) in one pass.
    total_count, total_spent, month_spent = (
        db.query(
            func.count(Transaction.id),
            func.coalesce(func.sum(case((is_success, Transaction.amount), else_=0)), 0),
            func.coalesce(
                func.sum(case((and_(is_success, Transaction.created_at >= month_start), Transaction.amount), else_=0)),
                0,
            ),
        )
        .filter(Transaction.user_id == current_user.id)
        .one()
    )

    # Query 2: SUM(credit_limit) over the user's cards.
    total_limit = (
        db.query(func.coalesce(func.sum(Card.credit_limit), 0))
        .filter(Card.user_id == current_user.id)
        .scalar()
    )

    # Query 3: last 5 transactions + the card's masked number, LIMIT 5.
    # OUTER JOIN because card_id is nullable (ON DELETE SET NULL).
    recent_rows = (
        db.query(
            Transaction.amount,
            Transaction.currency,
            Transaction.status,
            Transaction.created_at,
            Card.masked_number,
        )
        .outerjoin(Card, Card.id == Transaction.card_id)
        .filter(Transaction.user_id == current_user.id)
        .order_by(Transaction.created_at.desc(), Transaction.id.desc())
        .limit(5)
        .all()
    )

    month_spent = _dec(month_spent)
    available = max(_dec(total_limit) - month_spent, Decimal("0.00"))

    return DashboardSummary(
        total_transactions=total_count,
        total_amount_spent=_dec(total_spent),
        current_month_spending=month_spent,
        available_credit_limit=available,
        last_5_transactions=[
            DashboardTransaction(
                amount=r.amount,
                currency=r.currency,
                masked_card_number=r.masked_number,
                date=r.created_at,
                status=r.status,
            )
            for r in recent_rows
        ],
    )