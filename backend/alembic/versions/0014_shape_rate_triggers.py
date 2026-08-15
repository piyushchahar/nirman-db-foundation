"""booking_items triggers: agreed_rate immutability + deferred shape/status guard

Revision ID: 0014_shape_rate_triggers
Revises: 0013_worker_reservations
Create Date: 2026-08-14

NOTE ON REVISION ID LENGTH: originally named
"0014_booking_shape_and_rate_triggers" (36 characters), which exceeds the
32-character width of Alembic's own internal `alembic_version.version_num`
bookkeeping column. That table is Alembic tooling infrastructure, not part
of the Nirman domain schema, so shortening this identifier does not touch
any table/column/constraint defined by the spec or DB plan — only
Alembic's own revision-tracking id string.

Two independent PostgreSQL-level correctness mechanisms, per DB plan
§26 and §28, and spec Parts D.9 / D.9b:

1) booking_items_agreed_rate_immutable
   Verbatim from spec D.9: any UPDATE that changes agreed_rate (to a new
   value, or to NULL) raises an exception. Regular (non-deferred) BEFORE
   trigger — immutability must be enforced immediately, not at commit.

2) Deferred booking-shape / status-consistency constraint trigger
   (function `validate_booking_shape`, spec D.9b normative rejection
   contract). This is NOT the BookingStateMachine and does not authorize
   any transition — it only rejects a transaction whose FINAL committed
   state violates the documented shape. It is DEFERRABLE INITIALLY
   DEFERRED so a multi-statement transaction (create booking -> create
   booking_items -> create worker_reservations, or a multi-row status
   transition) can leave intermediate rows temporarily incomplete without
   a false failure, per spec D.9b: "must validate the final transaction
   state, not intermediate insert order."

   Row-level invariants (WORKER/TEAM XOR, agreed_rate NOT NULL, unique
   team_booking_group ownership) are already enforced by CHECK/UNIQUE/FK
   constraints created in earlier migrations and are NOT re-checked here.
   This trigger checks only the cross-row, aggregate invariants that a
   single-row CHECK constraint cannot express:
     - shape counts (1 WORKER row for an individual booking; 1 TEAM row
       + workers_needed WORKER rows for a team booking)
     - workers_needed = 1 for individual bookings (joins job_requirements)
     - bookings.team_booking_group_id matches the TEAM item's
       team_booking_group_id
     - worker_reservations count matches the expected shape
     - booking_items.status equals bookings.status for every item

   MODELING NOTE (documented, not silently assumed): the trigger treats
   "at least one committed booking_items row must exist for any booking
   row present at transaction end" as required by D.9b's literal wording
   ("individual booking: ... exactly one booking_items row exists").
   This has not been executed against a real PostgreSQL instance in this
   environment — see the final report's MIGRATION VERIFICATION section.
   Attached to both booking_items and worker_reservations (AFTER INSERT
   OR UPDATE OR DELETE, FOR EACH ROW) so that a transaction which only
   touches one of the two tables for a given booking still triggers
   validation of that booking's full shape at commit time.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0014_shape_rate_triggers"
down_revision: Union[str, None] = "0013_worker_reservations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


AGREED_RATE_FUNCTION = """
CREATE OR REPLACE FUNCTION prevent_agreed_rate_change()
RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.agreed_rate IS DISTINCT FROM OLD.agreed_rate THEN
        RAISE EXCEPTION 'booking_items.agreed_rate is immutable after creation';
    END IF;
    RETURN NEW;
END;
$$;
"""

AGREED_RATE_TRIGGER = """
CREATE TRIGGER booking_items_agreed_rate_immutable
BEFORE UPDATE OF agreed_rate ON booking_items
FOR EACH ROW
EXECUTE FUNCTION prevent_agreed_rate_change();
"""

SHAPE_VALIDATION_FUNCTION = """
CREATE OR REPLACE FUNCTION validate_booking_shape(p_booking_id uuid)
RETURNS void
LANGUAGE plpgsql AS $$
DECLARE
    v_status                booking_status;
    v_team_booking_group_id uuid;
    v_workers_needed        int;
    v_team_item_count       int;
    v_worker_item_count     int;
    v_mismatched_status     int;
    v_reservation_count     int;
    v_team_item_group_id    uuid;
BEGIN
    SELECT b.status, b.team_booking_group_id, jr.workers_needed
      INTO v_status, v_team_booking_group_id, v_workers_needed
      FROM bookings b
      JOIN job_requirements jr ON jr.id = b.job_requirement_id
     WHERE b.id = p_booking_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'validate_booking_shape: booking % not found (or its job_requirement is missing)',
            p_booking_id;
    END IF;

    SELECT count(*) FILTER (WHERE resource_type = 'TEAM'),
           count(*) FILTER (WHERE resource_type = 'WORKER'),
           count(*) FILTER (WHERE status IS DISTINCT FROM v_status)
      INTO v_team_item_count, v_worker_item_count, v_mismatched_status
      FROM booking_items
     WHERE booking_id = p_booking_id;

    IF v_mismatched_status > 0 THEN
        RAISE EXCEPTION
            'booking %: % booking_items row(s) have status different from bookings.status (%)',
            p_booking_id, v_mismatched_status, v_status;
    END IF;

    SELECT count(*) INTO v_reservation_count
      FROM worker_reservations
     WHERE booking_id = p_booking_id;

    IF v_team_item_count = 0 THEN
        -- Individual booking shape.
        IF v_workers_needed <> 1 THEN
            RAISE EXCEPTION
                'booking %: individual booking (no TEAM item) requires workers_needed = 1, found %',
                p_booking_id, v_workers_needed;
        END IF;
        IF v_worker_item_count <> 1 THEN
            RAISE EXCEPTION
                'booking %: individual booking must have exactly one WORKER booking_item, found %',
                p_booking_id, v_worker_item_count;
        END IF;
        IF v_reservation_count <> 1 THEN
            RAISE EXCEPTION
                'booking %: individual booking must have exactly one worker_reservations row, found %',
                p_booking_id, v_reservation_count;
        END IF;

    ELSIF v_team_item_count = 1 THEN
        -- Team booking shape.
        IF v_worker_item_count <> v_workers_needed THEN
            RAISE EXCEPTION
                'booking %: team booking must have exactly workers_needed (%) WORKER booking_items, found %',
                p_booking_id, v_workers_needed, v_worker_item_count;
        END IF;
        IF v_reservation_count <> v_workers_needed THEN
            RAISE EXCEPTION
                'booking %: team booking must have exactly workers_needed (%) worker_reservations rows, found %',
                p_booking_id, v_workers_needed, v_reservation_count;
        END IF;
        IF v_team_booking_group_id IS NULL THEN
            RAISE EXCEPTION
                'booking %: team booking must set bookings.team_booking_group_id',
                p_booking_id;
        END IF;

        SELECT team_booking_group_id INTO v_team_item_group_id
          FROM booking_items
         WHERE booking_id = p_booking_id AND resource_type = 'TEAM';

        IF v_team_item_group_id IS DISTINCT FROM v_team_booking_group_id THEN
            RAISE EXCEPTION
                'booking %: TEAM booking_item.team_booking_group_id (%) must match bookings.team_booking_group_id (%)',
                p_booking_id, v_team_item_group_id, v_team_booking_group_id;
        END IF;

    ELSE
        RAISE EXCEPTION
            'booking %: at most one TEAM booking_item is allowed, found %',
            p_booking_id, v_team_item_count;
    END IF;
END;
$$;
"""

BOOKING_ITEMS_SHAPE_TRIGGER_FUNCTION = """
CREATE OR REPLACE FUNCTION trg_validate_shape_from_booking_items()
RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    PERFORM validate_booking_shape(COALESCE(NEW.booking_id, OLD.booking_id));
    RETURN NULL;
END;
$$;
"""

BOOKING_ITEMS_SHAPE_TRIGGER = """
CREATE CONSTRAINT TRIGGER ct_booking_items_shape_validation
AFTER INSERT OR UPDATE OR DELETE ON booking_items
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION trg_validate_shape_from_booking_items();
"""

RESERVATIONS_SHAPE_TRIGGER_FUNCTION = """
CREATE OR REPLACE FUNCTION trg_validate_shape_from_worker_reservations()
RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    PERFORM validate_booking_shape(COALESCE(NEW.booking_id, OLD.booking_id));
    RETURN NULL;
END;
$$;
"""

RESERVATIONS_SHAPE_TRIGGER = """
CREATE CONSTRAINT TRIGGER ct_worker_reservations_shape_validation
AFTER INSERT OR UPDATE OR DELETE ON worker_reservations
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION trg_validate_shape_from_worker_reservations();
"""


def upgrade() -> None:
    op.execute(AGREED_RATE_FUNCTION)
    op.execute(AGREED_RATE_TRIGGER)

    op.execute(SHAPE_VALIDATION_FUNCTION)
    op.execute(BOOKING_ITEMS_SHAPE_TRIGGER_FUNCTION)
    op.execute(BOOKING_ITEMS_SHAPE_TRIGGER)
    op.execute(RESERVATIONS_SHAPE_TRIGGER_FUNCTION)
    op.execute(RESERVATIONS_SHAPE_TRIGGER)


def downgrade() -> None:
    op.execute(
        "DROP TRIGGER IF EXISTS ct_worker_reservations_shape_validation ON worker_reservations"
    )
    op.execute("DROP FUNCTION IF EXISTS trg_validate_shape_from_worker_reservations()")
    op.execute(
        "DROP TRIGGER IF EXISTS ct_booking_items_shape_validation ON booking_items"
    )
    op.execute("DROP FUNCTION IF EXISTS trg_validate_shape_from_booking_items()")
    op.execute("DROP FUNCTION IF EXISTS validate_booking_shape(uuid)")

    op.execute(
        "DROP TRIGGER IF EXISTS booking_items_agreed_rate_immutable ON booking_items"
    )
    op.execute("DROP FUNCTION IF EXISTS prevent_agreed_rate_change()")
