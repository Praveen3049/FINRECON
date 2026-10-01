from datetime import datetime, timezone
import enum
import uuid
from sqlalchemy import Boolean, Column, DateTime, Enum as SQLEnum, Index, String
from app.core.database import Base


class UserRole(str, enum.Enum):
    USER = "USER"
    AUDITOR = "AUDITOR"
    MANAGER = "MANAGER"


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole, values_callable=lambda x: [e.value for e in x]), nullable=False, default=UserRole.USER)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    last_login_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_users_email_role", "email", "role"),
    )

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"
