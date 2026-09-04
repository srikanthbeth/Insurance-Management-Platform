from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models.plan import InsurancePlan
from models.user import User
from repositories.plan_repository import (
    create_plan,
    delete_plan,
    get_all_plans,
    get_plan_by_id,
    get_plan_by_name,
    update_plan,
)
from schemas.plan import PlanCreate, PlanUpdate


def create_plan_service(
    db: Session,
    data: PlanCreate,
) -> InsurancePlan:

    existing_plan = get_plan_by_name(
        db,
        data.plan_name,
    )

    if existing_plan:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Plan name already exists",
        )

    if (
        data.eligibility_age_max
        <= data.eligibility_age_min
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Maximum eligibility age must be greater "
                "than minimum eligibility age"
            ),
        )

    plan = InsurancePlan(
        plan_name=data.plan_name.strip(),
        plan_type=data.plan_type,
        description=data.description,
        coverage_amount=data.coverage_amount,
        premium_amount=data.premium_amount,
        duration_years=data.duration_years,
        eligibility_age_min=data.eligibility_age_min,
        eligibility_age_max=data.eligibility_age_max,
    )

    try:
        create_plan(db, plan)
        db.commit()
        db.refresh(plan)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Plan name already exists",
        )

    return plan


def get_plan_service(
    db: Session,
    plan_id: int,
) -> InsurancePlan:

    plan = get_plan_by_id(
        db,
        plan_id,
    )

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found",
        )

    return plan


def get_all_plans_service(
    db: Session,
) -> list[InsurancePlan]:

    return get_all_plans(db)


def update_plan_service(
    db: Session,
    plan_id: int,
    data: PlanUpdate,
) -> InsurancePlan:

    plan = get_plan_by_id(
        db,
        plan_id,
    )

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found",
        )

    update_data = data.model_dump(
        exclude_unset=True
    )

    if "plan_name" in update_data:

        plan_name = update_data["plan_name"].strip()

        existing_plan = get_plan_by_name(
            db,
            plan_name,
        )

        if (
            existing_plan
            and existing_plan.id != plan.id
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Plan name already exists",
            )

        update_data["plan_name"] = plan_name

    min_age = update_data.get(
        "eligibility_age_min",
        plan.eligibility_age_min,
    )

    max_age = update_data.get(
        "eligibility_age_max",
        plan.eligibility_age_max,
    )

    if max_age <= min_age:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Maximum eligibility age must be greater "
                "than minimum eligibility age"
            ),
        )

    for field, value in update_data.items():
        setattr(
            plan,
            field,
            value,
        )

    try:
        update_plan(db, plan)
        db.commit()
        db.refresh(plan)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Plan name already exists",
        )

    return plan


def delete_plan_service(
    db: Session,
    plan_id: int,
    current_user: User,
) -> dict:

    plan = get_plan_by_id(
        db,
        plan_id,
    )

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found",
        )

    if current_user.role.value != "Super Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You do not have permission to delete plans"
            ),
        )

    delete_plan(
        db,
        plan,
    )

    db.commit()

    return {
        "success": True,
        "message": "Plan deleted successfully",
    }