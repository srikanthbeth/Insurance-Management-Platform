from decimal import Decimal

from sqlalchemy.orm import Session

from models.claim import Claim
from models.settlement import Settlement
from repositories.settlement_repository import (
    create_settlement,
    get_all_settlements,
    get_settlement_by_claim,
    get_settlement_by_id,
    get_settlement_by_payment_reference,
)


VALID_SETTLEMENT_STATUSES = {
    "Pending",
    "Processing",
    "Completed",
    "Failed",
}


def create_settlement_service(
    db: Session,
    claim_id: int,
    approved_amount: Decimal,
    payment_reference: str,
    settlement_status: str = "Pending",
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

    if claim.status != "Approved":
        raise ValueError(
            "Only approved claims can be settled"
        )

    # --------------------------------------------------------
    # DUPLICATE SETTLEMENT
    # --------------------------------------------------------

    existing_settlement = (
        get_settlement_by_claim(
            db,
            claim_id,
        )
    )

    if existing_settlement:
        raise ValueError(
            "Claim has already been settled"
        )

    # --------------------------------------------------------
    # SETTLEMENT STATUS
    # --------------------------------------------------------

    if settlement_status not in VALID_SETTLEMENT_STATUSES:
        raise ValueError(
            "Invalid settlement status"
        )

    # --------------------------------------------------------
    # APPROVED AMOUNT
    # --------------------------------------------------------

    if approved_amount <= 0:
        raise ValueError(
            "Approved amount must be greater than zero"
        )

    claim_amount = Decimal(
        str(claim.claim_amount)
    )

    # --------------------------------------------------------
    # GET ASSESSMENT
    # --------------------------------------------------------

    assessment = claim.assessment

    if not assessment:
        raise LookupError(
            "Claim assessment not found"
        )

    eligible_amount = Decimal(
        str(assessment.eligible_amount)
    )

    # --------------------------------------------------------
    # VALIDATE AMOUNT
    # --------------------------------------------------------

    if approved_amount > claim_amount:
        raise ValueError(
            "Settlement amount cannot exceed claim amount"
        )

    if approved_amount > eligible_amount:
        raise ValueError(
            "Settlement amount cannot exceed approved claim amount"
        )

    # --------------------------------------------------------
    # PAYMENT REFERENCE
    # --------------------------------------------------------

    existing_reference = (
        get_settlement_by_payment_reference(
            db,
            payment_reference,
        )
    )

    if existing_reference:
        raise ValueError(
            "Payment reference already exists"
        )

    # --------------------------------------------------------
    # CREATE SETTLEMENT
    # --------------------------------------------------------

    settlement = Settlement(
        claim_id=claim_id,
        approved_amount=approved_amount,
        payment_reference=payment_reference,
        settlement_status=settlement_status,
    )

    settlement = create_settlement(
        db,
        settlement,
    )

    # --------------------------------------------------------
    # COMPLETED SETTLEMENT
    # --------------------------------------------------------

    if settlement_status == "Completed":
        claim.status = "Settled"

        db.add(claim)
        db.commit()
        db.refresh(settlement)

    return settlement


def get_settlements_service(
    db: Session,
):
    return get_all_settlements(db)


def get_settlement_service(
    db: Session,
    settlement_id: int,
):
    settlement = get_settlement_by_id(
        db,
        settlement_id,
    )

    if not settlement:
        raise LookupError(
            "Settlement not found"
        )

    return settlement