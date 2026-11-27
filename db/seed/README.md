# Student 2 seed instructions

Owner: Student 2. Student 1 does not own seed data or hidden tests.

Use this directory to load problem statements, sample cases, and hidden test cases into PostgreSQL. Problem data comes from the private `code-evaluation-problems` repository and must not be copied into API or worker images.

## Expected inputs

```text
problems/<problem-slug>/statement.md
problems/<problem-slug>/sample.json
problems/<problem-slug>/hidden.json
```

Each JSON file should contain test cases with these fields:

```json
{
  "stdin": "2\n",
  "expected_stdout": "4\n",
  "is_hidden": true
}
```

## Seed script contract

Implement `db/seed/seed.py` to:

1. Read problem metadata from the private problems repo.
2. Insert or update rows in `problems`.
3. Insert or update rows in `test_cases`.
4. Use stable UUIDs so repeated seeding is idempotent.
5. Mark sample cases with `is_hidden=false` and hidden cases with `is_hidden=true`.
6. Print a summary of inserted/updated problems and test cases.

## Example command

```bash
python3 db/seed/seed.py \
  --problems-dir ../code-evaluation-problems/problems \
  --database-url "$DATABASE_URL"
```

## Rules

- Never expose hidden expected output through `/api/v1/problems`.
- Never commit secrets, private problem data, or generated database dumps.
- Seed only after `alembic upgrade head`.
- Add a small sample problem for local API/worker smoke tests.
