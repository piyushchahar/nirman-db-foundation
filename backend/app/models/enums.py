"""
Enum types required by the DB foundation.

Values are taken verbatim from the Nirman Technical Specification
v1.3 FINAL HARDENED:

- UserStatus        -> spec Part D.1
- BookingStatus      -> spec Part D.7 / D.8 (full transition whitelist)
- ResourceType       -> spec Part D.9 (booking_items.resource_type)
- RevieweeType       -> spec Part D.13 (reviews.reviewee_type)

These are PostgreSQL native ENUM types (created via
sqlalchemy.dialects.postgresql.ENUM in the migrations), not
VARCHAR + CHECK. No additional values are added beyond what the
specification defines; no roadmap-only states are introduced.
"""

from __future__ import annotations

import enum


class UserStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    DISABLED = "DISABLED"


class BookingStatus(str, enum.Enum):
    REQUESTED = "REQUESTED"
    HELD = "HELD"
    CONFIRMED = "CONFIRMED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class ResourceType(str, enum.Enum):
    WORKER = "WORKER"
    TEAM = "TEAM"


class RevieweeType(str, enum.Enum):
    WORKER = "WORKER"
    ORGANIZATION = "ORGANIZATION"
    HOMEOWNER = "HOMEOWNER"


# Reservation-holding statuses per spec Part D.10 ("Active-state strategy:
# Option A"): a worker_reservations row exists only while its booking is in
# one of these statuses. Kept here (rather than hardcoded in migrations) so
# the deferred trigger, tests, and any later service share one definition.
RESERVATION_HOLDING_STATUSES: tuple[str, ...] = (
    BookingStatus.REQUESTED.value,
    BookingStatus.HELD.value,
    BookingStatus.CONFIRMED.value,
    BookingStatus.IN_PROGRESS.value,
)
