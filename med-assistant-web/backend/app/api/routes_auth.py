from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app import models, deps
from app.schemas.user import UserCreate, UserLogin, UserOut, UserChangePassword
from app.auth import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/signup", response_model=UserOut)
def signup(user_in: UserCreate, db: Session = Depends(get_db)):
    existing = (
        db.query(models.user.User)
        .filter(models.user.User.email == user_in.email)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = models.user.User(
        name=user_in.name,
        email=user_in.email,
        role="doctor",
        hashed_password=hash_password(user_in.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login")
def login(user_in: UserLogin, response: Response, db: Session = Depends(get_db)):
    user = (
        db.query(models.user.User)
        .filter(models.user.User.email == user_in.email)
        .first()
    )
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    token = create_access_token({"sub": str(user.id)})
    
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=86400 * 7,
        samesite="lax",
    )
    response.set_cookie(
        key="logged_in",
        value="1",
        httponly=False,
        max_age=86400 * 7,
        samesite="lax",
    )
    return {"access_token": token, "token_type": "bearer"}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("logged_in")
    return {"message": "Logged out"}


@router.get("/me", response_model=UserOut)
def get_me(current_user: models.user.User = Depends(deps.get_current_user)):
    return current_user


@router.post("/change-password")
def change_password(
    data: UserChangePassword,
    db: Session = Depends(get_db),
    current_user: models.user.User = Depends(deps.get_current_user)
):
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password",
        )
    
    # Re-fetch the user to bind it to the local db session, allowing commit to succeed
    user = db.query(models.user.User).filter(models.user.User.id == current_user.id).first()
    user.hashed_password = hash_password(data.new_password)
    db.commit()
    return {"message": "Password changed successfully"}


@router.delete("/me")
def delete_account(
    response: Response,
    db: Session = Depends(get_db),
    current_user: models.user.User = Depends(deps.get_current_user)
):
    # Re-fetch user to local session for deletion
    user = db.query(models.user.User).filter(models.user.User.id == current_user.id).first()
    db.delete(user)
    db.commit()
    
    # Clean up cookies
    response.delete_cookie("access_token")
    response.delete_cookie("logged_in")
    return {"message": "Account deleted successfully"}
