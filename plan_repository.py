from sqlalchemy.orm import Session

from models.plan import InsurancePlan


def create_plan(
    db: Session,
    plan: InsurancePlan,
) -> InsurancePlan:

    db.add(plan)
    db.flush()

    return plan


def get_plan_by_id(
    db: Session,
    plan_id: int,
) -> InsurancePlan | None:

    return (
        db.query(InsurancePlan)
        .filter(
            InsurancePlan.id == plan_id
        )
        .first()
    )


def get_plan_by_name(
    db: Session,
    plan_name: str,
) -> InsurancePlan | None:

    return (
        db.query(InsurancePlan)
        .filter(
            InsurancePlan.plan_name == plan_name
        )
        .first()
    )


def get_all_plans(
    db: Session,
) -> list[InsurancePlan]:

    return (
        db.query(InsurancePlan)
        .order_by(InsurancePlan.id.desc())
        .all()
    )


def update_plan(
    db: Session,
    plan: InsurancePlan,
) -> InsurancePlan:

    db.flush()

    return plan


def delete_plan(
    db: Session,
    plan: InsurancePlan,
) -> None:

    db.delete(plan)
    db.flush()