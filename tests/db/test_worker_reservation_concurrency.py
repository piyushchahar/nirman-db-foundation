"""
Concurrent worker reservation race test (spec D.10; DB plan §32/§42).

Uses two REAL, separate PostgreSQL connections/transactions running on
separate threads — not the shared, rollback-isolated `db_conn` fixture,
because this test needs an actual COMMIT to observe the exclusion
constraint's cross-transaction blocking behavior. Cleans up its own rows
in a finally block via a third connection.

Transaction A: worker X, 09:00-17:00
Transaction B: worker X, 13:00-18:00 (overlaps A)

Expected: exactly one of A/B commits successfully; the other fails with
an ExclusionViolation raised by PostgreSQL itself.
"""

from __future__ import annotations

import threading
import uuid
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError

from tests.db.conftest import (
    make_booking,
    make_booking_item,
    make_job_requirement,
    make_project,
    make_user,
    make_worker_profile,
)


def _hm(hour: int) -> datetime:
    return datetime(2026, 9, 2, hour, 0, tzinfo=timezone.utc)


def test_concurrent_overlapping_reservations_exactly_one_commits(
    migrated_engine: Engine,
):
    # --- Arrange ---
    # Create the bookings in a valid committed state first.
    setup_conn = migrated_engine.connect()
    setup_trans = setup_conn.begin()

    requester_id = make_user(setup_conn)
    worker_user_id = make_user(setup_conn)
    worker_id = make_worker_profile(setup_conn, worker_user_id)
    project_id = make_project(setup_conn)
    jr_id = make_job_requirement(
        setup_conn,
        project_id,
        workers_needed=1,
    )

    booking_a = make_booking(
        setup_conn,
        jr_id,
        requester_id,
        status="HELD",
    )

    booking_b = make_booking(
        setup_conn,
        jr_id,
        requester_id,
        status="HELD",
    )

    make_booking_item(
        setup_conn,
        booking_id=booking_a,
        resource_type="WORKER",
        status="HELD",
        worker_profile_id=worker_id,
    )

    make_booking_item(
        setup_conn,
        booking_id=booking_b,
        resource_type="WORKER",
        status="HELD",
        worker_profile_id=worker_id,
    )

    # The shape trigger requires exactly one reservation per booking
    # at commit time, so create temporary reservations first.
    reservation_a_id = uuid.uuid4()
    reservation_b_id = uuid.uuid4()

    setup_conn.execute(
        text(
            """
            INSERT INTO worker_reservations
                (id, worker_profile_id, booking_id, reservation_range)
            VALUES
                (:id, :worker_id, :booking_id,
                 tstzrange(:start, :end, '[)'))
            """
        ),
        {
            "id": reservation_a_id,
            "worker_id": worker_id,
            "booking_id": booking_a,
            "start": _hm(0),
            "end": _hm(1),
        },
    )

    setup_conn.execute(
        text(
            """
            INSERT INTO worker_reservations
                (id, worker_profile_id, booking_id, reservation_range)
            VALUES
                (:id, :worker_id, :booking_id,
                 tstzrange(:start, :end, '[)'))
            """
        ),
        {
            "id": reservation_b_id,
            "worker_id": worker_id,
            "booking_id": booking_b,
            "start": _hm(2),
            "end": _hm(3),
        },
    )

    setup_trans.commit()
    setup_conn.close()

    results: dict[str, str] = {}
    start_barrier = threading.Barrier(2)

    def _attempt(
        label: str,
        reservation_id: uuid.UUID,
        booking_id,
        start_hour: int,
        end_hour: int,
    ):
        conn = migrated_engine.connect()

        try:
            trans = conn.begin()

            start_barrier.wait()

            try:
                # Remove this booking's temporary reservation.
                conn.execute(
                    text(
                        """
                        DELETE FROM worker_reservations
                        WHERE id = :reservation_id
                        """
                    ),
                    {"reservation_id": reservation_id},
                )

                # Insert the actual overlapping reservation.
                conn.execute(
                    text(
                        """
                        INSERT INTO worker_reservations
                            (
                                id,
                                worker_profile_id,
                                booking_id,
                                reservation_range
                            )
                        VALUES
                            (
                                :id,
                                :worker_id,
                                :booking_id,
                                tstzrange(:start, :end, '[)')
                            )
                        """
                    ),
                    {
                        "id": uuid.uuid4(),
                        "worker_id": worker_id,
                        "booking_id": booking_id,
                        "start": _hm(start_hour),
                        "end": _hm(end_hour),
                    },
                )

                trans.commit()
                results[label] = "COMMITTED"

            except IntegrityError:
                trans.rollback()
                results[label] = "REJECTED"

        finally:
            conn.close()

    thread_a = threading.Thread(
        target=_attempt,
        args=("A", reservation_a_id, booking_a, 9, 17),
    )

    thread_b = threading.Thread(
        target=_attempt,
        args=("B", reservation_b_id, booking_b, 13, 18),
    )

    thread_a.start()
    thread_b.start()

    thread_a.join(timeout=30)
    thread_b.join(timeout=30)

    try:
        assert set(results.keys()) == {"A", "B"}, (
            f"Both threads must finish: {results}"
        )

        outcomes = list(results.values())

        assert outcomes.count("COMMITTED") == 1, (
            f"Exactly one transaction must commit, got: {results}"
        )

        assert outcomes.count("REJECTED") == 1, (
            f"Exactly one transaction must be rejected, got: {results}"
        )

    finally:
        # Cleanup test data.
        #
        # The shape-validation triggers are DEFERRABLE and expect the
        # booking to exist while validating worker_reservations.
        # During teardown we are intentionally deleting the entire
        # object graph, so those validation triggers must not run.

        cleanup_conn = migrated_engine.connect()

        try:
            cleanup_conn.execute(
                text("SET session_replication_role = replica")
            )

            cleanup_conn.execute(
                text(
                    """
                    DELETE FROM worker_reservations
                    WHERE booking_id IN (:a, :b)
                    """
                ),
                {"a": booking_a, "b": booking_b},
            )

            cleanup_conn.execute(
                text(
                    """
                    DELETE FROM booking_items
                    WHERE booking_id IN (:a, :b)
                    """
                ),
                {"a": booking_a, "b": booking_b},
            )

            cleanup_conn.execute(
                text(
                    """
                    DELETE FROM bookings
                    WHERE id IN (:a, :b)
                    """
                ),
                {"a": booking_a, "b": booking_b},
            )

            cleanup_conn.execute(
                text(
                    """
                    DELETE FROM job_requirements
                    WHERE id = :id
                    """
                ),
                {"id": jr_id},
            )

            cleanup_conn.execute(
                text(
                    """
                    DELETE FROM projects
                    WHERE id = :id
                    """
                ),
                {"id": project_id},
            )

            cleanup_conn.execute(
                text(
                    """
                    DELETE FROM worker_profiles
                    WHERE id = :id
                    """
                ),
                {"id": worker_id},
            )

            cleanup_conn.execute(
                text(
                    """
                    DELETE FROM users
                    WHERE id IN (:a, :b)
                    """
                ),
                {"a": requester_id, "b": worker_user_id},
            )

            cleanup_conn.commit()

        finally:
            cleanup_conn.execute(
                text("SET session_replication_role = origin")
            )
            cleanup_conn.close()