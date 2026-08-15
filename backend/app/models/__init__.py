"""
Importing this package registers every model on `Base.metadata`, which
Alembic's `env.py` uses as the autogenerate/verification target.

Import order follows FK dependency order for readability only; SQLAlchemy
does not require any particular import order for mapper configuration.
"""

from app.models.enums import (  # noqa: F401
    BookingStatus,
    RevieweeType,
    ResourceType,
    UserStatus,
)
from app.models.user import User  # noqa: F401
from app.models.worker_profile import WorkerProfile  # noqa: F401
from app.models.organization import Organization  # noqa: F401
from app.models.team import Team, TeamMember  # noqa: F401
from app.models.project import Project  # noqa: F401
from app.models.project_location import ProjectLocation  # noqa: F401
from app.models.job_requirement import JobRequirement  # noqa: F401
from app.models.availability_window import AvailabilityWindow  # noqa: F401
from app.models.booking import Booking  # noqa: F401
from app.models.team_booking_group import TeamBookingGroup  # noqa: F401
from app.models.booking_item import BookingItem  # noqa: F401
from app.models.worker_reservation import WorkerReservation  # noqa: F401
from app.models.booking_idempotency import BookingIdempotency  # noqa: F401
from app.models.outbox_event import OutboxEvent  # noqa: F401
from app.models.review import Review  # noqa: F401

__all__ = [
    "BookingStatus",
    "RevieweeType",
    "ResourceType",
    "UserStatus",
    "User",
    "WorkerProfile",
    "Organization",
    "Team",
    "TeamMember",
    "Project",
    "ProjectLocation",
    "JobRequirement",
    "AvailabilityWindow",
    "Booking",
    "TeamBookingGroup",
    "BookingItem",
    "WorkerReservation",
    "BookingIdempotency",
    "OutboxEvent",
    "Review",
]
