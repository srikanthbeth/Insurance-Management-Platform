from decimal import Decimal
from typing import List

from pydantic import BaseModel


# ============================================================
# POLICY PREMIUM REPORT
# ============================================================

class PolicyPremiumReport(BaseModel):
    policy_id: int
    policy_number: str
    customer_name: str
    premium_amount: Decimal
    premium_collected: Decimal
    pending_premium: Decimal


class PolicyPremiumReportResponse(BaseModel):
    success: bool
    message: str
    data: List[PolicyPremiumReport]


# ============================================================
# CUSTOMER POLICY HISTORY
# ============================================================

class CustomerPolicyHistoryItem(BaseModel):
    policy_number: str
    status: str
    start_date: str
    end_date: str
    premium_amount: Decimal


class CustomerPolicyHistoryReport(BaseModel):
    customer_id: int
    customer_name: str
    policies: List[CustomerPolicyHistoryItem]


class CustomerPolicyHistoryResponse(BaseModel):
    success: bool
    message: str
    data: List[CustomerPolicyHistoryReport]


# ============================================================
# CLAIM SETTLEMENT REPORT
# ============================================================

class ClaimSettlementReport(BaseModel):
    claim_id: int
    claim_number: str
    customer_name: str
    claim_amount: Decimal
    claim_status: str
    settlement_amount: Decimal | None = None
    settlement_status: str | None = None


class ClaimSettlementReportResponse(BaseModel):
    success: bool
    message: str
    data: List[ClaimSettlementReport]


# ============================================================
# AGENT PERFORMANCE REPORT
# ============================================================

class AgentPerformanceReport(BaseModel):
    agent_id: int
    agent_name: str
    total_policies: int
    active_policies: int
    expired_policies: int
    total_premium: Decimal
    total_claims: int
    approved_claims: int
    rejected_claims: int


class AgentPerformanceReportResponse(BaseModel):
    success: bool
    message: str
    data: List[AgentPerformanceReport]


# ============================================================
# MONTHLY PREMIUM
# ============================================================

class MonthlyPremiumReport(BaseModel):
    month: str
    total_collected: Decimal


class MonthlyPremiumReportResponse(BaseModel):
    success: bool
    message: str
    data: List[MonthlyPremiumReport]


# ============================================================
# MONTHLY CLAIMS
# ============================================================

class MonthlyClaimReport(BaseModel):
    month: str
    total_claims: int
    approved_claims: int
    rejected_claims: int
    pending_claims: int


class MonthlyClaimReportResponse(BaseModel):
    success: bool
    message: str
    data: List[MonthlyClaimReport]