from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class PolicyRenewalResponse(BaseModel):
    id: int

    previous_policy_id: int
    new_policy_id: int

    previous_start_date: date
    previous_end_date: date

    new_start_date: date
    new_end_date: date

    renewal_date: datetime
    renewal_status: str

    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class ExpiringPolicyResponse(BaseModel):
    id: int
    policy_number: str

    customer_id: int
    plan_id: int
    agent_id: int

    start_date: date
    end_date: date

    coverage_amount: float
    premium_amount: float
    policy_status: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class ExpiringPolicyListResponse(BaseModel):
    success: bool
    message: str
    data: list[ExpiringPolicyResponse]