
from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict, field_validator


VALID_POLICY_STATUSES = {
    "Pending",
    "Active",
    "Expired",
    "Cancelled",
    "Suspended",
}


# ============================================================
# CREATE POLICY
# ============================================================

class PolicyCreate(BaseModel):
    policy_number: str = Field(
        ...,
        min_length=3,
        max_length=50,
    )

    customer_id: int = Field(
        ...,
        gt=0,
    )

    plan_id: int = Field(
        ...,
        gt=0,
    )

    agent_id: int = Field(
        ...,
        gt=0,
    )

    start_date: date

    end_date: date

    coverage_amount: Decimal = Field(
        ...,
        gt=0,
    )

    premium_amount: Decimal = Field(
        ...,
        gt=0,
    )

    policy_status: str = "Pending"

    # --------------------------------------------------------
    # Policy Number Validation
    # --------------------------------------------------------

    @field_validator("policy_number")
    @classmethod
    def validate_policy_number(cls, value):
        value = value.strip()

        if not value:
            raise ValueError(
                "Policy number cannot be empty"
            )

        return value

    # --------------------------------------------------------
    # Policy Status Validation
    # --------------------------------------------------------

    @field_validator("policy_status")
    @classmethod
    def validate_policy_status(cls, value):
        if value not in VALID_POLICY_STATUSES:
            raise ValueError(
                "Invalid policy status"
            )

        return value


# ============================================================
# UPDATE POLICY
# ============================================================

class PolicyUpdate(BaseModel):
    end_date: Optional[date] = None

    coverage_amount: Optional[Decimal] = Field(
        default=None,
        gt=0,
    )

    premium_amount: Optional[Decimal] = Field(
        default=None,
        gt=0,
    )

    policy_status: Optional[str] = None

    # --------------------------------------------------------
    # Policy Status Validation
    # --------------------------------------------------------

    @field_validator("policy_status")
    @classmethod
    def validate_policy_status(cls, value):
        if (
            value is not None
            and value not in VALID_POLICY_STATUSES
        ):
            raise ValueError(
                "Invalid policy status"
            )

        return value


# ============================================================
# POLICY RESPONSE
# ============================================================

class PolicyResponse(BaseModel):
    id: int

    policy_number: str

    customer_id: int
    plan_id: int
    agent_id: int

    start_date: date
    end_date: date

    # Convert PostgreSQL Decimal response to JSON number
    coverage_amount: float
    premium_amount: float

    policy_status: str

    model_config = ConfigDict(
        from_attributes=True
    )


# ============================================================
# POLICY LIST RESPONSE
# ============================================================

class PolicyListResponse(BaseModel):
    success: bool

    message: str

    data: list[PolicyResponse]

    total: int

    page: int

    limit: int

