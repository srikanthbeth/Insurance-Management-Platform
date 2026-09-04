from decimal import Decimal

from sqlalchemy.orm import Session

from models.claim import Claim
from models.claim_assessment import ClaimAssessment
from repositories.claim_assessment_repository import (
    create_claim_assessment,
    get_claim_assessment_by_claim,
)


VALID_RECOMMENDATIONS = {
    "Approved",
    "Partially Approved",
    "Rejected",
}


def create_claim_assessment_service(
    db: Session,
    claim_id: int,
    assessor_id: int,
    eligible_amount: Decimal,
    assessment_notes: str,
    recommendation: str,
):
    # --------------------------------------------------------
    # GET CLAIM
    # --------------------------------------------------------

    claim = (
        db.query(Claim)
        .filter(
            Claim.id == claim_id
        )
        .first()
    )

    if not claim:
        raise LookupError(
            "Claim not found"
        )

    # --------------------------------------------------------
    # CLAIM STATUS
    # --------------------------------------------------------

    if claim.status != "Under Review":
        raise ValueError(
            "Claim must be Under Review "
            "before assessment"
        )

    # --------------------------------------------------------
    # DUPLICATE ASSESSMENT
    # --------------------------------------------------------

    existing = get_claim_assessment_by_claim(
        db,
        claim_id,
    )

    if existing:
        raise ValueError(
            "Assessment already exists for this claim"
        )

    # --------------------------------------------------------
    # VALIDATE RECOMMENDATION
    # --------------------------------------------------------

    if recommendation not in VALID_RECOMMENDATIONS:
        raise ValueError(
            "Invalid recommendation"
        )

    # --------------------------------------------------------
    # VALIDATE ELIGIBLE AMOUNT
    # --------------------------------------------------------

    if eligible_amount <= 0:
        raise ValueError(
            "Eligible amount must be greater than zero"
        )

    claim_amount = Decimal(
        str(claim.claim_amount)
    )

    # --------------------------------------------------------
    # POLICY COVERAGE
    # --------------------------------------------------------

    policy = claim.policy

    if not policy:
        raise LookupError(
            "Policy not found"
        )

    policy_coverage = Decimal(
        str(policy.coverage_amount)
    )

    # --------------------------------------------------------
    # POLICY COVERAGE VALIDATION
    # --------------------------------------------------------

    # Check policy coverage FIRST
    if eligible_amount > policy_coverage:
        raise ValueError(
            "Eligible amount cannot exceed policy coverage"
        )

    # --------------------------------------------------------
    # CLAIM AMOUNT VALIDATION
    # --------------------------------------------------------

    if eligible_amount > claim_amount:
        raise ValueError(
            "Eligible amount cannot exceed claim amount"
        )

    # --------------------------------------------------------
    # CREATE ASSESSMENT
    # --------------------------------------------------------

    assessment = ClaimAssessment(
        claim_id=claim_id,
        assessor_id=assessor_id,
        eligible_amount=eligible_amount,
        assessment_notes=assessment_notes,
        recommendation=recommendation,
    )

    return create_claim_assessment(
        db,
        assessment,
    )


def get_claim_assessment_service(
    db: Session,
    claim_id: int,
):
    claim = (
        db.query(Claim)
        .filter(
            Claim.id == claim_id
        )
        .first()
    )

    if not claim:
        raise LookupError(
            "Claim not found"
        )

    assessment = get_claim_assessment_by_claim(
        db,
        claim_id,
    )

    if not assessment:
        raise LookupError(
            "Assessment not found"
        )

    return assessment