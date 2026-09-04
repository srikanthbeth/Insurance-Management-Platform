from datetime import date, datetime
from decimal import Decimal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


VALID_PAYMENT_METHODS = {
    "UPI",
    "Card",
    "Net Banking",
    "Auto Debit",
}

VALID_PAYMENT_STATUSES = {
    "Pending",
    "Completed",
    "Failed",
    "Refunded",
}


class PremiumPaymentCreate(BaseModel):
    customer_id: int

    amount: Decimal = Field(
        ...,
        gt=0,
    )

    payment_date: date

    payment_method: str

    transaction_id: str = Field(
        ...,
        min_length=3,
        max_length=100,
    )

    payment_status: str = "Pending"

    premium_due_date: date | None = None

    @field_validator("payment_method")
    @classmethod
    def validate_payment_method(cls, value):
        if value not in VALID_PAYMENT_METHODS:
            raise ValueError(
                "Invalid payment method"
            )

        return value

    @field_validator("payment_status")
    @classmethod
    def validate_payment_status(cls, value):
        if value not in VALID_PAYMENT_STATUSES:
            raise ValueError(
                "Invalid payment status"
            )

        return value


class PremiumPaymentUpdate(BaseModel):
    amount: Decimal | None = Field(
        default=None,
        gt=0,
    )

    payment_date: date | None = None

    payment_method: str | None = None

    payment_status: str | None = None

    premium_due_date: date | None = None

    @field_validator("payment_method")
    @classmethod
    def validate_payment_method(cls, value):
        if value is not None and value not in VALID_PAYMENT_METHODS:
            raise ValueError(
                "Invalid payment method"
            )

        return value

    @field_validator("payment_status")
    @classmethod
    def validate_payment_status(cls, value):
        if value is not None and value not in VALID_PAYMENT_STATUSES:
            raise ValueError(
                "Invalid payment status"
            )

        return value


class PremiumPaymentResponse(BaseModel):
    id: int
    policy_id: int
    customer_id: int
    amount: Decimal
    payment_date: date
    payment_method: str
    transaction_id: str
    payment_status: str
    premium_due_date: date | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )

class PremiumPaymentListResponse(BaseModel):
    success: bool
    message: str
    data: list[PremiumPaymentResponse]
    total: int
    page: int
    limit: int