from datetime import date, datetime

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import relationship

from database import Base


class PremiumPayment(Base):
    __tablename__ = "premium_payments"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    policy_id = Column(
        Integer,
        ForeignKey("policies.id"),
        nullable=False,
        index=True,
    )

    customer_id = Column(
        Integer,
        ForeignKey("customers.id"),
        nullable=False,
        index=True,
    )

    amount = Column(
        Numeric(12, 2),
        nullable=False,
    )

    payment_date = Column(
        Date,
        nullable=False,
        default=date.today,
    )

    payment_method = Column(
        String(50),
        nullable=False,
    )

    transaction_id = Column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )

    payment_status = Column(
        String(30),
        nullable=False,
        default="Pending",
    )

    premium_due_date = Column(
        Date,
        nullable=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    policy = relationship(
        "Policy",
        back_populates="premium_payments",
    )

    customer = relationship(
        "Customer",
        back_populates="premium_payments",
    )