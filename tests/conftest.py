import pytest
from fastapi.testclient import TestClient

from app.main import app, todos


@pytest.fixture(autouse=True)
def clear_todos():
    """Give every test an empty store, so tests can't affect each other."""
    todos.clear()  # setup: runs before each test
    yield  # the test runs here
    todos.clear()  # teardown: runs after each test, even if it failed


@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client


@pytest.fixture
def todo(client) -> dict:
    """A todo that already exists. Fixtures can use other fixtures."""
    response = client.post("/todos", json={"title": "Buy milk", "due": "2026-11-20"})
    return response.json()


@pytest.fixture
def make_todo(client):
    """Factory fixture: returns a function, so a test can create as many todos as it needs."""

    def _make_todo(title: str = "Todo", completed: bool = False, **fields) -> dict:
        created = client.post("/todos", json={"title": title, **fields}).json()
        if completed:  # POST always creates incomplete todos, so PATCH afterwards
            created = client.patch(
                f"/todos/{created['id']}", json={"completed": True}
            ).json()
        return created

    return _make_todo
