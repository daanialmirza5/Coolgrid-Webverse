from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.deps import get_current_user
from ...core.security import hash_password, verify_password
from ...models.user import User
from ...schemas.auth import UserOut
from ...schemas.user import ChangePasswordRequest, UpdateProfileRequest

router = APIRouter(prefix="/users", tags=["users"], dependencies=[Depends(get_current_user)])


@router.patch("/me", response_model=UserOut)
def update_profile(payload: UpdateProfileRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.organization is not None:
        user.organization = payload.organization
    db.commit()
    db.refresh(user)
    return user


@router.post("/me/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(payload: ChangePasswordRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not verify_password(payload.current_password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
    user.hashed_password = hash_password(payload.new_password)
    db.commit()
    return None
