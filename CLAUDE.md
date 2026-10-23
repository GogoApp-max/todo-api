# todo-api — learning project

This is a **learning project**. The user is a junior/mid React frontend engineer learning backend (Python, FastAPI, PostgreSQL, SQLAlchemy, Alembic, pytest).

The full plan, the current phase and the progress log are in @LEARNING_PLAN.md.

## How to help
- **Don't write the exercise or deliverable code for the user** unless they explicitly ask. Review their code, explain concepts, and give hints, starting small and getting more specific only if they're still stuck.
- Setup, boilerplate and config (installing packages, docker-compose, wiring Alembic) are fine to do directly. Explain what each piece is for.
- Relate new concepts to frontend/JS/TS equivalents where it helps.
- Use current idioms: SQLAlchemy 2.0 style (`Mapped[]`, `select()`), Pydantic v2, Python 3.13 type hints. Point out when tutorials online use outdated patterns.
- When a phase or exercise is finished, tick its checkbox and add a dated line to the progress log in LEARNING_PLAN.md.

## Commands
- Always use `uv run ...`. The system `python3` is 3.10 (pyenv), not the project's 3.13.
- `uv run pytest` · `uv run ruff check .` · `uv run ruff format .`
