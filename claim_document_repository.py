from sqlalchemy.orm import Session

from models.claim_document import ClaimDocument


def create_claim_document(
    db: Session,
    document: ClaimDocument,
):
    db.add(document)
    db.commit()
    db.refresh(document)

    return document


def get_claim_document_by_id(
    db: Session,
    document_id: int,
):
    return (
        db.query(ClaimDocument)
        .filter(
            ClaimDocument.id == document_id
        )
        .first()
    )


def get_claim_documents_by_claim(
    db: Session,
    claim_id: int,
):
    return (
        db.query(ClaimDocument)
        .filter(
            ClaimDocument.claim_id == claim_id
        )
        .order_by(
            ClaimDocument.id.desc()
        )
        .all()
    )


def update_claim_document(
    db: Session,
    document: ClaimDocument,
):
    db.commit()
    db.refresh(document)

    return document


def get_unverified_claim_documents(
    db: Session,
    claim_id: int,
):
    return (
        db.query(ClaimDocument)
        .filter(
            ClaimDocument.claim_id == claim_id,
            ClaimDocument.verification_status != "Verified",
        )
        .all()
    )