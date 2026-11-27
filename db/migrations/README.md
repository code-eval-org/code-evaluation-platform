# Student 2 migration instructions

Owner: Student 2. Student 1 does not create or edit migrations.

This directory is reserved for Alembic configuration and revision files that create the schema defined in `db/README.md`.

## Setup

```bash
pip install -r db/requirements.txt
set -a
source db/.env.example
set +a
cd db
alembic init migrations
```

Replace the generated `sqlalchemy.url` with `DATABASE_URL` from the environment in `db/migrations/env.py`. Keep credentials out of committed files.

## First revision

```bash
cd db
alembic revision -m "create evaluation schema"
```

Implement the four tables in this order:

1. `problems`
2. `test_cases`
3. `submissions`
4. `test_results`

Add the indexes and unique constraint listed in `db/README.md`.

## Commands

```bash
alembic upgrade head
alembic downgrade -1
alembic current
alembic history
```

## Rules

- Every schema change needs a new revision; never edit an applied revision.
- Generated SQL must work on PostgreSQL.
- Do not store hidden tests in migration files; load them through `db/seed/seed.py`.
- Coordinate changes to columns used by `shared/store_contracts.py` with Student 1 before merging.
