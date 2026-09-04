from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


VALID_RECOMMENDATIONS = {
    "Approved",
    "Partially Approved",
    "Rejected",
}


class ClaimAssessmentCreate(BaseModel):
    eligible_amount: Decimal = Field(
        gt=0,
    )

    assessment_notes: str = Field(
        min_length=5,
    )

    recommendation: str


class ClaimAssessmentResponse(BaseModel):
    id: int
    claim_id: int
    assessor_id: int
    eligible_amount: Decimal
    assessment_notes: str
    recommendation: str
    assessed_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )