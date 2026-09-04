from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class BeneficiaryCreate(BaseModel):
    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    relationship: str = Field(
        ...,
        min_length=2,
        max_length=50,
    )

    percentage: Decimal = Field(
        ...,
        gt=0,
        le=100,
    )

    phone: str = Field(
        ...,
        min_length=10,
        max_length=20,
    )

    identification_number: str = Field(
        ...,
        min_length=3,
        max_length=50,
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        value = value.strip()

        if not value:
            raise ValueError(
                "Beneficiary name cannot be empty"
            )

        return value

    @field_validator("relationship")
    @classmethod
    def validate_relationship(cls, value):
        value = value.strip()

        if not value:
            raise ValueError(
                "Relationship cannot be empty"
            )

        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value):
        value = value.strip()

        if not value:
            raise ValueError(
                "Phone cannot be empty"
            )

        if not value.isdigit():
            raise ValueError(
                "Phone must contain only digits"
            )

        return value

    @field_validator("identification_number")
    @classmethod
    def validate_identification_number(cls, value):
        value = value.strip()

        if not value:
            raise ValueError(
                "Identification number cannot be empty"
            )

        return value


class BeneficiaryUpdate(BaseModel):
    name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    relationship: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=50,
    )

    percentage: Optional[Decimal] = Field(
        default=None,
        gt=0,
        le=100,
    )

    phone: Optional[str] = Field(
        default=None,
        min_length=10,
        max_length=20,
    )

    identification_number: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=50,
    )


class BeneficiaryResponse(BaseModel):
    id: int
    policy_id: int
    name: str
    relationship: str
    percentage: Decimal
    phone: str
    identification_number: str

    class Config:
        from_attributes = True