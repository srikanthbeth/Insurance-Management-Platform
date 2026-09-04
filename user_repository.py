from sqlalchemy import select
from sqlalchemy.orm import Session

from models.refresh_token import RefreshToken
from models.user import User


def get_user_by_email(
    db: Session,
    email: str,
) -> User | None:
    statement = select(User).where(
        User.email == email
    )

    return db.scalar(statement)


def get_user_by_id(
    db: Session,
    user_id: int,
) -> User | None:
    statement = select(User).where(
        User.id == user_id
    )

    return db.scalar(statement)


def create_user(
    db: Session,
    user: User,
) -> User:
    db.add(user)
    db.flush()
    db.refresh(user)

    return user


def update_user(
    db: Session,
    user: User,
) -> User:
    db.add(user)
    db.flush()
    db.refresh(user)

    return user


def create_refresh_token(
    db: Session,
    refresh_token: RefreshToken,
) -> RefreshToken:
    db.add(refresh_token)
    db.flush()
    db.refresh(refresh_token)

    return refresh_token


def get_refresh_token(
    db: Session,
    token: str,
) -> RefreshToken | None:
    statement = select(RefreshToken).where(
        RefreshToken.token == token
    )

    return db.scalar(statement)

from sqlalchemy.orm import Session

from models.user import User


def get_user_by_id(
    db: Session,
    user_id: int,
):
    return (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )


def update_user_status(
    db: Session,
    user: User,
    is_active: bool,
):
    user.is_active = is_active

    db.commit()
    db.refresh(user)

    return user