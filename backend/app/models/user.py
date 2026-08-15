"""
users — spec Part D.1.

Only the columns explicitly required by the DB foundation are modeled:
id, authz_version, status, created_at, updated_at. The spec's `...existing
columns...` placeholder (name/email/auth credentials/roles etc.) is
explicitly out of scope for TASK-DB-FOUNDATION-001 and is not invented
here — see DEFERRED ARCHITECTURE ITEMS in the final report.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, func
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import UserStatus

user_status_enum = PGEnum(
    UserStatus, name="user_status", create_type=False, native_enum=True
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    authz_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    status: Mapped[UserStatus] = mapped_column(
        user_status_enum, nullable=False, server_default=UserStatus.ACTIVE.value
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
