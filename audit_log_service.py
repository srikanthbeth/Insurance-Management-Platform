from sqlalchemy.orm import Session

from models.audit_log import AuditLog

from repositories.audit_log import (
    create_audit_log,
    get_all_audit_logs,
    get_audit_log_by_id,
    get_audit_logs_by_user,
)


def create_audit_log_service(
    db: Session,
    user_id: int | None,
    action: str,
    entity_type: str,
    entity_id: int | None,
    description: str,
):
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
    )

    return create_audit_log(
        db,
        audit_log,
    )


def get_audit_logs_service(
    db: Session,
):
    logs = get_all_audit_logs(db)

    return {
        "success": True,
        "data": logs,
        "total": len(logs),
    }


def get_audit_log_service(
    db: Session,
    audit_log_id: int,
):
    log = get_audit_log_by_id(
        db,
        audit_log_id,
    )

    if not log:
        raise LookupError(
            "Audit log not found"
        )

    return log


def get_user_audit_logs_service(
    db: Session,
    user_id: int,
):
    logs = get_audit_logs_by_user(
        db,
        user_id,
    )

    return {
        "success": True,
        "data": logs,
        "total": len(logs),
    }