import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...core.audit import log_audit
from ...core.database import get_db
from ...core.deps import get_current_user
from ...core.security import (
    InvalidTokenError,
    TokenType,
    create_access_token,
    create_refresh_token,
    create_reset_token,
    decode_token,
    hash_password,
    verify_password,
)
from ...models.user import User, UserRole
from ...schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserOut,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _token_response(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(str(user.id), user.role.value),
        refresh_token=create_refresh_token(str(user.id)),
        user=UserOut.model_validate(user),
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter_by(email=payload.email.lower()).one_or_none()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists")

    user = User(
        email=payload.email.lower(),
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        organization=payload.organization,
        role=UserRole.VIEWER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    log_audit(db, action="register", resource_type="user", user_id=user.id, resource_id=str(user.id))
    return _token_response(user)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=payload.email.lower()).one_or_none()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")
    log_audit(db, action="login", resource_type="user", user_id=user.id, resource_id=str(user.id))
    return _token_response(user)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    try:
        claims = decode_token(payload.refresh_token, TokenType.REFRESH)
    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")
    user = db.get(User, uuid.UUID(claims["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return _token_response(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # JWTs are stateless and access tokens are short-lived; logout is a
    # client-side action (discard tokens). Nothing server-side to revoke
    # for this demo's scope.
    log_audit(db, action="logout", resource_type="user", user_id=user.id, resource_id=str(user.id))
    return None


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=payload.email.lower()).one_or_none()
    # Always return 200 regardless of whether the email exists, to avoid
    # leaking account existence.
    if user is None:
        return {"message": "If that email is registered, a reset link has been issued."}

    reset_token = create_reset_token(str(user.id))
    return {
        "message": "Password reset token issued.",
        "demo_note": (
            "No email provider is configured in this deployment, so the reset "
            "token is returned directly here instead of being emailed. In a "
            "production deployment this would be sent to the user's inbox."
        ),
        "reset_token": reset_token,
    }


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    try:
        claims = decode_token(payload.token, TokenType.RESET)
    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")
    user = db.get(User, uuid.UUID(claims["sub"]))
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reset token")
    user.hashed_password = hash_password(payload.new_password)
    db.commit()
    return None


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
