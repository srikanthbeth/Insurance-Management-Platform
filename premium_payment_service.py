from decimal import Decimal

from sqlalchemy.orm import Session

from models.customer import Customer
from models.policy import Policy
from models.premium_payment import PremiumPayment

from repositories.premium_payment_repository import (
    create_premium_payment,
    get_premium_payment_by_id,
    get_all_premium_payments,
    get_payments_by_policy,
    get_payments_by_customer,
    get_payment_by_transaction_id,
    update_premium_payment,
    delete_premium_payment,
    search_premium_payments,
)


VALID_STATUS_TRANSITIONS = {
    "Pending": {
        "Completed",
        "Failed",
    },
    "Completed": {
        "Refunded",
    },
    "Failed": set(),
    "Refunded": set(),
}


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


def validate_customer_exists(
    db: Session,
    customer_id: int,
):
    customer = (
        db.query(Customer)
        .filter(
            Customer.id == customer_id
        )
        .first()
    )

    if not customer:
        raise LookupError(
            "Customer not found"
        )

    return customer


def validate_customer_policy(
    policy,
    customer_id: int,
):
    if policy.customer_id != customer_id:
        raise ValueError(
            "Customer does not belong to this policy"
        )


def validate_transaction_unique(
    db: Session,
    transaction_id: str,
    exclude_id: int | None = None,
):
    existing = get_payment_by_transaction_id(
        db,
        transaction_id,
    )

    if existing:
        if (
            exclude_id is None
            or existing.id != exclude_id
        ):
            raise ValueError(
                "Duplicate transaction is not allowed"
            )


def validate_payment_amount(
    policy,
    amount: Decimal,
):
    expected_amount = Decimal(
        str(policy.premium_amount)
    )

    if amount != expected_amount:
        raise ValueError(
            "Payment amount must match the expected premium"
        )


def validate_policy_payment_allowed(
    policy,
):
    if policy.policy_status == "Cancelled":
        raise ValueError(
            "Cancelled policy cannot receive premium payments"
        )


def create_premium_payment_service(
    db: Session,
    policy_id: int,
    data,
):
    policy = validate_policy_exists(
        db,
        policy_id,
    )

    customer = validate_customer_exists(
        db,
        data.customer_id,
    )

    validate_customer_policy(
        policy,
        customer.id,
    )

    validate_policy_payment_allowed(
        policy,
    )

    validate_transaction_unique(
        db,
        data.transaction_id,
    )

    validate_payment_amount(
        policy,
        data.amount,
    )

    payment = PremiumPayment(
        policy_id=policy_id,
        customer_id=data.customer_id,
        amount=data.amount,
        payment_date=data.payment_date,
        payment_method=data.payment_method,
        transaction_id=data.transaction_id,
        payment_status=data.payment_status,
        premium_due_date=data.premium_due_date,
    )

    return create_premium_payment(
        db,
        payment,
    )


def get_premium_payment_service(
    db: Session,
    payment_id: int,
):
    payment = get_premium_payment_by_id(
        db,
        payment_id,
    )

    if not payment:
        raise LookupError(
            "Premium payment not found"
        )

    return payment


def get_all_premium_payments_service(
    db: Session,
    payment_status=None,
    payment_method=None,
    date_from=None,
    date_to=None,
    page: int = 1,
    limit: int = 10,
    sort_by: str = "id",
    sort_order: str = "desc",
):
    payments, total = search_premium_payments(
        db=db,
        payment_status=payment_status,
        payment_method=payment_method,
        date_from=date_from,
        date_to=date_to,
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return {
        "success": True,
        "message": "Premium payments retrieved successfully",
        "data": payments,
        "total": total,
        "page": page,
        "limit": limit,
    }

def get_policy_premium_payments_service(
    db: Session,
    policy_id: int,
):
    validate_policy_exists(
        db,
        policy_id,
    )

    return get_payments_by_policy(
        db,
        policy_id,
    )


def get_customer_premium_payments_service(
    db: Session,
    customer_id: int,
):
    validate_customer_exists(
        db,
        customer_id,
    )

    return get_payments_by_customer(
        db,
        customer_id,
    )


def update_premium_payment_service(
    db: Session,
    payment_id: int,
    data,
):
    payment = get_premium_payment_by_id(
        db,
        payment_id,
    )

    if not payment:
        raise LookupError(
            "Premium payment not found"
        )

    update_data = data.model_dump(
        exclude_unset=True
    )

    if "amount" in update_data:
        policy = validate_policy_exists(
            db,
            payment.policy_id,
        )

        validate_payment_amount(
            policy,
            update_data["amount"],
        )

    if "payment_status" in update_data:
        current_status = payment.payment_status
        new_status = update_data["payment_status"]

        if new_status != current_status:
            allowed = VALID_STATUS_TRANSITIONS.get(
                current_status,
                set(),
            )

            if new_status not in allowed:
                raise ValueError(
                    f"Invalid payment status transition: "
                    f"{current_status} -> {new_status}"
                )

    for field, value in update_data.items():
        setattr(
            payment,
            field,
            value,
        )

    return update_premium_payment(
        db,
        payment,
    )


def delete_premium_payment_service(
    db: Session,
    payment_id: int,
):
    payment = get_premium_payment_by_id(
        db,
        payment_id,
    )

    if not payment:
        raise LookupError(
            "Premium payment not found"
        )

    delete_premium_payment(
        db,
        payment,
    )

    return True