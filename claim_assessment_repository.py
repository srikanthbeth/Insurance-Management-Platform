from sqlalchemy.orm import Session

from models.claim_assessment import ClaimAssessment


def create_claim_assessment(
    db: Session,
    assessment: ClaimAssessment,
):
    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    return assessment


def get_claim_assessment_by_claim(
    db: Session,
    claim_id: int,
):
    return (
        db.query(ClaimAssessment)
        .filter(
            ClaimAssessment.claim_id == claim_id
        )
        .first()
    )


def get_claim_assessment_by_id(
    db: Session,
    assessment_id: int,
):
    return (
        db.query(ClaimAssessment)
        .filter(
            ClaimAssessment.id == assessment_id
        )
        .first()
    )