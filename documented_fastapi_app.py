"""
Exercise: Code Documentation
=============================
Original FastAPI application with comprehensive inline code documentation
added using AI prompting strategies.

Demonstrates:
- Module-level docstrings
- Class and method docstrings
- Inline comments explaining the "why"
- Type hints throughout
"""

from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Callable, Optional, Type, TypeVar, Generic, List
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
import jwt

# TypeVar allows the Repository class to work with any SQLAlchemy model.
# This is the foundation of the Generic Repository pattern used throughout.
T = TypeVar('T')

SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM  = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15


# ── DATABASE BASE MODEL ────────────────────────────────────────────────────
class Base:
    """
    Declarative base for all SQLAlchemy ORM models.
    Every model that maps to a database table inherits from this class.
    SQLAlchemy uses it to track all models and generate/migrate schemas.
    """
    pass


# ── ORM MODELS ─────────────────────────────────────────────────────────────
class User(Base):
    """
    Represents a registered user in the system.

    Attributes:
        id       -- Auto-incremented primary key.
        username -- Unique login identifier. Indexed for fast lookups.
        role     -- Access level: 'user' (default) or 'admin'.
        status   -- Membership tier: 'regular', 'member', or 'vip'.
        months   -- How long the user has been a member (used for loyalty discounts).
    """
    __tablename__ = "users"


class AuditLog(Base):
    """
    Records every significant user action for security auditing.

    Why audit logging matters:
        - Provides a tamper-evident record of who did what and when.
        - Required for compliance in many regulated industries.
        - Helps debug unexpected behaviour by tracing actions back to their source.

    Attributes:
        id        -- Auto-incremented primary key.
        user_id   -- FK reference to the User who performed the action.
        action    -- Short string describing the action, e.g. 'admin_list_users'.
        timestamp -- UTC datetime when the action occurred.
    """
    __tablename__ = "audit_logs"


# ── GENERIC REPOSITORY ─────────────────────────────────────────────────────
class Repository(Generic[T]):
    """
    Generic base repository providing reusable CRUD operations for any ORM model.

    Why use the Repository pattern?
        - Centralises all database access in one place per model.
        - Keeps route handlers free of raw SQL / ORM queries.
        - Makes swapping the database engine (e.g. SQLite → PostgreSQL) trivial.
        - Enables easy unit testing by mocking the repository.

    Type parameter T:
        The SQLAlchemy model this repository manages.
        e.g.  UserRepository(Repository[User])
              AuditRepository(Repository[AuditLog])
    """

    def __init__(self, model: Type[T]) -> None:
        # Store the model class so every method knows which table to query.
        self.model = model

    async def get(self, db: AsyncSession, record_id: int) -> Optional[T]:
        """
        Fetch a single record by primary key.

        Returns None if not found rather than raising an exception,
        so callers can decide how to handle the missing-record case.
        """
        result = await db.execute(
            select(self.model).where(self.model.id == record_id)
        )
        return result.scalar_one_or_none()

    async def list(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[T]:
        """
        Return a paginated slice of all records.

        Args:
            skip  -- Number of rows to skip (offset). Used for pagination.
            limit -- Maximum rows to return. Prevents accidentally loading
                     millions of rows in a single request.
        """
        result = await db.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def create(self, db: AsyncSession, obj: T) -> T:
        """
        Persist a new record and return it with its generated ID.

        db.refresh(obj) re-fetches the object from the DB so that
        auto-generated fields (e.g. id, created_at) are populated on the
        returned object.
        """
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj


# ── SPECIALISED REPOSITORIES ───────────────────────────────────────────────
class UserRepository(Repository[User]):
    """
    User-specific data access layer.
    Inherits all generic CRUD from Repository[User] and adds
    a username-based lookup needed for authentication.
    """

    async def get_by_username(self, db: AsyncSession, username: str) -> Optional[User]:
        """
        Look up a user by their unique username.

        Used by get_current_user() during JWT authentication to verify
        that the token's subject ('sub' claim) maps to a real account.
        Returns None if the username does not exist.
        """
        result = await db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()


class AuditRepository(Repository[AuditLog]):
    """
    Audit-log specific data access layer.
    Provides a convenience log() method so callers never touch
    AuditLog model construction directly.
    """

    async def log(self, db: AsyncSession, user_id: int, action: str) -> None:
        """
        Write one audit entry to the database.

        Args:
            user_id -- ID of the user who triggered the action.
            action  -- Short descriptive string, e.g. 'login', 'admin_list_users'.

        The timestamp is set here (server-side UTC) rather than by the client
        to prevent clock-skew or client manipulation.
        """
        entry = AuditLog(
            user_id=user_id,
            action=action,
            timestamp=datetime.utcnow(),
        )
        db.add(entry)
        await db.commit()


# ── DATABASE SESSION DEPENDENCY ────────────────────────────────────────────
async def get_db():
    """
    FastAPI dependency that yields an async database session.

    The 'async with' + try/finally pattern guarantees the session is
    closed (and the connection returned to the pool) even if the route
    raises an exception. Without this, the app would leak DB connections
    under load and eventually exhaust the pool.
    """
    async with AsyncSession() as session:
        try:
            yield session
        finally:
            await session.close()


# ── JWT HELPERS ────────────────────────────────────────────────────────────
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a signed JWT access token.

    How JWTs work:
        1. A payload dict (claims) is Base64-encoded as the token body.
        2. The payload is signed with SECRET_KEY using the HS256 algorithm.
        3. Anyone with the secret key can verify the signature — without
           needing to query the database on every request.

    Args:
        data          -- Claims to embed, typically {'sub': username}.
        expires_delta -- How long until the token expires.
                         Defaults to ACCESS_TOKEN_EXPIRE_MINUTES if not provided.

    Security note:
        Never put sensitive data (passwords, credit cards) in a JWT payload.
        The payload is Base64-encoded, not encrypted — it can be decoded
        without the secret key.
    """
    to_encode = data.copy()
    expire    = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})  # 'exp' is a standard JWT registered claim
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ── TIMING MIDDLEWARE ──────────────────────────────────────────────────────
class TimingMiddleware:
    """
    ASGI middleware that measures and reports request processing time.

    Why middleware instead of a decorator?
        Middleware wraps EVERY request automatically — no need to add
        a decorator to each route. This makes it ideal for cross-cutting
        concerns like logging, timing, and CORS.

    The X-Process-Time header is a non-standard but widely used convention
    that allows clients and API gateways to monitor backend performance
    without changing the response body.
    """

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        start_time   = datetime.utcnow()
        response     = await call_next(request)  # run the actual route handler
        process_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        response.headers["X-Process-Time"] = str(process_time)
        return response


# ── AUTH DEPENDENCY ────────────────────────────────────────────────────────
# oauth2_scheme extracts the Bearer token from the Authorization header.
# tokenUrl="token" tells FastAPI's /docs UI where to send login requests.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI dependency: decode a JWT and return the authenticated User.

    Dependency injection chain:
        Route handler
          └── get_current_user
                ├── oauth2_scheme  (extracts token from Authorization header)
                └── get_db         (provides the async DB session)

    Raises HTTP 401 in three cases:
        1. The token is missing or malformed.
        2. The JWT signature is invalid or the token has expired.
        3. The username in the token ('sub' claim) does not exist in the DB.

    Why a single exception for all three cases?
        Returning identical errors prevents attackers from distinguishing
        "bad token" from "valid token but unknown user" — both leak information.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},  # tells clients to use Bearer auth
    )

    try:
        payload  = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")  # 'sub' = subject (standard JWT claim)
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        # Catches expired tokens, invalid signatures, and malformed JWTs
        raise credentials_exception

    user_repo = UserRepository(User)
    user = await user_repo.get_by_username(db, username)
    if user is None:
        raise credentials_exception

    return user


# ── RBAC DEPENDENCY FACTORY ────────────────────────────────────────────────
def require_role(role: str):
    """
    Factory function that returns a FastAPI dependency enforcing a specific role.

    Why a factory instead of a single dependency?
        Different endpoints require different roles. By calling require_role("admin")
        or require_role("moderator") as a Depends() argument, each route declares
        its access requirements inline — no if/else blocks inside route handlers.

    Example usage:
        @app.get("/admin/users/")
        async def list_users(
            _: User = Depends(require_role("admin"))
        ):
            ...
    """
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' required.",
            )
        return current_user
    return role_checker


# ── APP LIFESPAN ───────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages application startup and shutdown lifecycle.

    Code BEFORE yield runs on startup (e.g. create DB tables, warm caches).
    Code AFTER yield runs on shutdown (e.g. close connections, flush logs).

    Using @asynccontextmanager avoids the older on_event("startup") pattern,
    which is deprecated in recent FastAPI versions.
    """
    # Startup
    print("App starting — initialising database connection pool.")
    yield
    # Shutdown
    print("App shutting down — releasing resources.")


# ── APPLICATION ────────────────────────────────────────────────────────────
app = FastAPI(
    title="FastAPI User Management API",
    description="Demonstrates Repository pattern, DI, JWT auth, RBAC, and audit logging.",
    version="1.0.0",
    lifespan=lifespan,
)
app.middleware("http")(TimingMiddleware())


# ── ROUTES ─────────────────────────────────────────────────────────────────
@app.get(
    "/admin/users/",
    summary="List all users",
    description="Returns a paginated list of users. Admin role required.",
)
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    # require_role("admin") will raise 403 before this handler runs
    # if the authenticated user is not an admin.
    current_user: User = Depends(require_role("admin")),
) -> List[User]:
    """
    Admin-only endpoint: returns paginated list of all users.

    Every successful call is recorded in the audit log so administrators
    can review who accessed the user list and when.
    """
    user_repo  = UserRepository(User)
    audit_repo = AuditRepository(AuditLog)

    users = await user_repo.list(db, skip=skip, limit=limit)

    # Record this admin action — runs after the query so a DB error
    # in the query doesn't produce a misleading audit entry.
    await audit_repo.log(db, current_user.id, "admin_list_users")

    return users
