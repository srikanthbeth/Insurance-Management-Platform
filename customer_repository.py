from sqlalchemy.orm import Session

from models.customer import Customer


def create_customer(
    db: Session,
    customer: Customer,
) -> Customer:
    db.add(customer)
    db.flush()

    return customer


def get_customer_by_id(
    db: Session,
    customer_id: int,
) -> Customer | None:
    return (
        db.query(Customer)
        .filter(
            Customer.id == customer_id,
            Customer.is_deleted.is_(False),
        )
        .first()
    )


def get_customer_by_email(
    db: Session,
    email: str,
) -> Customer | None:
    return (
        db.query(Customer)
        .filter(
            Customer.email == email,
            Customer.is_deleted.is_(False),
        )
        .first()
    )


def get_customer_by_identification_number(
    db: Session,
    identification_number: str,
) -> Customer | None:
    return (
        db.query(Customer)
        .filter(
            Customer.identification_number
            == identification_number,
            Customer.is_deleted.is_(False),
        )
        .first()
    )


def get_all_customers(
    db: Session,
) -> list[Customer]:
    return (
        db.query(Customer)
        .filter(
            Customer.is_deleted.is_(False)
        )
        .order_by(Customer.id.desc())
        .all()
    )


def update_customer(
    db: Session,
    customer: Customer,
) -> Customer:
    db.flush()

    return customer