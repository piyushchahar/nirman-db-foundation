"""
Shared SQLAlchemy declarative base.

All models import `Base` from here so that a single MetaData object
collects every table, which Alembic's `env.py` then uses as the
autogenerate/verification target.
"""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
