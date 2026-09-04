from datetime import date, datetime
from sqlalchemy import func
from sqlalchemy.orm import Session

from models.customer import Customer
from models.policy import Policy, PolicyStatus
from models.premium_payment import PremiumPayment
from models.claim import Claim
from models.settlement import Settlement
from models.user import User, UserRole


# ============================================================
# ADMIN DASHBOARD
# ============================================================

def get_dashboard_service(db: Session):

    total_customers = (
        db.query(func.count(Customer.id))
        .scalar()
        or 0
    )

    active_policies = (
        db.query(func.count(Policy.id))
        .filter(
            Policy.policy_status == PolicyStatus.ACTIVE
        )
        .scalar()
        or 0
    )

    expired_policies = (
        db.query(func.count(Policy.id))
        .filter(
            Policy.policy_status == PolicyStatus.EXPIRED
        )
        .scalar()
        or 0
    )

    total_premium_collected = (
        db.query(
            func.coalesce(
                func.sum(PremiumPayment.amount),
                0,
            )
        )
        .filter(
            PremiumPayment.payment_status == "Completed"
        )
        .scalar()
        or 0
    )

    pending_premium = (
        db.query(
            func.coalesce(
                func.sum(PremiumPayment.amount),
                0,
            )
        )
        .filter(
            PremiumPayment.payment_status == "Pending"
        )
        .scalar()
        or 0
    )

    total_claims = (
        db.query(func.count(Claim.id))
        .scalar()
        or 0
    )

    approved_claims = (
        db.query(func.count(Claim.id))
        .filter(
            Claim.status == "Approved"
        )
        .scalar()
        or 0
    )

    rejected_claims = (
        db.query(func.count(Claim.id))
        .filter(
            Claim.status == "Rejected"
        )
        .scalar()
        or 0
    )

    pending_claims = (
        db.query(func.count(Claim.id))
        .filter(
            Claim.status == "Pending"
        )
        .scalar()
        or 0
    )

    total_settlement_amount = (
        db.query(
            func.coalesce(
                func.sum(Settlement.approved_amount),
                0,
            )
        )
        .filter(
            Settlement.settlement_status == "Completed"
        )
        .scalar()
        or 0
    )

    return {
        "total_customers": total_customers,
        "active_policies": active_policies,
        "expired_policies": expired_policies,
        "total_premium_collected": total_premium_collected,
        "pending_premium": pending_premium,
        "total_claims": total_claims,
        "approved_claims": approved_claims,
        "rejected_claims": rejected_claims,
        "pending_claims": pending_claims,
        "total_settlement_amount": total_settlement_amount,
    }


# ============================================================
# POLICY-WISE PREMIUM REPORT
# ============================================================

def get_policy_premium_report_service(db: Session):

    rows = (
        db.query(
            Policy.id.label("policy_id"),
            Policy.policy_number,
            func.coalesce(
                func.sum(PremiumPayment.amount),
                0,
            ).label("total_premium"),
        )
        .outerjoin(
            PremiumPayment,
            PremiumPayment.policy_id == Policy.id,
        )
        .group_by(
            Policy.id,
            Policy.policy_number,
        )
        .order_by(
            Policy.id
        )
        .all()
    )

    return [
        {
            "policy_id": row.policy_id,
            "policy_number": row.policy_number,
            "total_premium": row.total_premium,
        }
        for row in rows
    ]


# ============================================================
# CUSTOMER POLICY HISTORY
# ============================================================

def get_customer_policy_history_service(
    db: Session,
    customer_id: int,
):

    customer = (
        db.query(Customer)
        .filter(Customer.id == customer_id)
        .first()
    )

    if not customer:
        raise LookupError("Customer not found")

    policies = (
        db.query(Policy)
        .filter(
            Policy.customer_id == customer_id
        )
        .order_by(
            Policy.start_date.desc()
        )
        .all()
    )

    return {
        "customer_id": customer_id,
        "customer_name": getattr(
            customer,
            "full_name",
            None,
        ),
        "policies": policies,
    }


# ============================================================
# CLAIM SETTLEMENT REPORT
# ============================================================

def get_claim_settlement_report_service(
    db: Session,
):

    rows = (
        db.query(
            Claim.id.label("claim_id"),
            Claim.claim_number,
            Claim.status,
            Claim.claim_amount,
            Settlement.approved_amount,
            Settlement.settlement_status,
            Settlement.settlement_date,
            Settlement.payment_reference,
        )
        .outerjoin(
            Settlement,
            Settlement.claim_id == Claim.id,
        )
        .order_by(
            Claim.id.desc()
        )
        .all()
    )

    return [
        {
            "claim_id": row.claim_id,
            "claim_number": row.claim_number,
            "claim_status": row.status,
            "claim_amount": row.claim_amount,
            "settlement_amount": row.approved_amount,
            "settlement_status": row.settlement_status,
            "settlement_date": row.settlement_date,
            "payment_reference": row.payment_reference,
        }
        for row in rows
    ]


# ============================================================
# AGENT PERFORMANCE REPORT
# ============================================================

def get_agent_performance_report_service(
    db: Session,
):

    agents = (
        db.query(User)
        .filter(
            User.role == UserRole.INSURANCE_AGENT
        )
        .all()
    )

    result = []

    for agent in agents:

        policy_count = (
            db.query(func.count(Policy.id))
            .filter(
                Policy.agent_id == agent.id
            )
            .scalar()
            or 0
        )

        premium_collected = (
            db.query(
                func.coalesce(
                    func.sum(PremiumPayment.amount),
                    0,
                )
            )
            .join(
                Policy,
                Policy.id == PremiumPayment.policy_id,
            )
            .filter(
                Policy.agent_id == agent.id,
                PremiumPayment.payment_status
                == "Completed",
            )
            .scalar()
            or 0
        )

        result.append(
            {
                "agent_id": agent.id,
                "agent_name": agent.full_name,
                "email": agent.email,
                "total_policies": policy_count,
                "premium_collected": premium_collected,
            }
        )

    return result


# ============================================================
# MONTHLY PREMIUM COLLECTION
# ============================================================

def get_monthly_premium_collection_service(
    db: Session,
):

    rows = (
        db.query(
            func.extract(
                "year",
                PremiumPayment.payment_date,
            ).label("year"),
            func.extract(
                "month",
                PremiumPayment.payment_date,
            ).label("month"),
            func.coalesce(
                func.sum(PremiumPayment.amount),
                0,
            ).label("total_amount"),
        )
        .filter(
            PremiumPayment.payment_status
            == "Completed"
        )
        .group_by(
            func.extract(
                "year",
                PremiumPayment.payment_date,
            ),
            func.extract(
                "month",
                PremiumPayment.payment_date,
            ),
        )
        .order_by(
            func.extract(
                "year",
                PremiumPayment.payment_date,
            ),
            func.extract(
                "month",
                PremiumPayment.payment_date,
            ),
        )
        .all()
    )

    return [
        {
            "year": int(row.year),
            "month": int(row.month),
            "total_amount": row.total_amount,
        }
        for row in rows
    ]


# ============================================================
# MONTHLY CLAIM STATISTICS
# ============================================================

def get_monthly_claim_statistics_service(
    db: Session,
):

    rows = (
        db.query(
            func.extract(
                "year",
                Claim.created_at,
            ).label("year"),
            func.extract(
                "month",
                Claim.created_at,
            ).label("month"),
            func.count(Claim.id).label(
                "total_claims"
            ),
        )
        .group_by(
            func.extract(
                "year",
                Claim.created_at,
            ),
            func.extract(
                "month",
                Claim.created_at,
            ),
        )
        .order_by(
            func.extract(
                "year",
                Claim.created_at,
            ),
            func.extract(
                "month",
                Claim.created_at,
            ),
        )
        .all()
    )

    return [
        {
            "year": int(row.year),
            "month": int(row.month),
            "total_claims": row.total_claims,
        }
        for row in rows
    ]