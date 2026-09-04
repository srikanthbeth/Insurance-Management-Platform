from datetime import date

from sqlalchemy.orm import Session

from models.customer import Customer
from models.plan import InsurancePlan, PlanStatus
from models.policy import Policy, PolicyStatus
from models.user import User
from repositories.policy import search_policies
from repositories.policy import (
    create_policy,
    get_all_policies,
    get_policy_by_id,
    get_policy_by_number,
    update_policy,
)


# ============================================================
# AGE CALCULATION
# ============================================================

def calculate_age(date_of_birth: date) -> int:
    today = date.today()

    return (
        today.year
        - date_of_birth.year
        - (
            (today.month, today.day)
            < (date_of_birth.month, date_of_birth.day)
        )
    )


# ============================================================
# CREATE POLICY
# ============================================================

def create_policy_service(
    db: Session,
    data,
):
    # --------------------------------------------------------
    # Duplicate policy number
    # --------------------------------------------------------

    existing_policy = get_policy_by_number(
        db,
        data.policy_number,
    )

    if existing_policy:
        raise ValueError(
            "Policy number already exists"
        )

    # --------------------------------------------------------
    # Customer
    # --------------------------------------------------------

    customer = (
        db.query(Customer)
        .filter(Customer.id == data.customer_id)
        .first()
    )

    if not customer:
        raise LookupError(
            "Customer not found"
        )

    # --------------------------------------------------------
    # Plan
    # --------------------------------------------------------

    plan = (
        db.query(InsurancePlan)
        .filter(
            InsurancePlan.id == data.plan_id
        )
        .first()
    )

    if not plan:
        raise LookupError(
            "Plan not found"
        )

    # --------------------------------------------------------
    # Plan must be active
    # --------------------------------------------------------

    if plan.status != PlanStatus.ACTIVE:
        raise ValueError(
            "Inactive insurance plan cannot be purchased"
        )

    # --------------------------------------------------------
    # Agent
    # --------------------------------------------------------

    agent = (
        db.query(User)
        .filter(User.id == data.agent_id)
        .first()
    )

    if not agent:
        raise LookupError(
            "Agent not found"
        )

    # --------------------------------------------------------
    # Agent role validation
    # --------------------------------------------------------

    if agent.role not in {
        "Insurance Agent",
        "Super Admin",
    }:
        raise ValueError(
            "Selected user is not authorized as an insurance agent"
        )

    # --------------------------------------------------------
    # Date validation
    # --------------------------------------------------------

    if data.end_date <= data.start_date:
        raise ValueError(
            "End date must be after start date"
        )

    # --------------------------------------------------------
    # Customer age eligibility
    # --------------------------------------------------------

    customer_age = calculate_age(
        customer.date_of_birth
    )

    if (
        customer_age < plan.eligibility_age_min
        or customer_age > plan.eligibility_age_max
    ):
        raise ValueError(
            "Customer is not eligible for this insurance plan"
        )

    # --------------------------------------------------------
    # Create policy
    # --------------------------------------------------------

    policy = Policy(
        policy_number=data.policy_number,
        customer_id=data.customer_id,
        plan_id=data.plan_id,
        agent_id=data.agent_id,
        start_date=data.start_date,
        end_date=data.end_date,
        coverage_amount=data.coverage_amount,
        premium_amount=data.premium_amount,
        policy_status=data.policy_status,
    )

    return create_policy(
        db,
        policy,
    )


# ============================================================
# GET ALL POLICIES
# ============================================================

def get_policies_service(
    db: Session,
):
    policies = get_all_policies(db)

    return {
        "success": True,
        "data": policies,
        "total": len(policies),
    }


# Keep this alias if your existing code uses this name
def get_all_policies_service(
    db: Session,
):
    return get_policies_service(db)


# ============================================================
# GET SINGLE POLICY
# ============================================================

def get_policy_service(
    db: Session,
    policy_id: int,
):
    policy = get_policy_by_id(
        db,
        policy_id,
    )

    if not policy:
        raise LookupError(
            "Policy not found"
        )

    return policy


# ============================================================
# UPDATE POLICY
# ============================================================

def update_policy_service(
    db: Session,
    policy_id: int,
    data,
):
    policy = get_policy_by_id(
        db,
        policy_id,
    )

    if not policy:
        raise LookupError(
            "Policy not found"
        )

    # --------------------------------------------------------
    # Cancelled policy cannot be updated
    # --------------------------------------------------------

    if policy.policy_status == PolicyStatus.CANCELLED:
        raise ValueError(
            "Cancelled policy cannot be updated"
        )

    update_data = data.model_dump(
        exclude_unset=True
    )

    # --------------------------------------------------------
    # Validate end date
    # --------------------------------------------------------

    new_start_date = update_data.get(
        "start_date",
        policy.start_date,
    )

    new_end_date = update_data.get(
        "end_date",
        policy.end_date,
    )

    if new_end_date <= new_start_date:
        raise ValueError(
            "End date must be after start date"
        )

    # --------------------------------------------------------
    # Validate status transition
    # --------------------------------------------------------

    new_status = update_data.get(
        "policy_status"
    )

    if new_status is not None:
        validate_status_transition(
            policy.policy_status,
            new_status,
        )

    return update_policy(
        db,
        policy,
        update_data,
    )


# ============================================================
# ACTIVATE POLICY
# ============================================================

def activate_policy_service(
    db: Session,
    policy_id: int,
):
    policy = get_policy_by_id(
        db,
        policy_id,
    )

    if not policy:
        raise LookupError(
            "Policy not found"
        )

    if policy.policy_status == PolicyStatus.ACTIVE:
        raise ValueError(
            "Policy is already active"
        )

    if policy.policy_status == PolicyStatus.CANCELLED:
        raise ValueError(
            "Cancelled policy cannot be activated"
        )

    if policy.policy_status == PolicyStatus.EXPIRED:
        raise ValueError(
            "Expired policy cannot be activated"
        )

    policy.policy_status = PolicyStatus.ACTIVE

    db.commit()
    db.refresh(policy)

    return policy


# ============================================================
# CANCEL POLICY
# ============================================================

def cancel_policy_service(
    db: Session,
    policy_id: int,
):
    policy = get_policy_by_id(
        db,
        policy_id,
    )

    if not policy:
        raise LookupError(
            "Policy not found"
        )

    if policy.policy_status == PolicyStatus.CANCELLED:
        raise ValueError(
            "Policy is already cancelled"
        )

    policy.policy_status = PolicyStatus.CANCELLED

    db.commit()
    db.refresh(policy)

    return policy


# ============================================================
# STATUS TRANSITIONS
# ============================================================

def validate_status_transition(
    current_status,
    new_status,
):
    allowed_transitions = {
        PolicyStatus.PENDING: {
            PolicyStatus.ACTIVE,
            PolicyStatus.CANCELLED,
        },

        PolicyStatus.ACTIVE: {
            PolicyStatus.EXPIRED,
            PolicyStatus.CANCELLED,
            PolicyStatus.SUSPENDED,
        },

        PolicyStatus.SUSPENDED: {
            PolicyStatus.ACTIVE,
            PolicyStatus.CANCELLED,
        },

        PolicyStatus.EXPIRED: set(),

        PolicyStatus.CANCELLED: set(),
    }

    allowed = allowed_transitions.get(
        current_status,
        set(),
    )

    if new_status not in allowed:
        raise ValueError(
            f"Cannot change policy status "
            f"from {current_status} to {new_status}"
        )


def search_policies_service(
    db: Session,
    search=None,
    policy_status=None,
    plan_type=None,
    customer_id=None,
    expiry_from=None,
    expiry_to=None,
    page: int = 1,
    limit: int = 10,
    sort_by: str = "id",
    sort_order: str = "desc",
):
    policies, total = search_policies(
        db=db,
        search=search,
        policy_status=policy_status,
        plan_type=plan_type,
        customer_id=customer_id,
        expiry_from=expiry_from,
        expiry_to=expiry_to,
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return {
        "success": True,
        "message": "Policies retrieved successfully",
        "data": policies,
        "total": total,
        "page": page,
        "limit": limit,
    }