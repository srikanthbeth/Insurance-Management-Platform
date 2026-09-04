from sqlalchemy import func
from sqlalchemy.orm import Session

from models.customer import Customer
from models.policy import Policy, PolicyStatus
from models.premium_payment import PremiumPayment
from models.claim import Claim
from models.settlement import Settlement
from models.user import User


# ============================================================
# POLICY PREMIUM REPORT
# ============================================================

def get_policy_premium_report(db: Session):

    policies = (
        db.query(
            Policy.id,
            Policy.policy_number,
            Customer.full_name,
            Policy.premium_amount,
        )
        .join(
            Customer,
            Customer.id == Policy.customer_id,
        )
        .all()
    )

    result = []

    for policy in policies:

        collected = (
            db.query(
                func.coalesce(
                    func.sum(PremiumPayment.amount),
                    0,
                )
            )
            .filter(
                PremiumPayment.policy_id == policy.id,
                PremiumPayment.payment_status == "Completed",
            )
            .scalar()
        )

        collected = collected or 0

        pending = policy.premium_amount - collected

        if pending < 0:
            pending = 0

        result.append(
            {
                "policy_id": policy.id,
                "policy_number": policy.policy_number,
                "customer_name": policy.full_name,
                "premium_amount": policy.premium_amount,
                "premium_collected": collected,
                "pending_premium": pending,
            }
        )

    return result


# ============================================================
# CUSTOMER POLICY HISTORY
# ============================================================

def get_customer_policy_history(db: Session):

    customers = db.query(Customer).all()

    result = []

    for customer in customers:

        policies = (
            db.query(Policy)
            .filter(
                Policy.customer_id == customer.id
            )
            .all()
        )

        policy_data = []

        for policy in policies:

            status = policy.policy_status

            if hasattr(status, "value"):
                status = status.value
            else:
                status = str(status)

            policy_data.append(
                {
                    "policy_number": policy.policy_number,
                    "status": status,
                    "start_date": (
                        policy.start_date.isoformat()
                        if policy.start_date
                        else None
                    ),
                    "end_date": (
                        policy.end_date.isoformat()
                        if policy.end_date
                        else None
                    ),
                    "premium_amount": policy.premium_amount,
                }
            )

        result.append(
            {
                "customer_id": customer.id,
                "customer_name": customer.full_name,
                "policies": policy_data,
            }
        )

    return result


# ============================================================
# CLAIM SETTLEMENT REPORT
# ============================================================

def get_claim_settlement_report(db: Session):

    claims = (
        db.query(Claim, Customer)
        .join(
            Customer,
            Customer.id == Claim.customer_id,
        )
        .all()
    )

    result = []

    for claim, customer in claims:

        settlement = (
            db.query(Settlement)
            .filter(
                Settlement.claim_id == claim.id
            )
            .first()
        )

        claim_status = claim.status

        if hasattr(claim_status, "value"):
            claim_status = claim_status.value
        else:
            claim_status = str(claim_status)

        settlement_status = None
        settlement_amount = None

        if settlement:

            settlement_amount = (
                settlement.approved_amount
            )

            settlement_status = (
                settlement.settlement_status
            )

            if hasattr(
                settlement_status,
                "value",
            ):
                settlement_status = (
                    settlement_status.value
                )
            else:
                settlement_status = str(
                    settlement_status
                )

        result.append(
            {
                "claim_id": claim.id,
                "claim_number": claim.claim_number,
                "customer_name": customer.full_name,
                "claim_amount": claim.claim_amount,
                "claim_status": claim_status,
                "settlement_amount": settlement_amount,
                "settlement_status": settlement_status,
            }
        )

    return result


# ============================================================
# AGENT PERFORMANCE
# ============================================================

def get_agent_performance_report(db: Session):

    agents = (
        db.query(User)
        .filter(
            User.role == "Insurance Agent"
        )
        .all()
    )

    result = []

    for agent in agents:

        policies = (
            db.query(Policy)
            .filter(
                Policy.agent_id == agent.id
            )
            .all()
        )

        policy_ids = [
            policy.id
            for policy in policies
        ]

        total_premium = sum(
            (
                policy.premium_amount
                for policy in policies
            ),
            0,
        )

        active_policies = sum(
            1
            for policy in policies
            if (
                policy.policy_status
                == PolicyStatus.ACTIVE
            )
        )

        expired_policies = sum(
            1
            for policy in policies
            if (
                policy.policy_status
                == PolicyStatus.EXPIRED
            )
        )

        total_claims = 0
        approved_claims = 0
        rejected_claims = 0

        if policy_ids:

            claims = (
                db.query(Claim)
                .filter(
                    Claim.policy_id.in_(
                        policy_ids
                    )
                )
                .all()
            )

            total_claims = len(claims)

            approved_claims = sum(
                1
                for claim in claims
                if str(claim.status)
                in (
                    "Approved",
                    "ClaimStatus.APPROVED",
                )
            )

            rejected_claims = sum(
                1
                for claim in claims
                if str(claim.status)
                in (
                    "Rejected",
                    "ClaimStatus.REJECTED",
                )
            )

        result.append(
            {
                "agent_id": agent.id,
                "agent_name": agent.full_name,
                "total_policies": len(policies),
                "active_policies": active_policies,
                "expired_policies": expired_policies,
                "total_premium": total_premium,
                "total_claims": total_claims,
                "approved_claims": approved_claims,
                "rejected_claims": rejected_claims,
            }
        )

    return result


# ============================================================
# MONTHLY PREMIUM COLLECTION
# ============================================================

def get_monthly_premium_report(db: Session):

    month_expression = func.to_char(
        PremiumPayment.payment_date,
        "YYYY-MM",
    )

    results = (
        db.query(
            month_expression.label("month"),

            func.coalesce(
                func.sum(
                    PremiumPayment.amount
                ),
                0,
            ).label("total_collected"),
        )
        .filter(
            PremiumPayment.payment_status
            == "Completed"
        )
        .group_by(
            month_expression
        )
        .order_by(
            month_expression
        )
        .all()
    )

    return [
        {
            "month": row.month,
            "total_collected": row.total_collected,
        }
        for row in results
    ]


# ============================================================
# MONTHLY CLAIM STATISTICS
# ============================================================

def get_monthly_claim_report(db: Session):

    month_expression = func.to_char(
        Claim.created_at,
        "YYYY-MM",
    )

    results = (
        db.query(
            month_expression.label("month"),

            func.count(
                Claim.id
            ).label(
                "total_claims"
            ),

            func.count(
                Claim.id
            ).filter(
                Claim.status == "Approved"
            ).label(
                "approved_claims"
            ),

            func.count(
                Claim.id
            ).filter(
                Claim.status == "Rejected"
            ).label(
                "rejected_claims"
            ),

            func.count(
                Claim.id
            ).filter(
                Claim.status.in_(
                    [
                        "Pending",
                        "Submitted",
                        "Under Review",
                    ]
                )
            ).label(
                "pending_claims"
            ),
        )
        .group_by(
            month_expression
        )
        .order_by(
            month_expression
        )
        .all()
    )

    return [
        {
            "month": row.month,
            "total_claims": row.total_claims,
            "approved_claims": row.approved_claims,
            "rejected_claims": row.rejected_claims,
            "pending_claims": row.pending_claims,
        }
        for row in results
    ]