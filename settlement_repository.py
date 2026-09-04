from sqlalchemy import select
from sqlalchemy.orm import Session

from models.settlement import Settlement


def create_settlement(
    db: Session,
    settlement: Settlement,
):
    db.add(settlement)
    db.commit()
    db.refresh(settlement)

    return settlement


def get_settlement_by_id(
    db: Session,
    settlement_id: int,
):
    statement = select(Settlement).where(
        Settlement.id == settlement_id
    )

    return db.scalar(statement)


def get_settlement_by_claim(
    db: Session,
    claim_id: int,
):
    statement = select(Settlement).where(
        Settlement.claim_id == claim_id
    )

    return db.scalar(statement)


def get_settlement_by_payment_reference(
    db: Session,
    payment_reference: str,
):
    statement = select(Settlement).where(
        Settlement.payment_reference
        == payment_reference
    )

    return db.scalar(statement)


def get_all_settlements(
    db: Session,
):
    statement = (
        select(Settlement)
        .order_by(Settlement.id.desc())
    )

    return list(db.scalars(statement).all())