from sqlalchemy import Column, Integer, String, Numeric, ForeignKey
from sqlalchemy.orm import relationship as sa_relationship

from database import Base


class Beneficiary(Base):
    __tablename__ = "beneficiaries"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    policy_id = Column(
        Integer,
        ForeignKey("policies.id"),
        nullable=False,
    )

    name = Column(
        String(100),
        nullable=False,
    )

    relationship = Column(
        String(50),
        nullable=False,
    )

    percentage = Column(
        Numeric(5, 2),
        nullable=False,
    )

    phone = Column(
        String(20),
        nullable=False,
    )

    identification_number = Column(
        String(50),
        nullable=False,
    )

    policy = sa_relationship(
        "Policy",
        back_populates="beneficiaries",
    )