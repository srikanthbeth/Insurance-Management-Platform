from sqlalchemy.orm import Session

from models.audit_log import AuditLog


def create_audit_log(
    db: Session,
    audit_log: AuditLog,
):
    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)

    return audit_log


def get_all_audit_logs(
    db: Session,
):
    return (
        db.query(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .all()
    )


def get_audit_log_by_id(
    db: Session,
    audit_log_id: int,
):
    return (
        db.query(AuditLog)
        .filter(
            AuditLog.id == audit_log_id
        )
        .first()
    )


def get_audit_logs_by_user(
    db: Session,
    user_id: int,
):
    return (
        db.query(AuditLog)
        .filter(
            AuditLog.user_id == user_id
        )
        .order_by(
            AuditLog.created_at.desc()
        )
        .all()
    )