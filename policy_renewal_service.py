from datetime import date, timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from models.policy import Policy
from models.policy_renewal import PolicyRenewal

from repositories.policy_renewal_repository import (
    create_policy_renewal,
    get_expiring_policies,
    get_renewal_by_previous_policy,
)


# ============================================================
# RENEW POLICY
# ============================================================

def renew_policy_service(
    db: Session,
    policy_id: int,
):
    # --------------------------------------------------------
    # GET POLICY
    # --------------------------------------------------------

    policy = (
        db.query(Policy)
        .filter(
            Policy.id == policy_id
        )
        .first()
    )

    if not policy:
        raise LookupError(
            "Policy not found"
        )

    # --------------------------------------------------------
    # POLICY STATUS
    # --------------------------------------------------------

    if policy.policy_status != "Active":
        raise ValueError(
            "Only active policies can be renewed"
        )

    # --------------------------------------------------------
    # PREVENT DUPLICATE RENEWAL
    # --------------------------------------------------------

    existing_renewal = (
        get_renewal_by_previous_policy(
            db,
            policy_id,
        )
    )

    if existing_renewal:
        raise ValueError(
            "Policy has already been renewed"
        )

    # --------------------------------------------------------
    # POLICY DATE VALIDATION
    # --------------------------------------------------------

    today = date.today()

    if policy.end_date < today:
        raise ValueError(
            "Expired policies cannot be renewed"
        )

    # --------------------------------------------------------
    # CALCULATE NEW POLICY PERIOD
    # --------------------------------------------------------

    old_start_date = policy.start_date
    old_end_date = policy.end_date

    policy_duration = (
        old_end_date - old_start_date
    ).days

    new_start_date = (
        old_end_date + timedelta(days=1)
    )

    new_end_date = (
        new_start_date
        + timedelta(days=policy_duration)
    )

    # --------------------------------------------------------
    # GENERATE NEW POLICY NUMBER
    # --------------------------------------------------------

    new_policy_number = (
        f"POL-REN-{uuid4().hex[:10].upper()}"
    )

    # --------------------------------------------------------
    # CREATE NEW POLICY
    # --------------------------------------------------------

    new_policy = Policy(
        policy_number=new_policy_number,
        customer_id=policy.customer_id,
        plan_id=policy.plan_id,
        agent_id=policy.agent_id,
        start_date=new_start_date,
        end_date=new_end_date,
        coverage_amount=policy.coverage_amount,
        premium_amount=policy.premium_amount,
        policy_status="Active",
    )

    db.add(new_policy)
    db.flush()

    # --------------------------------------------------------
    # CREATE RENEWAL HISTORY
    # --------------------------------------------------------

    renewal = PolicyRenewal(
        previous_policy_id=policy.id,
        new_policy_id=new_policy.id,
        previous_start_date=old_start_date,
        previous_end_date=old_end_date,
        new_start_date=new_start_date,
        new_end_date=new_end_date,
        renewal_status="Completed",
    )

    renewal = create_policy_renewal(
        db,
        renewal,
    )

    return renewal


# ============================================================
# EXPIRING POLICIES
# ============================================================

def get_expiring_policies_service(
    db: Session,
    days: int = 30,
):
    return get_expiring_policies(
        db,
        days=days,
    )