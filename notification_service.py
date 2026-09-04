from sqlalchemy.orm import Session

from models.notification import Notification

from repositories.notification import (
    create_notification,
    get_notification_by_id,
    get_user_notifications,
    mark_notification_as_read,
)


def create_notification_service(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    notification_type: str,
):
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
        is_read=False,
    )

    return create_notification(
        db,
        notification,
    )


def get_user_notifications_service(
    db: Session,
    user_id: int,
):
    notifications = get_user_notifications(
        db,
        user_id,
    )

    return {
        "success": True,
        "message": "Notifications retrieved successfully",
        "data": notifications,
        "total": len(notifications),
    }


def mark_notification_as_read_service(
    db: Session,
    notification_id: int,
    user_id: int,
):
    notification = get_notification_by_id(
        db,
        notification_id,
    )

    if not notification:
        raise LookupError("Notification not found")

    if notification.user_id != user_id:
        raise PermissionError(
            "You are not authorized to update this notification"
        )

    return mark_notification_as_read(
        db,
        notification,
    )