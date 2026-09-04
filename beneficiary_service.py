from decimal import Decimal

from sqlalchemy.orm import Session

from models.beneficiary import Beneficiary
from models.policy import Policy

from repositories.beneficiary_repository import (
    create_beneficiary,
    get_beneficiary_by_id,
    get_beneficiaries_by_policy,
    get_beneficiary_by_identification,
    update_beneficiary,
    delete_beneficiary,
)


def validate_policy_exists(
    db: Session,
    policy_id: int,
):
    policy = (
        db.query(Policy)
        .filter(Policy.id == policy_id)
        .first()
    )

    if not policy:
        raise LookupError(
            "Policy not found"
        )

    return policy


def validate_percentage(
    db: Session,
    policy_id: int,
    percentage: Decimal,
    exclude_id: int | None = None,
):
    beneficiaries = get_beneficiaries_by_policy(
        db,
        policy_id,
    )

    total = Decimal("0")

    for beneficiary in beneficiaries:
        if exclude_id is not None:
            if beneficiary.id == exclude_id:
                continue

        total += Decimal(
            str(beneficiary.percentage)
        )

    new_total = total + percentage

    if new_total > Decimal("100"):
        raise ValueError(
            "Beneficiary percentages cannot exceed 100%"
        )

    return new_total


def create_beneficiary_service(
    db: Session,
    policy_id: int,
    data,
):
    validate_policy_exists(
        db,
        policy_id,
    )

    existing = get_beneficiary_by_identification(
        db,
        policy_id,
        data.identification_number,
    )

    if existing:
        raise ValueError(
            "Duplicate beneficiary is not allowed"
        )

    validate_percentage(
        db,
        policy_id,
        data.percentage,
    )

    beneficiary = Beneficiary(
        policy_id=policy_id,
        name=data.name,
        relationship=data.relationship,
        percentage=data.percentage,
        phone=data.phone,
        identification_number=data.identification_number,
    )

    return create_beneficiary(
        db,
        beneficiary,
    )


def get_policy_beneficiaries_service(
    db: Session,
    policy_id: int,
):
    validate_policy_exists(
        db,
        policy_id,
    )

    return get_beneficiaries_by_policy(
        db,
        policy_id,
    )


def update_beneficiary_service(
    db: Session,
    beneficiary_id: int,
    data,
):
    beneficiary = get_beneficiary_by_id(
        db,
        beneficiary_id,
    )

    if not beneficiary:
        raise LookupError(
            "Beneficiary not found"
        )

    update_data = data.model_dump(
        exclude_unset=True
    )

    if (
        "identification_number"
        in update_data
    ):
        existing = get_beneficiary_by_identification(
            db,
            beneficiary.policy_id,
            update_data[
                "identification_number"
            ],
        )

        if (
            existing
            and existing.id != beneficiary.id
        ):
            raise ValueError(
                "Duplicate beneficiary is not allowed"
            )

    if "percentage" in update_data:
        validate_percentage(
            db,
            beneficiary.policy_id,
            update_data["percentage"],
            exclude_id=beneficiary.id,
        )

    for field, value in update_data.items():
        setattr(
            beneficiary,
            field,
            value,
        )

    return update_beneficiary(
        db,
        beneficiary,
    )


def delete_beneficiary_service(
    db: Session,
    beneficiary_id: int,
):
    beneficiary = get_beneficiary_by_id(
        db,
        beneficiary_id,
    )

    if not beneficiary:
        raise LookupError(
            "Beneficiary not found"
        )

    delete_beneficiary(
        db,
        beneficiary,
    )

    return True