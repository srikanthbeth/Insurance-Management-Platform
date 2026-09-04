from sqlalchemy.orm import Session

from models.beneficiary import Beneficiary


def create_beneficiary(
    db: Session,
    beneficiary: Beneficiary,
):
    db.add(beneficiary)
    db.commit()
    db.refresh(beneficiary)

    return beneficiary


def get_beneficiary_by_id(
    db: Session,
    beneficiary_id: int,
):
    return (
        db.query(Beneficiary)
        .filter(
            Beneficiary.id == beneficiary_id
        )
        .first()
    )


def get_beneficiaries_by_policy(
    db: Session,
    policy_id: int,
):
    return (
        db.query(Beneficiary)
        .filter(
            Beneficiary.policy_id == policy_id
        )
        .order_by(Beneficiary.id)
        .all()
    )


def get_beneficiary_by_identification(
    db: Session,
    policy_id: int,
    identification_number: str,
):
    return (
        db.query(Beneficiary)
        .filter(
            Beneficiary.policy_id == policy_id,
            Beneficiary.identification_number
            == identification_number,
        )
        .first()
    )


def update_beneficiary(
    db: Session,
    beneficiary: Beneficiary,
):
    db.commit()
    db.refresh(beneficiary)

    return beneficiary


def delete_beneficiary(
    db: Session,
    beneficiary: Beneficiary,
):
    db.delete(beneficiary)
    db.commit()