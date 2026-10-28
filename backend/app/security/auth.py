import os
import datetime
import bcrypt
import jwt
from typing import Optional
from fastapi import Header, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.db.session import get_db
from backend.app.models.models import User

DEFAULT_DEV_USER_ID = "00000000-0000-0000-0000-000000000001"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7

bearer_scheme = HTTPBearer(auto_error=False)

def hash_password(password: str) -> str:
    """Hashes a plaintext password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against a stored bcrypt hash."""
    if not hashed_password:
        return False
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def create_access_token(user_id: str, email: Optional[str] = None, expires_delta: Optional[datetime.timedelta] = None) -> str:
    """Generates a signed JWT access token."""
    expire = datetime.datetime.now(datetime.timezone.utc) + (expires_delta or datetime.timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS))
    payload = {
        "sub": user_id,
        "email": email,
        "exp": expire,
        "iat": datetime.datetime.now(datetime.timezone.utc)
    }
    encoded_jwt = jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """Decodes and validates a JWT access token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None

def get_current_user(
    auth_credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db)
) -> User:
    """
    Authenticates user via:
    1. Authorization: Bearer <jwt_token>
    2. X-User-Id header (for developer API testing)
    3. Auto-provisioned Guest User (for instant exploratory studio use)
    """
    # 1. Check Bearer Token
    if auth_credentials and auth_credentials.credentials:
        token = auth_credentials.credentials
        payload = decode_access_token(token)
        if not payload or "sub" not in payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired authentication token.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_id = payload["sub"]
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account associated with token not found.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if user.account_status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is suspended or inactive."
            )
        return user

    # 2. Check X-User-Id header
    if x_user_id and x_user_id.strip():
        user_id = x_user_id.strip()
        user = db.query(User).filter((User.id == user_id) | (User.auth_provider_id == user_id)).first()
        if not user:
            user = User(
                id=user_id if len(user_id) == 36 else None,
                auth_provider_id=user_id,
                username=f"User_{user_id[:6]}",
                account_status="active"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    # 3. Default Guest / Explorer User
    guest_user = db.query(User).filter(User.auth_provider_id == DEFAULT_DEV_USER_ID).first()
    if not guest_user:
        guest_user = User(
            id=DEFAULT_DEV_USER_ID,
            auth_provider_id=DEFAULT_DEV_USER_ID,
            username="Guest Studio User",
            account_status="active"
        )
        db.add(guest_user)
        db.commit()
        db.refresh(guest_user)

    return guest_user

def verify_ownership(resource_owner_id: str, user: User, resource_type: str = "resource"):
    """Enforces strict multi-tenant authorization."""
    if resource_owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: you do not have permission to view or modify this {resource_type}."
        )
