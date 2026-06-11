"""
File 1: Original API Endpoint Code
===================================
Endpoint: GET /admin/users/
Application: FastAPI User Management API
"""

from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Callable, Optional, Type, TypeVar, Generic, List
from datetime import datetime, timedelta
import jwt

from database import Base, get_db
from models import User, AuditLog

SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM  = "HS256"

T = TypeVar('T')

# --- Repository Pattern ---
class Repository(Generic[T]):
    def __init__(self, model: Type[T]):
        self.model = model

    async def list(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[T]:
        result = await db.execute(select(self.model).offset(skip).limit(limit))
        return result.scalars().all()


class UserRepository(Repository[User]):
    pass


class AuditRepository(Repository[AuditLog]):
    async def log(self, db: AsyncSession, user_id: int, action: str) -> None:
        entry = AuditLog(user_id=user_id, action=action, timestamp=datetime.utcnow())
        db.add(entry)
        await db.commit()


# --- JWT & Auth ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user


# --- Role-Based Access Control ---
def require_role(role: str):
    async def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' required.",
            )
        return current_user
    return role_checker


# --- Timing Middleware ---
class TimingMiddleware:
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        start_time   = datetime.utcnow()
        response     = await call_next(request)
        process_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        response.headers["X-Process-Time"] = str(process_time)
        return response


# --- The Endpoint ---
app = FastAPI(title="FastAPI User Management API")
app.middleware("http")(TimingMiddleware())


@app.get("/admin/users/")
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    user_repo  = UserRepository(User)
    audit_repo = AuditRepository(AuditLog)

    users = await user_repo.list(db, skip=skip, limit=limit)
    await audit_repo.log(db, current_user.id, "admin_list_users")

    return users
