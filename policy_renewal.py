from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class PolicyRenewal(Base):
    __tablename__ = "policy_renewals"

    __table_args__ = (
        UniqueConstraint(
            "previous_policy_id",
            name="uq_policy_renewal_previous_policy",
        ),
        UniqueConstraint(
            "new_policy_id",
            name="uq_policy_renewal_new_policy",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    previous_policy_id: Mapped[int] = mapped_column(
        ForeignKey("policies.id"),
        nullable=False,
        index=True,
    )

    new_policy_id: Mapped[int] = mapped_column(
        ForeignKey("policies.id"),
        nullable=False,
        index=True,
    )

    previous_start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    previous_end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    new_start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    new_end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    renewal_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    renewal_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="Completed",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    # ---------------------------------------------------------
    # Previous / Old Policy
    # ---------------------------------------------------------

    previous_policy = relationship(
        "Policy",
        foreign_keys=[previous_policy_id],
        back_populates="previous_renewals",
    )

    # ---------------------------------------------------------
    # New / Renewed Policy
    # ---------------------------------------------------------

    new_policy = relationship(
        "Policy",
        foreign_keys=[new_policy_id],
        back_populates="renewal_record",
        uselist=False,
    )