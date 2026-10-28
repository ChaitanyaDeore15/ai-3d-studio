from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.db.session import get_db
from backend.app.models.models import User
from backend.app.schemas.schemas import UserRegisterRequest, UserLoginRequest, TokenResponse, UserResponse
from backend.app.security.auth import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter()

@router.post("/auth/register", response_model=TokenResponse)
def register_user(
    data: UserRegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Registers a new user account with secure password hashing.
    Enforces unique emails and usernames.
    """
    clean_email = data.email.strip().lower()
    clean_username = data.username.strip().lower()

    # Check existing email
    existing_email = db.query(User).filter(func.lower(User.email) == clean_email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    # Check existing username
    existing_user = db.query(User).filter(func.lower(User.username) == clean_username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This username is already taken. Please choose another."
        )

    # Create user
    pw_hash = hash_password(data.password)
    user = User(
        auth_provider_id=f"local_{clean_email}",
        email=clean_email,
        username=data.username.strip(),
        hashed_password=pw_hash,
        account_status="active"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user_id=user.id, email=user.email)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )

@router.post("/auth/login", response_model=TokenResponse)
def login_user(
    data: UserLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticates user with email/username and password.
    Returns signed JWT access token.
    """
    identifier = data.email_or_username.strip().lower()

    user = db.query(User).filter(
        (func.lower(User.email) == identifier) | (func.lower(User.username) == identifier)
    ).first()

    if not user or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email/username or password."
        )

    if not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email/username or password."
        )

    if user.account_status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated."
        )

    token = create_access_token(user_id=user.id, email=user.email)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )

@router.get("/auth/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Returns the authenticated user profile."""
    return UserResponse.model_validate(current_user)
