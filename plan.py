from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from sqlalchemy.orm import relationship

from sqlalchemy import (
    DateTime,
    Enum as SQLEnum,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class PlanType(str, Enum):
    LIFE = "Life"
    HEALTH = "Health"
    VEHICLE = "Vehicle"
    PROPERTY = "Property"
    TRAVEL = "Travel"


class PlanStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"


class InsurancePlan(Base):
    __tablename__ = "insurance_plans"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    plan_name: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        nullable=False,
        index=True,
    )

    plan_type: Mapped[PlanType] = mapped_column(
        SQLEnum(PlanType),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    coverage_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    premium_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    duration_years: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    eligibility_age_min: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    eligibility_age_max: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    status: Mapped[PlanStatus] = mapped_column(
        SQLEnum(PlanStatus),
        nullable=False,
        default=PlanStatus.ACTIVE,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    policies = relationship(
    "Policy",
    back_populates="plan",
)