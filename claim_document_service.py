import os
import uuid

from fastapi import UploadFile
from sqlalchemy.orm import Session

from models.claim_document import ClaimDocument
from repositories.claim_document_repository import (
    create_claim_document,
    get_claim_document_by_id,
    get_claim_documents_by_claim,
    update_claim_document,
)
from services.claim_service import (
    validate_policy_exists,
)


ALLOWED_DOCUMENT_TYPES = {
    "ID Proof",
    "Invoice",
    "Medical Report",
    "FIR",
    "Repair Estimate",
    "Other",
}


ALLOWED_FILE_EXTENSIONS = {
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png",
}


UPLOAD_DIRECTORY = "uploads/claim_documents"


def create_claim_document_service(
    db: Session,
    claim_id: int,
    document_type: str,
    file: UploadFile,
):
    # Import here to avoid circular import issues
    from models.claim import Claim

    claim = (
        db.query(Claim)
        .filter(
            Claim.id == claim_id
        )
        .first()
    )

    if not claim:
        raise LookupError(
            "Claim not found"
        )

    if document_type not in ALLOWED_DOCUMENT_TYPES:
        raise ValueError(
            "Invalid document type"
        )

    original_filename = file.filename

    if not original_filename:
        raise ValueError(
            "File name is required"
        )

    extension = os.path.splitext(
        original_filename
    )[1].lower()

    if extension not in ALLOWED_FILE_EXTENSIONS:
        raise ValueError(
            "File type not allowed. "
            "Only PDF, JPG, JPEG and PNG files are allowed"
        )

    os.makedirs(
        UPLOAD_DIRECTORY,
        exist_ok=True,
    )

    unique_filename = (
        f"{uuid.uuid4().hex}"
        f"{extension}"
    )

    file_path = os.path.join(
        UPLOAD_DIRECTORY,
        unique_filename,
    )

    try:
        with open(
            file_path,
            "wb",
        ) as buffer:
            while True:
                chunk = file.file.read(1024 * 1024)

                if not chunk:
                    break

                buffer.write(chunk)

    except Exception:
        raise ValueError(
            "Failed to save uploaded file"
        )

    document = ClaimDocument(
        claim_id=claim_id,
        document_type=document_type,
        file_name=original_filename,
        file_path=file_path,
        verification_status="Pending",
    )

    return create_claim_document(
        db,
        document,
    )


def get_claim_documents_service(
    db: Session,
    claim_id: int,
):
    from models.claim import Claim

    claim = (
        db.query(Claim)
        .filter(
            Claim.id == claim_id
        )
        .first()
    )

    if not claim:
        raise LookupError(
            "Claim not found"
        )

    return get_claim_documents_by_claim(
        db,
        claim_id,
    )


def verify_claim_document_service(
    db: Session,
    document_id: int,
    verification_status: str,
):
    document = get_claim_document_by_id(
        db,
        document_id,
    )

    if not document:
        raise LookupError(
            "Document not found"
        )

    if verification_status not in {
        "Verified",
        "Rejected",
    }:
        raise ValueError(
            "Invalid verification status"
        )

    document.verification_status = (
        verification_status
    )

    return update_claim_document(
        db,
        document,
    )