"""
POST /payments/pay        - make a payment: creates a PENDING row, then
                             immediately resolves it to SUCCESS/FAILED via
                             the simulation rules in simulation.py.
GET  /payments/{id}       - look up one of the current user's payments.
GET  /payments/           - the current user's own payment history.

Card ownership is always re-checked here even though the Django side
already scopes card listing to `request.user` — this is a separate
service and must not trust that a card_id belongs to the caller just
because the frontend sent it.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import Card, Transaction, User
from notifications import build_payment_alerts, send_email
from schemas import PaymentCreate, PaymentOut
from simulation import simulate_payment

router = APIRouter(prefix="/payments", tags=["Payments"])


def _utcnow() -> datetime:
    """
    Naive UTC datetime — matches how Django stores DateTimeFields in MySQL
    under USE_TZ=True (the aware value is converted to UTC and written
    without an offset; Django re-attaches UTC tzinfo on read). Writing a
    tz-aware value directly here would be inconsistent with what Django's
    own rows in the same table look like.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _serialize(txn: Transaction) -> PaymentOut:
    return PaymentOut(
        id=txn.id,
        reference=txn.reference,
        card_last4=txn.card.last4 if txn.card else None,
        amount=txn.amount,
        currency=txn.currency,
        status=txn.status,
        failure_reason=txn.failure_reason or "",
        created_at=txn.created_at,
        updated_at=txn.updated_at,
    )


@router.post("/pay", response_model=PaymentOut, status_code=status.HTTP_201_CREATED)
def make_payment(
    payload: PaymentCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    card = db.query(Card).filter(Card.id == payload.card_id, Card.user_id == current_user.id).first()
    if not card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found.")

    # A blocked card must never be able to pay (enforced here, not just in the UI).
    if card.is_blocked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This card is blocked. Please contact support.")

    now = _utcnow()
    txn = Transaction(
        user_id=current_user.id,
        card_id=card.id,
        amount=payload.amount,
        currency=payload.currency,
        status="PENDING",
        created_at=now,
        updated_at=now,
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)

    # "Processing" happens synchronously here for this simulation — a real
    # gateway integration would likely resolve this asynchronously via a
    # webhook, updating the same row from PENDING to a final status later.
    final_status, reason = simulate_payment(card.last4, payload.amount)
    txn.status = final_status
    txn.failure_reason = reason
    txn.updated_at = _utcnow()
    db.commit()
    db.refresh(txn)

    # E-mail alerts (large transaction / low credit). The messages are built here
    # while the DB session is open; only the SMTP send runs after the response.
    for alert in build_payment_alerts(db, current_user, card, txn):
        background_tasks.add_task(send_email, alert)

    return _serialize(txn)


@router.get("/{payment_id}", response_model=PaymentOut)
def get_payment(
    payment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    txn = db.query(Transaction).filter(Transaction.id == payment_id, Transaction.user_id == current_user.id).first()
    if not txn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found.")
    return _serialize(txn)


@router.get("/", response_model=list[PaymentOut])
def list_my_payments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Transaction)
        .filter(Transaction.user_id == current_user.id)
        .order_by(Transaction.created_at.desc())
        .limit(100)
        .all()
    )
    return [_serialize(t) for t in rows]
