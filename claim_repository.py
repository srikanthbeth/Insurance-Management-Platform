from sqlalchemy.orm import Session

from models.claim import Claim


# ============================================================
# CREATE CLAIM
# ============================================================

def create_claim(
    db: Session,
    claim: Claim,
):
    db.add(claim)
    db.commit()
    db.refresh(claim)

    return claim


# ============================================================
# GET CLAIM BY ID
# ============================================================

def get_claim_by_id(
    db: Session,
    claim_id: int,
):
    return (
        db.query(Claim)
        .filter(
            Claim.id == claim_id
        )
        .first()
    )


# ============================================================
# GET CLAIM BY NUMBER
# ============================================================

def get_claim_by_number(
    db: Session,
    claim_number: str,
):
    return (
        db.query(Claim)
        .filter(
            Claim.claim_number == claim_number
        )
        .first()
    )


# ============================================================
# GET CLAIM BY POLICY + INCIDENT
# ============================================================

def get_claim_by_policy_incident(
    db: Session,
    policy_id: int,
    incident_date,
):
    return (
        db.query(Claim)
        .filter(
            Claim.policy_id == policy_id,
            Claim.incident_date == incident_date,
        )
        .first()
    )


# ============================================================
# GET ALL CLAIMS
# ============================================================

def get_claims(
    db: Session,
):
    return (
        db.query(Claim)
        .order_by(
            Claim.id.desc()
        )
        .all()
    )


# ============================================================
# LEVEL 12
# SEARCH / FILTER / PAGINATION / SORTING
# ============================================================

def search_claims(
    db: Session,
    claim_status=None,
    claim_type=None,
    date_from=None,
    date_to=None,
    amount_from=None,
    amount_to=None,
    page: int = 1,
    limit: int = 10,
    sort_by: str = "id",
    sort_order: str = "desc",
):
    query = db.query(Claim)

    # --------------------------------------------------------
    # FILTER BY CLAIM STATUS
    # --------------------------------------------------------

    if claim_status:
        query = query.filter(
            Claim.status == claim_status
        )

    # --------------------------------------------------------
    # FILTER BY CLAIM TYPE
    # --------------------------------------------------------

    if claim_type:
        query = query.filter(
            Claim.claim_type == claim_type
        )

    # --------------------------------------------------------
    # FILTER BY INCIDENT DATE RANGE
    # --------------------------------------------------------

    if date_from:
        query = query.filter(
            Claim.incident_date >= date_from
        )

    if date_to:
        query = query.filter(
            Claim.incident_date <= date_to
        )

    # --------------------------------------------------------
    # FILTER BY CLAIM AMOUNT RANGE
    # --------------------------------------------------------

    if amount_from is not None:
        query = query.filter(
            Claim.claim_amount >= amount_from
        )

    if amount_to is not None:
        query = query.filter(
            Claim.claim_amount <= amount_to
        )

    # --------------------------------------------------------
    # VALID SORT FIELDS
    # --------------------------------------------------------

    sort_fields = {
        "id": Claim.id,
        "claim_number": Claim.claim_number,
        "claim_type": Claim.claim_type,
        "incident_date": Claim.incident_date,
        "claim_amount": Claim.claim_amount,
        "status": Claim.status,
        "created_at": Claim.created_at,
        "updated_at": Claim.updated_at,
    }

    if sort_by not in sort_fields:
        raise ValueError(
            f"Invalid sort field: {sort_by}"
        )

    # --------------------------------------------------------
    # VALID SORT ORDER
    # --------------------------------------------------------

    if sort_order not in {
        "asc",
        "desc",
    }:
        raise ValueError(
            "Invalid sort order. Use 'asc' or 'desc'"
        )

    sort_column = sort_fields[sort_by]

    if sort_order == "asc":
        query = query.order_by(
            sort_column.asc()
        )
    else:
        query = query.order_by(
            sort_column.desc()
        )

    # --------------------------------------------------------
    # TOTAL COUNT
    # --------------------------------------------------------

    total = query.count()

    # --------------------------------------------------------
    # PAGINATION
    # --------------------------------------------------------

    offset = (
        (page - 1) * limit
    )

    claims = (
        query
        .offset(offset)
        .limit(limit)
        .all()
    )

    return claims, total


# ============================================================
# GET CLAIMS BY CUSTOMER
# ============================================================

def get_claims_by_customer(
    db: Session,
    customer_id: int,
):
    return (
        db.query(Claim)
        .filter(
            Claim.customer_id == customer_id
        )
        .order_by(
            Claim.id.desc()
        )
        .all()
    )


# ============================================================
# GET CLAIMS BY POLICY
# ============================================================

def get_claims_by_policy(
    db: Session,
    policy_id: int,
):
    return (
        db.query(Claim)
        .filter(
            Claim.policy_id == policy_id
        )
        .order_by(
            Claim.id.desc()
        )
        .all()
    )


# ============================================================
# UPDATE CLAIM
# ============================================================

def update_claim(
    db: Session,
    claim: Claim,
):
    db.commit()
    db.refresh(claim)

    return claim


# ============================================================
# DELETE CLAIM
# ============================================================

def delete_claim(
    db: Session,
    claim: Claim,
):
    db.delete(claim)
    db.commit()