"""
Exercise: Understanding FastAPI Code Patterns
=============================================
FastAPI application demonstrating:
- Repository pattern
- Dependency injection
- JWT authentication
- Role-based access control
- Timing middleware
- Audit logging (Part 4 implementation)
"""

from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Callable, Optional, Type, TypeVar, Generic, List
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from functools import wraps
import jwt

from database import Base, get_db
from models import User, AuditLog

# ── JWT CONFIG ─────────────────────────────────────────────────────────────
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM  = "HS256"

# ── GENERIC REPOSITORY PATTERN ─────────────────────────────────────────────
T = TypeVar('T')

class Repository(Generic[T]):
    """Base repository providing reusable CRUD operations for any model."""

    def __init__(self, model: Type[T]):
        self.model = model

    async def get(self, db: AsyncSession, record_id: int) -> Optional[T]:
        result = await db.execute(select(self.model).where(self.model.id == record_id))
        return result.scalar_one_or_none()

    async def list(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[T]:
        result = await db.execute(select(self.model).offset(skip).limit(limit))
        return result.scalars().all()

    async def create(self, db: AsyncSession, obj: T) -> T:
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj


class UserRepository(Repository[User]):
    """User-specific data access. Inherits all base CRUD from Repository."""

    async def get_by_username(self, db: AsyncSession, username: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()


class AuditRepository(Repository[AuditLog]):
    """Repository for recording user actions to the audit log."""

    async def log(self, db: AsyncSession, user_id: int, action: str) -> None:
        entry = AuditLog(
            user_id=user_id,
            action=action,
            timestamp=datetime.utcnow(),
        )
        db.add(entry)
        await db.commit()


# ── JWT HELPERS ────────────────────────────────────────────────────────────
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT token with an expiry time."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ── TIMING MIDDLEWARE ──────────────────────────────────────────────────────
class TimingMiddleware:
    """Records processing time for every request in the X-Process-Time header."""

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        start_time   = datetime.utcnow()
        response     = await call_next(request)
        process_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        response.headers["X-Process-Time"] = str(process_time)
        return response


# ── DEPENDENCY: CURRENT USER ───────────────────────────────────────────────
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Decode the JWT and return the authenticated User, or raise HTTP 401."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload  = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    user_repo = UserRepository(User)
    user = await user_repo.get_by_username(db, username)
    if user is None:
        raise credentials_exception
    return user


# ── DEPENDENCY: ROLE-BASED ACCESS CONTROL ─────────────────────────────────
def require_role(role: str):
    """Factory that returns a dependency enforcing a specific user role."""
    async def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' required.",
            )
        return current_user
    return role_checker


# ── APP SETUP ──────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle handler."""
    print("Application starting — DB connection pool ready.")
    yield
    print("Application shutting down — closing connections.")


app = FastAPI(title="FastAPI Code Patterns Demo", lifespan=lifespan)
app.middleware("http")(TimingMiddleware())


# ── ROUTES ─────────────────────────────────────────────────────────────────
@app.get("/admin/users/")
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """
    Admin-only endpoint. Returns a paginated list of all users.
    Execution flow:
      TimingMiddleware → get_db → oauth2_scheme → get_current_user
      → require_role("admin") → handler → AuditRepository.log → return
    """
    user_repo  = UserRepository(User)
    audit_repo = AuditRepository(AuditLog)

    users = await user_repo.list(db, skip=skip, limit=limit)
    await audit_repo.log(db, current_user.id, "admin_list_users")

    return users
