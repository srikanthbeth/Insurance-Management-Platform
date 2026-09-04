from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Claim(Base):
    __tablename__ = "claims"

    __table_args__ = (
        UniqueConstraint(
            "claim_number",
            name="uq_claim_claim_number",
        ),
        UniqueConstraint(
            "policy_id",
            "incident_date",
            name="uq_claim_policy_incident",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    claim_number: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    policy_id: Mapped[int] = mapped_column(
        ForeignKey("policies.id"),
        nullable=False,
        index=True,
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id"),
        nullable=False,
        index=True,
    )

    claim_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    incident_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    claim_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="Submitted",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    policy = relationship(
        "Policy",
        back_populates="claims",
    )

    customer = relationship(
        "Customer",
        back_populates="claims",
    )

    documents = relationship(
        "ClaimDocument",
        back_populates="claim",
        cascade="all, delete-orphan",
    )

    assessment = relationship(
        "ClaimAssessment",
        back_populates="claim",
        uselist=False,
        cascade="all, delete-orphan",
    )

    settlement = relationship(
    "Settlement",
    back_populates="claim",
    uselist=False,
    cascade="all, delete-orphan",
)