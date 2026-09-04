from sqlalchemy.orm import Session

from models.premium_payment import PremiumPayment


def create_premium_payment(
    db: Session,
    payment: PremiumPayment,
):
    db.add(payment)
    db.commit()
    db.refresh(payment)

    return payment


def get_premium_payment_by_id(
    db: Session,
    payment_id: int,
):
    return (
        db.query(PremiumPayment)
        .filter(
            PremiumPayment.id == payment_id
        )
        .first()
    )


def get_all_premium_payments(
    db: Session,
):
    return (
        db.query(PremiumPayment)
        .order_by(
            PremiumPayment.id.desc()
        )
        .all()
    )


def get_payments_by_policy(
    db: Session,
    policy_id: int,
):
    return (
        db.query(PremiumPayment)
        .filter(
            PremiumPayment.policy_id == policy_id
        )
        .order_by(
            PremiumPayment.id.desc()
        )
        .all()
    )


def get_payments_by_customer(
    db: Session,
    customer_id: int,
):
    return (
        db.query(PremiumPayment)
        .filter(
            PremiumPayment.customer_id == customer_id
        )
        .order_by(
            PremiumPayment.id.desc()
        )
        .all()
    )


def get_payment_by_transaction_id(
    db: Session,
    transaction_id: str,
):
    return (
        db.query(PremiumPayment)
        .filter(
            PremiumPayment.transaction_id
            == transaction_id
        )
        .first()
    )


def update_premium_payment(
    db: Session,
    payment: PremiumPayment,
):
    db.commit()
    db.refresh(payment)

    return payment


def delete_premium_payment(
    db: Session,
    payment: PremiumPayment,
):
    db.delete(payment)
    db.commit()

    return True

from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from models.premium_payment import PremiumPayment


def create_premium_payment(
    db: Session,
    payment: PremiumPayment,
):
    db.add(payment)
    db.commit()
    db.refresh(payment)

    return payment


def get_premium_payment_by_id(
    db: Session,
    payment_id: int,
):
    return (
        db.query(PremiumPayment)
        .filter(
            PremiumPayment.id == payment_id
        )
        .first()
    )


def get_all_premium_payments(
    db: Session,
):
    return (
        db.query(PremiumPayment)
        .order_by(
            PremiumPayment.id.desc()
        )
        .all()
    )


def get_payments_by_policy(
    db: Session,
    policy_id: int,
):
    return (
        db.query(PremiumPayment)
        .filter(
            PremiumPayment.policy_id == policy_id
        )
        .order_by(
            PremiumPayment.id.desc()
        )
        .all()
    )


def get_payments_by_customer(
    db: Session,
    customer_id: int,
):
    return (
        db.query(PremiumPayment)
        .filter(
            PremiumPayment.customer_id == customer_id
        )
        .order_by(
            PremiumPayment.id.desc()
        )
        .all()
    )


def get_payment_by_transaction_id(
    db: Session,
    transaction_id: str,
):
    return (
        db.query(PremiumPayment)
        .filter(
            PremiumPayment.transaction_id
            == transaction_id
        )
        .first()
    )


def update_premium_payment(
    db: Session,
    payment: PremiumPayment,
):
    db.commit()
    db.refresh(payment)

    return payment


def delete_premium_payment(
    db: Session,
    payment: PremiumPayment,
):
    db.delete(payment)
    db.commit()

    return True


# ============================================================
# LEVEL 12
# FILTERING / PAGINATION / SORTING
# ============================================================

def search_premium_payments(
    db: Session,
    payment_status=None,
    payment_method=None,
    date_from: date | None = None,
    date_to: date | None = None,
    page: int = 1,
    limit: int = 10,
    sort_by: str = "id",
    sort_order: str = "desc",
):
    query = db.query(PremiumPayment)

    # --------------------------------------------------------
    # FILTER BY PAYMENT STATUS
    # --------------------------------------------------------

    if payment_status:
        query = query.filter(
            PremiumPayment.payment_status
            == payment_status
        )

    # --------------------------------------------------------
    # FILTER BY PAYMENT METHOD
    # --------------------------------------------------------

    if payment_method:
        query = query.filter(
            PremiumPayment.payment_method
            == payment_method
        )

    # --------------------------------------------------------
    # FILTER BY PAYMENT DATE
    # --------------------------------------------------------

    if date_from:
        query = query.filter(
            PremiumPayment.payment_date
            >= date_from
        )

    if date_to:
        query = query.filter(
            PremiumPayment.payment_date
            <= date_to
        )

    # --------------------------------------------------------
    # SORTING
    # --------------------------------------------------------

    sort_fields = {
        "id": PremiumPayment.id,
        "amount": PremiumPayment.amount,
        "payment_date": PremiumPayment.payment_date,
        "payment_method": PremiumPayment.payment_method,
        "payment_status": PremiumPayment.payment_status,
        "transaction_id": PremiumPayment.transaction_id,
        "premium_due_date": PremiumPayment.premium_due_date,
        "created_at": PremiumPayment.created_at,
        "updated_at": PremiumPayment.updated_at,
    }

    if sort_by not in sort_fields:
        raise ValueError(
            f"Invalid sort field: {sort_by}"
        )

    if sort_order not in {"asc", "desc"}:
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

    offset = (page - 1) * limit

    payments = (
        query
        .offset(offset)
        .limit(limit)
        .all()
    )

    return payments, total