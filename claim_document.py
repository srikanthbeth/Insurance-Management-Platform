from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
)


VALID_DOCUMENT_TYPES = {
    "ID Proof",
    "Invoice",
    "Medical Report",
    "FIR",
    "Repair Estimate",
    "Other",
}


VALID_VERIFICATION_STATUSES = {
    "Pending",
    "Verified",
    "Rejected",
}


class ClaimDocumentResponse(BaseModel):
    id: int
    claim_id: int
    document_type: str
    file_name: str
    file_path: str
    uploaded_at: datetime
    verification_status: str

    model_config = ConfigDict(
        from_attributes=True
    )