"""
Minimal FastAPI stub, present only for repository health checks and to
give test/CI infrastructure something to import. Contains NO business
logic, NO endpoints beyond a health check, and NO booking/authz/pricing
behavior — all of that is explicitly out of scope for
TASK-DB-FOUNDATION-001 (DB plan §2).
"""

from __future__ import annotations

from fastapi import FastAPI
from sqlalchemy import text

from app.db.session import get_engine

app = FastAPI(title="Nirman DB Foundation", version="0.1.0")


@app.get("/health")
def health() -> dict:
    """Confirms the process can reach PostgreSQL. No business logic."""
    with get_engine().connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ok"}
