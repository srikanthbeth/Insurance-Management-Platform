from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from models.plan import InsurancePlan
from models.policy import Policy


# ============================================================
# CREATE
# ============================================================

def create_policy(
    db: Session,
    policy: Policy,
):
    db.add(policy)
    db.commit()
    db.refresh(policy)

    return policy


# ============================================================
# GET BY ID
# ============================================================

def get_policy_by_id(
    db: Session,
    policy_id: int,
):
    return (
        db.query(Policy)
        .filter(Policy.id == policy_id)
        .first()
    )


# ============================================================
# GET BY POLICY NUMBER
# ============================================================

def get_policy_by_number(
    db: Session,
    policy_number: str,
):
    return (
        db.query(Policy)
        .filter(
            Policy.policy_number == policy_number
        )
        .first()
    )


# ============================================================
# GET ALL
# ============================================================

def get_all_policies(
    db: Session,
):
    return (
        db.query(Policy)
        .order_by(Policy.id.desc())
        .all()
    )


# ============================================================
# UPDATE
# ============================================================

def update_policy(
    db: Session,
    policy: Policy,
    update_data: dict,
):
    for field, value in update_data.items():
        setattr(policy, field, value)

    db.commit()
    db.refresh(policy)

    return policy


# ============================================================
# DELETE
# ============================================================

def delete_policy(
    db: Session,
    policy: Policy,
):
    db.delete(policy)
    db.commit()


# ============================================================
# SEARCH / FILTER / PAGINATION
# ============================================================

def search_policies(
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
    query = (
        db.query(Policy)
        .join(
            InsurancePlan,
            Policy.plan_id == InsurancePlan.id,
        )
    )

    # --------------------------------------------------------
    # SEARCH BY POLICY NUMBER
    # --------------------------------------------------------

    if search:
        query = query.filter(
            Policy.policy_number.ilike(
                f"%{search.strip()}%"
            )
        )

    # --------------------------------------------------------
    # FILTER: POLICY STATUS
    # --------------------------------------------------------

    if policy_status is not None:
        query = query.filter(
            Policy.policy_status == policy_status
        )

    # --------------------------------------------------------
    # FILTER: PLAN TYPE
    # --------------------------------------------------------

    if plan_type is not None:
        query = query.filter(
            InsurancePlan.plan_type == plan_type
        )

    # --------------------------------------------------------
    # FILTER: CUSTOMER
    # --------------------------------------------------------

    if customer_id is not None:
        query = query.filter(
            Policy.customer_id == customer_id
        )

    # --------------------------------------------------------
    # FILTER: EXPIRY DATE FROM
    # --------------------------------------------------------

    if expiry_from is not None:
        query = query.filter(
            Policy.end_date >= expiry_from
        )

    # --------------------------------------------------------
    # FILTER: EXPIRY DATE TO
    # --------------------------------------------------------

    if expiry_to is not None:
        query = query.filter(
            Policy.end_date <= expiry_to
        )

    # --------------------------------------------------------
    # VALIDATE SORT ORDER
    # --------------------------------------------------------

    sort_order = sort_order.lower()

    if sort_order not in {"asc", "desc"}:
        raise ValueError(
            "sort_order must be either 'asc' or 'desc'"
        )

    # --------------------------------------------------------
    # SORT COLUMNS
    # --------------------------------------------------------

    sort_columns = {
        "id": Policy.id,
        "policy_number": Policy.policy_number,
        "start_date": Policy.start_date,
        "end_date": Policy.end_date,
        "premium_amount": Policy.premium_amount,
        "coverage_amount": Policy.coverage_amount,
        "policy_status": Policy.policy_status,
    }

    if sort_by not in sort_columns:
        raise ValueError(
            "Invalid sort_by field"
        )

    sort_column = sort_columns[sort_by]

    # --------------------------------------------------------
    # SORT
    # --------------------------------------------------------

    if sort_order == "desc":
        query = query.order_by(
            desc(sort_column)
        )
    else:
        query = query.order_by(
            asc(sort_column)
        )

    # --------------------------------------------------------
    # TOTAL BEFORE PAGINATION
    # --------------------------------------------------------

    total = query.count()

    # --------------------------------------------------------
    # PAGINATION
    # --------------------------------------------------------

    offset = (page - 1) * limit

    policies = (
        query
        .offset(offset)
        .limit(limit)
        .all()
    )

    return policies, total