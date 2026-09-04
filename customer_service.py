from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models.customer import Customer
from repositories.customer_repository import (
    create_customer,
    get_all_customers,
    get_customer_by_email,
    get_customer_by_id,
    get_customer_by_identification_number,
    update_customer,
)
from schemas.customer import (
    CustomerCreate,
    CustomerUpdate,
)


def create_customer_service(
    db: Session,
    data: CustomerCreate,
) -> Customer:

    email = str(data.email).lower()

    existing_email = get_customer_by_email(
        db,
        email,
    )

    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    existing_identification = (
        get_customer_by_identification_number(
            db,
            data.identification_number,
        )
    )

    if existing_identification:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Identification number already registered",
        )

    customer = Customer(
        full_name=data.full_name.strip(),
        email=email,
        phone=data.phone.strip(),
        date_of_birth=data.date_of_birth,
        address=data.address.strip(),
        identification_number=(
            data.identification_number.strip()
        ),
        occupation=data.occupation.strip(),
    )

    try:
        create_customer(
            db,
            customer,
        )

        db.commit()
        db.refresh(customer)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Customer already exists",
        )

    return customer


def get_customers_service(
    db: Session,
) -> list[Customer]:

    return get_all_customers(db)


def get_customer_service(
    db: Session,
    customer_id: int,
) -> Customer:

    customer = get_customer_by_id(
        db,
        customer_id,
    )

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    return customer


def update_customer_service(
    db: Session,
    customer_id: int,
    data: CustomerUpdate,
) -> Customer:

    customer = get_customer_by_id(
        db,
        customer_id,
    )

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    update_data = data.model_dump(
        exclude_unset=True
    )

    if "email" in update_data:

        email = str(
            update_data["email"]
        ).lower()

        existing_email = (
            get_customer_by_email(
                db,
                email,
            )
        )

        if (
            existing_email
            and existing_email.id != customer.id
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        update_data["email"] = email

    if "identification_number" in update_data:

        identification_number = (
            update_data[
                "identification_number"
            ].strip()
        )

        existing_identification = (
            get_customer_by_identification_number(
                db,
                identification_number,
            )
        )

        if (
            existing_identification
            and existing_identification.id
            != customer.id
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Identification number "
                    "already registered"
                ),
            )

        update_data[
            "identification_number"
        ] = identification_number

    if "full_name" in update_data:
        update_data["full_name"] = (
            update_data["full_name"].strip()
        )

    if "phone" in update_data:
        update_data["phone"] = (
            update_data["phone"].strip()
        )

    if "address" in update_data:
        update_data["address"] = (
            update_data["address"].strip()
        )

    if "occupation" in update_data:
        update_data["occupation"] = (
            update_data["occupation"].strip()
        )

    for field, value in update_data.items():
        setattr(
            customer,
            field,
            value,
        )

    try:
        update_customer(
            db,
            customer,
        )

        db.commit()
        db.refresh(customer)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Customer already exists",
        )

    return customer

def delete_customer_service(
    db: Session,
    customer_id: int,
    current_user,
):
    customer = get_customer_by_id(
        db,
        customer_id,
    )

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    customer.is_deleted = True

    try:
        db.commit()
        db.refresh(customer)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to delete customer",
        )

    return {
        "success": True,
        "message": "Customer deleted successfully",
    }