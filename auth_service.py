from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.refresh_token import RefreshToken
from models.user import User

from repositories.user_repository import (
    create_refresh_token,
    create_user,
    get_refresh_token,
    get_user_by_email,
    get_user_by_id,
    update_user_status,
)

from schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
)

from utils.jwt import (
    create_access_token,
    create_refresh_token as generate_refresh_token,
    decode_token,
)

from utils.security import (
    hash_password,
    verify_password,
)


# ============================================================
# REGISTER USER
# ============================================================

def register_user(
    db: Session,
    data: RegisterRequest,
) -> User:

    existing_user = get_user_by_email(
        db,
        data.email,
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        full_name=data.full_name.strip(),
        email=data.email.lower(),
        password_hash=hash_password(data.password),
        role=data.role,
        is_active=True,
    )

    create_user(db, user)

    db.commit()
    db.refresh(user)

    return user


# ============================================================
# LOGIN USER
# ============================================================

def login_user(
    db: Session,
    data: LoginRequest,
) -> dict:

    user = get_user_by_email(
        db,
        data.email.lower(),
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(
        data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    access_token = create_access_token(
        {
            "sub": str(user.id),
            "role": user.role.value,
        }
    )

    refresh_token, expires_at = (
        generate_refresh_token(
            {
                "sub": str(user.id),
                "role": user.role.value,
            }
        )
    )

    refresh_token_model = RefreshToken(
        user_id=user.id,
        token=refresh_token,
        expires_at=expires_at,
        is_revoked=False,
    )

    create_refresh_token(
        db,
        refresh_token_model,
    )

    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user,
    }


# ============================================================
# REFRESH ACCESS TOKEN
# ============================================================

def refresh_access_token(
    db: Session,
    refresh_token: str,
) -> dict:

    stored_token = get_refresh_token(
        db,
        refresh_token,
    )

    if not stored_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    if stored_token.is_revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked",
        )

    now = datetime.now(timezone.utc)

    expires_at = stored_token.expires_at

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(
            tzinfo=timezone.utc
        )

    if expires_at <= now:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
        )

    try:
        payload = decode_token(refresh_token)

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user = get_user_by_id(
        db,
        int(user_id),
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
        )

    access_token = create_access_token(
        {
            "sub": str(user.id),
            "role": user.role.value,
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


# ============================================================
# CHANGE PASSWORD
# ============================================================

def change_password(
    db: Session,
    user: User,
    data: ChangePasswordRequest,
) -> None:

    # --------------------------------------------------------
    # Verify current password
    # --------------------------------------------------------

    if not verify_password(
        data.current_password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # --------------------------------------------------------
    # New password must be different
    # --------------------------------------------------------

    if data.current_password == data.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different",
        )

    # --------------------------------------------------------
    # Hash and save new password
    # --------------------------------------------------------

    user.password_hash = hash_password(
        data.new_password
    )

    db.commit()


# ============================================================
# ACTIVATE / DEACTIVATE USER
# ============================================================

def change_user_status_service(
    db: Session,
    current_user: User,
    user_id: int,
    is_active: bool,
):
    # --------------------------------------------------------
    # Super Admin cannot deactivate themselves
    # --------------------------------------------------------

    if (
        current_user.id == user_id
        and not is_active
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Super Admin cannot deactivate "
                "their own account"
            ),
        )

    # --------------------------------------------------------
    # Find target user
    # --------------------------------------------------------

    user = get_user_by_id(
        db,
        user_id,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # --------------------------------------------------------
    # Update status
    # --------------------------------------------------------

    return update_user_status(
        db,
        user,
        is_active,
    )