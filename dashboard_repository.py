from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.customer import Customer
from models.policy import Policy, PolicyStatus
from models.premium_payment import PremiumPayment
from models.claim import Claim
from models.settlement import Settlement


def get_total_customers(db: Session) -> int:
    return db.query(func.count(Customer.id)).scalar() or 0


def get_active_policies(db: Session) -> int:
    return (
        db.query(func.count(Policy.id))
        .filter(
            Policy.policy_status == PolicyStatus.ACTIVE
        )
        .scalar()
        or 0
    )


def get_expired_policies(db: Session) -> int:
    return (
        db.query(func.count(Policy.id))
        .filter(
            Policy.policy_status == PolicyStatus.EXPIRED
        )
        .scalar()
        or 0
    )


def get_total_premium_collected(db: Session) -> Decimal:
    result = (
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
    )

    return Decimal(str(result or 0))


def get_pending_premium(db: Session) -> Decimal:
    result = (
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
    )

    return Decimal(str(result or 0))


def get_total_claims(db: Session) -> int:
    return db.query(func.count(Claim.id)).scalar() or 0


def get_approved_claims(db: Session) -> int:
    return (
        db.query(func.count(Claim.id))
        .filter(
            Claim.claim_status == "Approved"
        )
        .scalar()
        or 0
    )


def get_rejected_claims(db: Session) -> int:
    return (
        db.query(func.count(Claim.id))
        .filter(
            Claim.claim_status == "Rejected"
        )
        .scalar()
        or 0
    )


def get_pending_claims(db: Session) -> int:
    return (
        db.query(func.count(Claim.id))
        .filter(
            Claim.claim_status == "Pending"
        )
        .scalar()
        or 0
    )


def get_total_settlement_amount(db: Session) -> Decimal:
    result = (
        db.query(
            func.coalesce(
                func.sum(Settlement.settlement_amount),
                0,
            )
        )
        .scalar()
    )

    return Decimal(str(result or 0))