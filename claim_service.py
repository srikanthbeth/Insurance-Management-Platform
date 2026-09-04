
from decimal import Decimal

from sqlalchemy.orm import Session

from models.claim import Claim
from models.policy import Policy

from repositories.claim_document_repository import (
    get_unverified_claim_documents,
)

from repositories.claim_repository import (
    create_claim,
    get_claim_by_id,
    get_claim_by_number,
    get_claim_by_policy_incident,
    get_claims,
    search_claims,
    update_claim,
)


# ============================================================
# CLAIM STATUS TRANSITIONS
# ============================================================

VALID_STATUS_TRANSITIONS = {
    "Submitted": {
        "Under Review",
        "Rejected",
    },
    "Under Review": {
        "Documents Required",
        "Approved",
        "Rejected",
    },
    "Documents Required": {
        "Under Review",
        "Rejected",
    },
    "Approved": {
        "Settled",
    },
    "Rejected": set(),
    "Settled": set(),
}


# ============================================================
# VALIDATE POLICY EXISTS
# ============================================================

def validate_policy_exists(
    db: Session,
    policy_id: int,
):
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

    return policy


# ============================================================
# VALIDATE CUSTOMER BELONGS TO POLICY
# ============================================================

def validate_customer_policy(
    policy,
    customer_id: int,
):
    if policy.customer_id != customer_id:
        raise ValueError(
            "Customer does not belong to this policy"
        )


# ============================================================
# VALIDATE POLICY ACTIVE
# ============================================================

def validate_policy_active(
    policy,
):
    if policy.policy_status != "Active":
        raise ValueError(
            "Claim can be created only for an active policy"
        )


# ============================================================
# VALIDATE INCIDENT DATE
# ============================================================

def validate_incident_date(
    policy,
    incident_date,
):
    if (
        incident_date < policy.start_date
        or incident_date > policy.end_date
    ):
        raise ValueError(
            "Incident date must fall within policy coverage"
        )


# ============================================================
# VALIDATE CLAIM AMOUNT
# ============================================================

def validate_claim_amount(
    policy,
    claim_amount,
):
    if Decimal(str(claim_amount)) > Decimal(
        str(policy.coverage_amount)
    ):
        raise ValueError(
            "Claim amount cannot exceed coverage amount"
        )


# ============================================================
# CREATE CLAIM
# ============================================================

def create_claim_service(
    db: Session,
    data,
):
    # --------------------------------------------------------
    # Validate policy
    # --------------------------------------------------------

    policy = validate_policy_exists(
        db,
        data.policy_id,
    )

    # --------------------------------------------------------
    # Claim can only be created for active policy
    # --------------------------------------------------------

    validate_policy_active(
        policy
    )

    # --------------------------------------------------------
    # Validate customer belongs to policy
    # --------------------------------------------------------

    validate_customer_policy(
        policy,
        data.customer_id,
    )

    # --------------------------------------------------------
    # Validate incident date
    # --------------------------------------------------------

    validate_incident_date(
        policy,
        data.incident_date,
    )

    # --------------------------------------------------------
    # Validate claim amount
    # --------------------------------------------------------

    validate_claim_amount(
        policy,
        data.claim_amount,
    )

    # --------------------------------------------------------
    # Prevent duplicate claim number
    # --------------------------------------------------------

    existing_number = get_claim_by_number(
        db,
        data.claim_number,
    )

    if existing_number:
        raise ValueError(
            "Claim number already exists"
        )

    # --------------------------------------------------------
    # Prevent duplicate claim for same incident
    # --------------------------------------------------------

    existing_incident = (
        get_claim_by_policy_incident(
            db,
            data.policy_id,
            data.incident_date,
        )
    )

    if existing_incident:
        raise ValueError(
            "Duplicate claim for the same incident is not allowed"
        )

    # --------------------------------------------------------
    # Create claim
    # --------------------------------------------------------

    claim = Claim(
        claim_number=data.claim_number,
        policy_id=data.policy_id,
        customer_id=data.customer_id,
        claim_type=data.claim_type,
        incident_date=data.incident_date,
        claim_amount=data.claim_amount,
        description=data.description,
        status=data.status,
    )

    return create_claim(
        db,
        claim,
    )


# ============================================================
# GET SINGLE CLAIM
# ============================================================

def get_claim_service(
    db: Session,
    claim_id: int,
):
    claim = get_claim_by_id(
        db,
        claim_id,
    )

    if not claim:
        raise LookupError(
            "Claim not found"
        )

    return claim


# ============================================================
# GET ALL CLAIMS
# ============================================================

# ============================================================
# LEVEL 12
# SEARCH / FILTER / PAGINATION / SORTING
# ============================================================

def get_claims_service(
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
    claims, total = search_claims(
        db=db,
        claim_status=claim_status,
        claim_type=claim_type,
        date_from=date_from,
        date_to=date_to,
        amount_from=amount_from,
        amount_to=amount_to,
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return {
        "success": True,
        "message": "Claims retrieved successfully",
        "data": claims,
        "total": total,
        "page": page,
        "limit": limit,
    }

# ============================================================
# UPDATE CLAIM
# ============================================================

def update_claim_service(
    db: Session,
    claim_id: int,
    data,
):
    claim = get_claim_by_id(
        db,
        claim_id,
    )

    if not claim:
        raise LookupError(
            "Claim not found"
        )

    # --------------------------------------------------------
    # Settled claims cannot be updated
    # --------------------------------------------------------

    if claim.status == "Settled":
        raise ValueError(
            "Settled claim cannot be updated"
        )

    update_data = data.model_dump(
        exclude_unset=True
    )

    # --------------------------------------------------------
    # Validate policy
    # --------------------------------------------------------

    policy = validate_policy_exists(
        db,
        claim.policy_id,
    )

    # --------------------------------------------------------
    # Validate updated incident date
    # --------------------------------------------------------

    if "incident_date" in update_data:

        validate_incident_date(
            policy,
            update_data["incident_date"],
        )

        existing = (
            get_claim_by_policy_incident(
                db,
                claim.policy_id,
                update_data["incident_date"],
            )
        )

        if (
            existing
            and existing.id != claim.id
        ):
            raise ValueError(
                "Duplicate claim for the same incident is not allowed"
            )

    # --------------------------------------------------------
    # Validate updated claim amount
    # --------------------------------------------------------

    if "claim_amount" in update_data:

        validate_claim_amount(
            policy,
            update_data["claim_amount"],
        )

    # --------------------------------------------------------
    # Validate status transition
    # --------------------------------------------------------

    if "status" in update_data:

        new_status = update_data["status"]

        if new_status != claim.status:

            allowed = VALID_STATUS_TRANSITIONS.get(
                claim.status,
                set(),
            )

            if new_status not in allowed:

                raise ValueError(
                    f"Invalid claim status transition: "
                    f"{claim.status} to {new_status}"
                )

            # ------------------------------------------------
            # IMPORTANT:
            # Claim cannot be approved when documents
            # are still unverified.
            # ------------------------------------------------

            if new_status == "Approved":

                unverified_documents = (
                    get_unverified_claim_documents(
                        db,
                        claim.id,
                    )
                )

                if unverified_documents:

                    raise ValueError(
                        "Claim cannot be approved while "
                        "documents are unverified"
                    )

    # --------------------------------------------------------
    # Update fields
    # --------------------------------------------------------

    for field, value in update_data.items():

        setattr(
            claim,
            field,
            value,
        )

    return update_claim(
        db,
        claim,
    )


# ============================================================
# SUBMIT CLAIM
# ============================================================

def submit_claim_service(
    db: Session,
    claim_id: int,
):
    claim = get_claim_by_id(
        db,
        claim_id,
    )

    if not claim:
        raise LookupError(
            "Claim not found"
        )

    if claim.status != "Submitted":

        raise ValueError(
            "Only submitted claims can be processed"
        )

    claim.status = "Under Review"

    return update_claim(
        db,
        claim,
    )


# ============================================================
# APPROVE CLAIM
# ============================================================

def approve_claim_service(
    db: Session,
    claim_id: int,
):
    claim = get_claim_by_id(
        db,
        claim_id,
    )

    if not claim:
        raise LookupError(
            "Claim not found"
        )

    # --------------------------------------------------------
    # Claim must be under review
    # --------------------------------------------------------

    if claim.status != "Under Review":

        raise ValueError(
            "Only claims under review can be approved"
        )

    # --------------------------------------------------------
    # LEVEL 8 BUSINESS RULE
    #
    # Claim cannot proceed to final approval if there are
    # unverified documents.
    # --------------------------------------------------------

    unverified_documents = (
        get_unverified_claim_documents(
            db,
            claim.id,
        )
    )

    if unverified_documents:

        raise ValueError(
            "Claim cannot be approved while documents are unverified"
        )

    # --------------------------------------------------------
    # Approve claim
    # --------------------------------------------------------

    claim.status = "Approved"

    return update_claim(
        db,
        claim,
    )


# ============================================================
# REJECT CLAIM
# ============================================================

def reject_claim_service(
    db: Session,
    claim_id: int,
):
    claim = get_claim_by_id(
        db,
        claim_id,
    )

    if not claim:
        raise LookupError(
            "Claim not found"
        )

    # --------------------------------------------------------
    # Claim can be rejected from these states
    # --------------------------------------------------------

    if claim.status not in {
        "Submitted",
        "Under Review",
        "Documents Required",
    }:

        raise ValueError(
            "Claim cannot be rejected in its current status"
        )

    claim.status = "Rejected"

    return update_claim(
        db,
        claim,
    )

