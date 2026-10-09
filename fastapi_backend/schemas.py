from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PaymentCreate(BaseModel):
    card_id: int
    amount: Decimal = Field(..., gt=0, le=1_000_000)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    category: Literal["SHOPPING", "FOOD", "TRAVEL", "BILLS", "ENTERTAINMENT", "HEALTH", "OTHER"] = "OTHER"

    @field_validator("currency")
    @classmethod
    def uppercase_currency(cls, v: str) -> str:
        return v.upper()


class PaymentOut(BaseModel):
    id: int
    reference: str
    card_last4: Optional[str] = None
    amount: Decimal
    currency: str
    status: str
    failure_reason: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)



class DashboardTransaction(BaseModel):
    amount: Decimal
    currency: str
    masked_card_number: Optional[str] = None
    date: datetime
    status: str


class DashboardSummary(BaseModel):
    total_transactions: int
    total_amount_spent: Decimal
    current_month_spending: Decimal
    available_credit_limit: Decimal
    last_5_transactions: list[DashboardTransaction]