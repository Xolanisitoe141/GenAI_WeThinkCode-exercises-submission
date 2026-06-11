"""
SQLAlchemy ORM models.
"""
from sqlalchemy import Column, Integer, String, DateTime
from database import Base


class User(Base):
    __tablename__ = "users"

    id       = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    role     = Column(String, default="user")   # "user" | "admin"
    months   = Column(Integer, default=0)        # membership months
    status   = Column(String, default="regular") # "regular" | "member" | "vip"


class AuditLog(Base):
    """Records user actions for auditing purposes (Part 4 implementation)."""
    __tablename__ = "audit_logs"

    id        = Column(Integer, primary_key=True, index=True)
    user_id   = Column(Integer, nullable=False)
    action    = Column(String, nullable=False)   # e.g. "login", "admin_list_users"
    timestamp = Column(DateTime, nullable=False)
