"""Authentication and current-user endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..auth import create_access_token, get_current_user, hash_password, verify_password
from ..database import get_db

router = APIRouter(tags=["auth"])


@router.post("/signup", response_model=schemas.MessageResponse, status_code=status.HTTP_201_CREATED)
@router.post("/register", response_model=schemas.MessageResponse, status_code=status.HTTP_201_CREATED)
@router.post("/auth/signup", response_model=schemas.MessageResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: schemas.UserSignupRequest, db: Session = Depends(get_db)):
    """Create a user account with bcrypt password hash."""
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = models.User(email=payload.email, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    return schemas.MessageResponse(message="User registered successfully")


@router.post("/login", response_model=schemas.TokenResponse)
@router.post("/auth/login", response_model=schemas.TokenResponse)
def login(payload: schemas.UserLoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return JWT token."""
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token({"sub": str(user.id)})
    return schemas.TokenResponse(access_token=token, token_type="bearer")


@router.get("/me", response_model=schemas.UserResponse)
def me(current_user: models.User = Depends(get_current_user)):
    """Return authenticated user profile."""
    return current_user
