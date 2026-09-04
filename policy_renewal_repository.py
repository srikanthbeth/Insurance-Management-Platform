from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.policy import Policy
from models.policy_renewal import PolicyRenewal


# ============================================================
# CREATE RENEWAL
# ============================================================

def create_policy_renewal(
    db: Session,
    renewal: PolicyRenewal,
):
    db.add(renewal)
    db.commit()
    db.refresh(renewal)

    return renewal


# ============================================================
# GET RENEWAL BY PREVIOUS POLICY
# ============================================================

def get_renewal_by_previous_policy(
    db: Session,
    policy_id: int,
):
    statement = select(PolicyRenewal).where(
        PolicyRenewal.previous_policy_id == policy_id
    )

    return db.scalar(statement)


# ============================================================
# GET RENEWAL BY NEW POLICY
# ============================================================

def get_renewal_by_new_policy(
    db: Session,
    policy_id: int,
):
    statement = select(PolicyRenewal).where(
        PolicyRenewal.new_policy_id == policy_id
    )

    return db.scalar(statement)


# ============================================================
# GET EXPIRING POLICIES
# ============================================================

def get_expiring_policies(
    db: Session,
    days: int = 30,
):
    today = date.today()
    expiry_date = today + timedelta(days=days)

    statement = (
        select(Policy)
        .where(
            Policy.policy_status == "Active",
            Policy.end_date >= today,
            Policy.end_date <= expiry_date,
        )
        .order_by(Policy.end_date.asc())
    )

    return list(
        db.scalars(statement).all()
    )