from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class CustomerCreate(BaseModel):
    full_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    email: EmailStr

    phone: str = Field(
        ...,
        min_length=10,
        max_length=15,
    )

    date_of_birth: date

    address: str = Field(
        ...,
        min_length=5,
        max_length=500,
    )

    identification_number: str = Field(
        ...,
        min_length=3,
        max_length=100,
    )

    occupation: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str):
        value = value.strip()

        if len(value) < 2:
            raise ValueError(
                "Full name must contain at least 2 characters"
            )

        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str):
        value = value.strip()

        if not value.isdigit():
            raise ValueError(
                "Phone number must contain only digits"
            )

        if len(value) < 10 or len(value) > 15:
            raise ValueError(
                "Phone number must be between 10 and 15 digits"
            )

        return value

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, value: date):
        today = date.today()

        if value >= today:
            raise ValueError(
                "Date of birth must be in the past"
            )

        age = (
            today.year
            - value.year
            - (
                (today.month, today.day)
                < (value.month, value.day)
            )
        )

        if age < 18:
            raise ValueError(
                "Customer must be at least 18 years old"
            )

        if age > 100:
            raise ValueError(
                "Customer age cannot exceed 100 years"
            )

        return value


class CustomerUpdate(BaseModel):
    full_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    email: EmailStr | None = None

    phone: str | None = Field(
        default=None,
        min_length=10,
        max_length=15,
    )

    date_of_birth: date | None = None

    address: str | None = Field(
        default=None,
        min_length=5,
        max_length=500,
    )

    identification_number: str | None = Field(
        default=None,
        min_length=3,
        max_length=100,
    )

    occupation: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value):
        if value is None:
            return value

        value = value.strip()

        if len(value) < 2:
            raise ValueError(
                "Full name must contain at least 2 characters"
            )

        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value):
        if value is None:
            return value

        value = value.strip()

        if not value.isdigit():
            raise ValueError(
                "Phone number must contain only digits"
            )

        if len(value) < 10 or len(value) > 15:
            raise ValueError(
                "Phone number must be between 10 and 15 digits"
            )

        return value

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, value):
        if value is None:
            return value

        today = date.today()

        if value >= today:
            raise ValueError(
                "Date of birth must be in the past"
            )

        age = (
            today.year
            - value.year
            - (
                (today.month, today.day)
                < (value.month, value.day)
            )
        )

        if age < 18:
            raise ValueError(
                "Customer must be at least 18 years old"
            )

        if age > 100:
            raise ValueError(
                "Customer age cannot exceed 100 years"
            )

        return value


class CustomerResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    phone: str
    date_of_birth: date
    address: str
    identification_number: str
    occupation: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class CustomerListResponse(BaseModel):
    success: bool = True
    data: list[CustomerResponse]