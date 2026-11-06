# Backend Learning Plan — Todo API

Learning Python, FastAPI, PostgreSQL, SQLAlchemy 2.0, Alembic and pytest by building a Todo API.
Background: React frontend engineer (junior/mid), new to backend.

## Stack
- **Core:** Python 3.13, FastAPI, Pydantic v2, PostgreSQL, SQLAlchemy 2.0 (`Mapped[]` style), Alembic, pytest
- **Tooling:** uv (packages/venv), ruff (lint + format), pydantic-settings (config), Docker Compose (Postgres only), httpx/TestClient
- **Deferred:** async SQLAlchemy, Redis, Celery, Docker for the app itself, deploy

## Domain (built up in layers)
- Todo → plain CRUD
- List has many Todos → one-to-many
- Todos ↔ Tags → many-to-many
- User + auth → every todo belongs to a user; authorization

## Commands
- `uv run python file.py` — run with the project's Python (system python3 is 3.10 — don't use it)
- `uv add <pkg>` / `uv add --dev <pkg>` — install
- `uv run pytest` · `uv run ruff check .` · `uv run ruff format .`

---

## Phase 0 — Python basics ⬅️ CURRENT
Concepts: syntax compared to JS, type hints, comprehensions, classes/`@dataclass`, decorators, exceptions, context managers (`with`), modules, uv/virtualenvs.

Exercises (in `phase0/`):
- [x] `basics.py` — `summarize(todos) -> str` with f-string; list comprehension (incomplete titles); dict comprehension `{id: title}`; `.get()` vs `[]` on missing key
- [x] `gotchas.py` — mutable default arg `def add_item(item, items=[])` bug + fix; `is` vs `==`; falsy values
- [x] `models.py` — `Todo` dataclass (`id`, `title`, `completed=False`, `due: date | None = None`), `mark_done()`, a `@log_call` decorator
- [x] `todo_cli.py` — **deliverable**: CLI (`add` / `list` / `done` / `delete`) saving to `todos.json`; argparse subcommands, json, pathlib, `with open`, custom `TodoNotFoundError`; split into `create_todo` / `list_todos` / `update_todo` / `delete_todo`
- [ ] (optional) `tests/test_todo_cli.py` — 3 pytest tests for the CRUD functions

Done when you can answer: What does a decorator actually do? Why is `def f(x=[])` a bug? What does `with` guarantee?

## Phase 1 — FastAPI, in-memory
Path/query params, request bodies, Pydantic schemas (`TodoCreate` / `TodoUpdate` / `TodoRead`), status codes (201/204/404/422), `HTTPException`, `/docs`, `Depends()`, `def` vs `async def`.
**Deliverable:** CRUD `/todos` stored in a dict, plus `?completed=` filter and `limit`/`offset` pagination.
Done when: you can explain PUT vs PATCH, and why the API returns 422.

## Phase 2 — pytest (then keep testing in every phase)
Discovery, `assert`, `-k`, fixtures (scopes, `yield`), `parametrize`, `TestClient`, `pytest-cov`.
**Deliverable:** tests for every Phase 1 endpoint, covering success and failure paths. Try TDD for at least one feature per phase.

## Phase 3 — PostgreSQL + raw SQL
Postgres via docker compose, psql/GUI, hand-written CRUD SQL, constraints, `timestamptz`, foreign keys, JOINs, indexes and `EXPLAIN`, transactions.
**Deliverable:** `schema.sql` (users, lists, todos, tags, todo_tags) plus ~10 hand-written queries.
Done when: you can query "all incomplete todos in list X with tag Y".

## Phase 4 — SQLAlchemy 2.0
Engine/Session lifecycle (one session per request via `Depends`), `Mapped[]` models, `select()` / `scalars()` / `get()`, commit/refresh, ORM models kept separate from Pydantic schemas (`from_attributes=True`), `echo=True`, pydantic-settings + `.env`.
**Deliverable:** Todo CRUD backed by Postgres (temporarily using `create_all()`).
Done when: you can explain `commit()` vs `flush()`, and what happens when you forget to commit.

## Phase 5 — Alembic
`alembic init`, wiring `env.py`, autogenerate (always read what it produced) vs hand-written migrations, upgrade/downgrade/history. Practice: add `due_date`, rename a column, add a NOT NULL column to a table that already has data.
**Deliverable:** `create_all()` removed; the whole schema comes from migrations.

## Phase 6 — Relationships
Lists → todos (`relationship`, `back_populates`, cascade), todos ↔ tags (association table), N+1 problem fixed with `selectinload` / `joinedload`, nested response schemas.
**Deliverable:** `/lists`, `/lists/{id}/todos`, `/tags`, filter todos by tag, each with migrations and tests.

## Phase 7 — Testing against a real database
Separate test DB, transaction-rollback-per-test fixture, `app.dependency_overrides`, factories, unit vs integration tests.
**Deliverable:** isolated suite against Postgres that runs in under ~10s.

## Phase 8 — Project structure
`routers/` `schemas/` `models/` `services/` `core/config.py` `db/session.py`, thin routers, exception handlers, consistent error response shape, logging, ruff (optionally mypy).
**Deliverable:** refactor done with all tests still passing.

## Phase 9 — Users and authentication
Password hashing (pwdlib/argon2), register/login → JWT, `get_current_user`, protected routes, ownership checks (404 rather than 403 for other users' resources), migration adding `user_id`, auth fixtures, "user A can't touch user B's todo" tests.

## Phase 10 — React frontend
CORS, small React (or TanStack Query) app, optional `openapi-typescript` types, token storage trade-offs.

## Optional extras
Async (`AsyncSession` + asyncpg), Docker for the app, GitHub Actions CI with a Postgres service, deploy (Railway/Fly/Render), soft deletes, cursor pagination, full-text search.

---

## Progress log
- 2026-10-19 — Plan created; project set up with `uv init` (Python 3.13, pytest, ruff). Starting Phase 0.
- 2026-10-23 — Phase 0: `basics.py` done (f-strings, list/dict comprehensions, generator expression, `.get()` vs `[]`, `KeyError`). Repo pushed to GitHub.
- 2026-10-23 — Phase 0: `gotchas.py` done (mutable default args, `is` vs `==` + small-int cache, falsy values, `is None` vs `not x`). Code written by Claude on request.
- 2026-10-23 — Phase 0: `models.py` done (`@dataclass`, `self`, `@log_call` decorator with `*args/**kwargs` + `functools.wraps`, `field(default_factory=list)`). Code written by Claude on request.
- 2026-11-06 — Phase 0: `todo_cli.py` deliverable done (JSON storage with date round trip, CRUD + `TodoNotFoundError`, argparse subcommands, stderr + exit codes). Storage/CRUD written by the user with fixes; `main()` fixed by Claude on request.
