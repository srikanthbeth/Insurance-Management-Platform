from sqlalchemy import select
from sqlalchemy.orm import Session

from models.notification import Notification


def create_notification(
    db: Session,
    notification: Notification,
):
    db.add(notification)
    db.commit()
    db.refresh(notification)

    return notification


def get_user_notifications(
    db: Session,
    user_id: int,
):
    statement = (
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.id.desc())
    )

    return db.scalars(statement).all()


def get_notification_by_id(
    db: Session,
    notification_id: int,
):
    statement = select(Notification).where(
        Notification.id == notification_id
    )

    return db.scalar(statement)


def mark_notification_as_read(
    db: Session,
    notification: Notification,
):
    notification.is_read = True

    db.commit()
    db.refresh(notification)

    return notification