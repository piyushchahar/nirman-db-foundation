from __future__ import annotations

import os
import uuid

import sqlalchemy as sa
from fastapi.testclient import TestClient

from app.core.config import get_test_database_url
from app.main import app
from app.db.session import get_db


def test_create_booking_http_to_postgres():
    engine = sa.create_engine(get_test_database_url(), future=True)

    requester_id = uuid.uuid4()
    project_id = uuid.uuid4()
    job_requirement_id = uuid.uuid4()

    with engine.begin() as conn:
        conn.execute(
            sa.text(
                "INSERT INTO users (id, authz_version, status) "
                "VALUES (:id, 1, 'ACTIVE')"
            ),
            {"id": requester_id},
        )
        conn.execute(
            sa.text(
                "INSERT INTO projects "
                "(id, latitude, longitude, city, state) "
                "VALUES (:id, 25.4358, 78.5685, 'Jhansi', 'Uttar Pradesh')"
            ),
            {"id": project_id},
        )
        conn.execute(
            sa.text(
                "INSERT INTO job_requirements "
                "(id, project_id, workers_needed, start_time, end_time) "
                "VALUES (:id, :project_id, 1, "
                "'2026-09-10T09:00:00+00:00', "
                "'2026-09-10T17:00:00+00:00')"
            ),
            {"id": job_requirement_id, "project_id": project_id},
        )

    TestSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/bookings",
                json={
                    "job_requirement_id": str(job_requirement_id),
                    "requester_id": str(requester_id),
                    "idempotency_key": "api-test-"
                    + uuid.uuid4().hex,
                },
            )

        assert response.status_code == 200

        body = response.json()
        assert body["data"]["job_requirement_id"] == str(job_requirement_id)
        assert body["data"]["requester_id"] == str(requester_id)
        assert body["data"]["status"] == "REQUESTED"
        assert body["meta"]["request_id"]

        with engine.connect() as conn:
            row = conn.execute(
                sa.text(
                    "SELECT status FROM bookings "
                    "WHERE id = :id"
                ),
                {"id": uuid.UUID(body["data"]["id"])},
            ).one()

        assert row.status == "REQUESTED"

    finally:
        app.dependency_overrides.clear()

        with engine.begin() as conn:
            conn.execute(
                sa.text("DELETE FROM booking_idempotency WHERE requester_id = :id"),
                {"id": requester_id},
            )
            conn.execute(
                sa.text("DELETE FROM bookings WHERE requester_id = :id"),
                {"id": requester_id},
            )
            conn.execute(
                sa.text("DELETE FROM job_requirements WHERE id = :id"),
                {"id": job_requirement_id},
            )
            conn.execute(
                sa.text("DELETE FROM projects WHERE id = :id"),
                {"id": project_id},
            )
            conn.execute(
                sa.text("DELETE FROM users WHERE id = :id"),
                {"id": requester_id},
            )

    engine.dispose()

from sqlalchemy.orm import sessionmaker
