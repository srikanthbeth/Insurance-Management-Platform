from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


VALID_SETTLEMENT_STATUSES = {
    "Pending",
    "Processing",
    "Completed",
    "Failed",
}


class SettlementCreate(BaseModel):
    approved_amount: Decimal = Field(
        ...,
        gt=0,
    )

    payment_reference: str = Field(
        ...,
        min_length=3,
        max_length=100,
    )

    settlement_status: str = Field(
        default="Pending",
    )


class SettlementResponse(BaseModel):
    id: int
    claim_id: int
    approved_amount: Decimal
    settlement_date: datetime
    payment_reference: str
    settlement_status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class SettlementListResponse(BaseModel):
    success: bool
    message: str
    data: list[SettlementResponse]