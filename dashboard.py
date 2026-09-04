from decimal import Decimal

from pydantic import BaseModel


class DashboardData(BaseModel):
    total_customers: int
    active_policies: int
    expired_policies: int

    total_premium_collected: Decimal
    pending_premium: Decimal

    total_claims: int
    approved_claims: int
    rejected_claims: int
    pending_claims: int

    total_settlement_amount: Decimal


class DashboardResponse(BaseModel):
    success: bool
    message: str
    data: DashboardData