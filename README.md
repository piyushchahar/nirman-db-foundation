# Nirman — TASK-DB-FOUNDATION-001

Database foundation only: PostgreSQL schema, Alembic migrations,
SQLAlchemy models, and a real-Postgres pytest suite. No business logic,
no services, no API, no frontend (see `nirman-db-foundation-final-approved.md`
§2 and this report's OUT-OF-SCOPE CONFIRMATION section).

## Why this README exists

This repository was built in a sandboxed environment with **no network
access and no PostgreSQL installed**, so none of the verification steps
below (`alembic upgrade head`, the test suite, the concurrency test,
formatter/linter/type-checker) have actually been executed against a
real database yet. Everything below is written so you can run the real
verification yourself with one `docker-compose` command. Please run all
of these and treat any failure as a bug report — do not assume they
pass just because the code looks right on inspection.

## Run it

```bash
# 1. Start PostgreSQL 16 and a Python runner container with this repo mounted.
docker compose up -d postgres runner

# 2. Wait for postgres healthcheck (docker compose up already waits on it
#    via `depends_on: condition: service_healthy`, but you can confirm):
docker compose ps

# 3. Install dependencies inside the runner container.
docker compose exec runner pip install -e ".[dev]"

# 4. Run the full migration chain against the dev database.
docker compose exec runner alembic upgrade head

# 5. Inspect the resulting schema (tables/enums/extensions/triggers/exclusion
#    constraint) — e.g. with psql:
docker compose exec postgres psql -U nirman -d nirman -c '\dt'
docker compose exec postgres psql -U nirman -d nirman -c '\dT+'
docker compose exec postgres psql -U nirman -d nirman -c "SELECT extname FROM pg_extension;"
docker compose exec postgres psql -U nirman -d nirman -c "SELECT tgname FROM pg_trigger WHERE NOT tgisinternal;"
docker compose exec postgres psql -U nirman -d nirman -c "SELECT conname FROM pg_constraint WHERE contype = 'x';"

# 6. Run the full test suite (creates/recreates its own nirman_test database
#    automatically via tests/db/conftest.py — does not touch the `nirman` dev DB).
docker compose exec runner pytest tests/db -v

# 6a. Run just the concurrency test:
docker compose exec runner pytest tests/db/test_worker_reservation_concurrency.py -v

# 7. Formatter / linter / type checker:
docker compose exec runner black --check .
docker compose exec runner ruff check .
docker compose exec runner mypy backend/app

# 8. Migration downgrade/upgrade verification (this is also exercised
#    automatically by tests/db/test_migrations.py on its own ephemeral
#    database, but you can also do it by hand against the dev DB):
docker compose exec runner alembic downgrade base
docker compose exec postgres psql -U nirman -d nirman -c '\dt'   # should be empty except alembic_version
docker compose exec runner alembic upgrade head
docker compose exec postgres psql -U nirman -d nirman -c '\dt'   # full schema again

# 9. Tear down.
docker compose down -v
```

## What to look for

- Step 4 should complete with 17 migrations applied (`0001` .. `0017`),
  no errors.
- Step 6 should report all tests passing. If `test_worker_reservation_concurrency.py`
  is flaky (e.g. under very slow/loaded CI), it's worth re-running it a
  few times — it uses a `threading.Barrier` to line up two real
  transactions, which is inherently timing-sensitive, though the
  assertion itself (exactly one COMMIT, exactly one ExclusionViolation)
  should hold regardless of exact timing.
- Step 8's downgrade should drop every domain table/enum/extension
  cleanly. If it doesn't, that's a real bug in a `downgrade()` function
  — please report which migration failed.

## Repository layout

```
nirman/
├── backend/
│   ├── app/
│   │   ├── main.py            # health-check-only FastAPI stub, no business logic
│   │   ├── db/                # engine/session/declarative base
│   │   ├── models/             # SQLAlchemy models, one file per table group
│   │   └── core/config.py      # DATABASE_URL / TEST_DATABASE_URL resolution
│   └── alembic/
│       ├── env.py
│       └── versions/           # 0001..0017, dependency-ordered
├── tests/db/                   # real-PostgreSQL pytest suite (14 files + conftest)
├── alembic.ini
├── pyproject.toml
└── docker-compose.yml
```

See the final implementation report delivered in chat for the full
CONSTRAINTS / TRIGGERS / INDEXES / DEFERRED ARCHITECTURE ITEMS breakdown.
