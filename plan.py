from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from models.plan import PlanStatus, PlanType


class PlanCreate(BaseModel):
    plan_name: str = Field(
        ...,
        min_length=2,
        max_length=150,
    )

    plan_type: PlanType

    description: str | None = None

    coverage_amount: Decimal = Field(
        ...,
        gt=0,
    )

    premium_amount: Decimal = Field(
        ...,
        gt=0,
    )

    duration_years: int = Field(
        ...,
        gt=0,
    )

    eligibility_age_min: int = Field(
        ...,
        ge=0,
    )

    eligibility_age_max: int = Field(
        ...,
        ge=0,
    )

    @field_validator("plan_name")
    @classmethod
    def validate_plan_name(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "Plan name cannot be empty"
            )

        return value

    @field_validator("eligibility_age_max")
    @classmethod
    def validate_age_range(
        cls,
        value: int,
        info,
    ) -> int:
        min_age = info.data.get(
            "eligibility_age_min"
        )

        if min_age is not None and value <= min_age:
            raise ValueError(
                "Maximum eligibility age must be greater than minimum eligibility age"
            )

        return value


class PlanUpdate(BaseModel):
    plan_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    plan_type: PlanType | None = None

    description: str | None = None

    coverage_amount: Decimal | None = Field(
        default=None,
        gt=0,
    )

    premium_amount: Decimal | None = Field(
        default=None,
        gt=0,
    )

    duration_years: int | None = Field(
        default=None,
        gt=0,
    )

    eligibility_age_min: int | None = Field(
        default=None,
        ge=0,
    )

    eligibility_age_max: int | None = Field(
        default=None,
        ge=0,
    )

    status: PlanStatus | None = None

    @field_validator("plan_name")
    @classmethod
    def validate_plan_name(cls, value):
        if value is None:
            return value

        value = value.strip()

        if not value:
            raise ValueError(
                "Plan name cannot be empty"
            )

        return value


class PlanResponse(BaseModel):
    id: int
    plan_name: str
    plan_type: PlanType
    description: str | None
    coverage_amount: Decimal
    premium_amount: Decimal
    duration_years: int
    eligibility_age_min: int
    eligibility_age_max: int
    status: PlanStatus

    model_config = ConfigDict(
        from_attributes=True
    )


class PlanListResponse(BaseModel):
    success: bool = True
    message: str = "Plans retrieved successfully"
    data: list[PlanResponse]
    total: int