"""
auth.py  (router)
=================
POST /auth/register  — register a new user
POST /auth/login     — JWT login
GET  /auth/me        — current user profile
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr

_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

from database.connection import get_db
from database.models import User, UserRole
from config.settings import get_settings
from config.logging_config import get_logger

logger   = get_logger("backend.routers.auth")
settings = get_settings()
router   = APIRouter()

import bcrypt

_oauth2  = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------
class RegisterRequest(BaseModel):
    """Registration request body."""
    username: str
    email:    EmailStr
    password: str
    role:     UserRole = UserRole.USER


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    token_type:   str = "bearer"
    username:     str
    role:         str


class UserProfile(BaseModel):
    """Current user profile."""
    id:       int
    username: str
    email:    str
    role:     str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
import hashlib
import os

def _hash_password(password: str) -> str:
    """Hash password using bcrypt with fallback to hashlib pbkdf2_hmac."""
    try:
        pwd_bytes = password.encode('utf-8')[:72]
        salt = bcrypt.gensalt()
        return "bcrypt$" + bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')
    except Exception:
        salt = os.urandom(16)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return "pbkdf2$" + salt.hex() + "$" + pwd_hash.hex()


def _verify_password(plain: str, hashed: str) -> bool:
    """Verify password against bcrypt or pbkdf2 hash."""
    try:
        if hashed.startswith("pbkdf2$"):
            parts = hashed.split("$")
            if len(parts) == 3:
                salt = bytes.fromhex(parts[1])
                check_hash = hashlib.pbkdf2_hmac('sha256', plain.encode('utf-8'), salt, 100000)
                return check_hash.hex() == parts[2]
            return False
        
        raw_hash = hashed.replace("bcrypt$", "") if hashed.startswith("bcrypt$") else hashed
        pwd_bytes = plain.encode('utf-8')[:72]
        return bcrypt.checkpw(pwd_bytes, raw_hash.encode('utf-8'))
    except Exception:
        return False


def _create_token(username: str, role: str) -> str:
    """
    Generate a signed JWT access token.

    Args:
        username: Subject claim.
        role:     User role claim.

    Returns:
        Encoded JWT string.
    """
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": username, "role": role, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def get_current_user(token: str = Depends(_oauth2), db: Session = Depends(get_db)) -> User:
    """
    Dependency: decode the JWT and return the current user from DB.

    Args:
        token: Bearer token from Authorization header.
        db:    Database session.

    Returns:
        User ORM object.

    Raises:
        HTTPException 401: if token is invalid or user not found.
    """
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload  = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username = payload.get("sub")
        if username is None:
            raise credentials_exc
    except JWTError:
        raise credentials_exc

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exc
    return user


_oauth2_optional = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def get_optional_current_user(
    token: Optional[str] = Depends(_oauth2_optional),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Dependency: return current User if valid Bearer token provided, else None."""
    if not token:
        return None
    try:
        payload  = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username = payload.get("sub")
        if not username:
            return None
        return db.query(User).filter(User.username == username).first()
    except Exception:
        return None


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency that ensures the current user has the Admin role."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin role required.")
    return current_user


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@router.post("/register", response_model=TokenResponse, summary="Register new user")
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    try:
        if db.query(User).filter(User.username == request.username).first():
            raise HTTPException(status_code=400, detail="Username already registered.")
        if db.query(User).filter(User.email == request.email).first():
            raise HTTPException(status_code=400, detail="Email already registered.")

        user = User(
            username=request.username,
            email=request.email,
            hashed_password=_hash_password(request.password),
            role=request.role,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        token = _create_token(user.username, user.role.value)
        logger.info("New user registered: %s (%s)", user.username, user.role)
        return TokenResponse(access_token=token, username=user.username, role=user.role.value)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Registration error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Registration error: {type(exc).__name__} - {str(exc)}")


@router.post("/login", response_model=TokenResponse, summary="Login and get JWT token")
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    try:
        user = db.query(User).filter(User.username == form.username).first()
        if user is None or not _verify_password(form.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password.",
            )

        user.last_login = datetime.utcnow()
        db.commit()

        token = _create_token(user.username, user.role.value)
        return TokenResponse(access_token=token, username=user.username, role=user.role.value)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Login error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Login error: {type(exc).__name__} - {str(exc)}")


@router.get("/me", response_model=UserProfile, summary="Current user profile")
def me(current_user: User = Depends(get_current_user)):
    """Return the profile of the currently authenticated user."""
    return UserProfile(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role.value,
    )
