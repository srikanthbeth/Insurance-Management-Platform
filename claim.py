from datetime import date, datetime
from decimal import Decimal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


VALID_CLAIM_STATUSES = {
    "Submitted",
    "Under Review",
    "Documents Required",
    "Approved",
    "Rejected",
    "Settled",
}


VALID_CLAIM_TYPES = {
    "Health",
    "Life",
    "Vehicle",
    "Property",
    "Travel",
    "Other",
}


class ClaimCreate(BaseModel):
    claim_number: str = Field(
        ...,
        min_length=3,
        max_length=100,
    )

    policy_id: int = Field(
        ...,
        gt=0,
    )

    customer_id: int = Field(
        ...,
        gt=0,
    )

    claim_type: str

    incident_date: date

    claim_amount: Decimal = Field(
        ...,
        gt=0,
    )

    description: str = Field(
        ...,
        min_length=5,
        max_length=2000,
    )

    status: str = "Submitted"

    @field_validator("claim_type")
    @classmethod
    def validate_claim_type(cls, value):
        if value not in VALID_CLAIM_TYPES:
            raise ValueError(
                "Invalid claim type"
            )

        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value):
        if value not in VALID_CLAIM_STATUSES:
            raise ValueError(
                "Invalid claim status"
            )

        return value


class ClaimUpdate(BaseModel):
    claim_type: str | None = None

    incident_date: date | None = None

    claim_amount: Decimal | None = Field(
        default=None,
        gt=0,
    )

    description: str | None = Field(
        default=None,
        min_length=5,
        max_length=2000,
    )

    status: str | None = None

    @field_validator("claim_type")
    @classmethod
    def validate_claim_type(cls, value):
        if value is not None and value not in VALID_CLAIM_TYPES:
            raise ValueError(
                "Invalid claim type"
            )

        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value):
        if value is not None and value not in VALID_CLAIM_STATUSES:
            raise ValueError(
                "Invalid claim status"
            )

        return value


class ClaimResponse(BaseModel):
    id: int
    claim_number: str
    policy_id: int
    customer_id: int
    claim_type: str
    incident_date: date
    claim_amount: Decimal
    description: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )

    # ============================================================
# CLAIM LIST RESPONSE
# ============================================================

class ClaimListResponse(BaseModel):
    success: bool
    message: str
    data: list[ClaimResponse]
    total: int
    page: int
    limit: int