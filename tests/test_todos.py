import pytest

# --- POST /todos ---


def test_create_todo(client):
    response = client.post("/todos", json={"title": "Buy milk"})

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Buy milk"
    assert body["completed"] is False
    assert body["due"] is None
    assert isinstance(body["id"], int)


def test_create_todo_with_due_date(client):
    response = client.post("/todos", json={"title": "Dentist", "due": "2026-11-20"})

    assert response.status_code == 201
    assert response.json()["due"] == "2026-11-20"


def test_create_todo_ignores_client_supplied_id(client, make_todo):
    make_todo()

    response = client.post("/todos", json={"title": "x", "id": 999})

    assert response.json()["id"] != 999


def test_create_todo_ids_are_unique(make_todo):
    ids = [make_todo()["id"] for _ in range(3)]

    assert len(set(ids)) == 3


@pytest.mark.parametrize(
    "body",
    [
        {},  # title missing
        {"title": None},  # title must be a string
        {"title": "x", "due": "tomorrow"},  # not a date
        {"title": "x", "due": "2026-13-01"},  # month 13
    ],
    ids=["missing-title", "null-title", "due-not-a-date", "due-invalid-month"],
)
def test_create_todo_invalid_body_returns_422(client, body):
    response = client.post("/todos", json=body)

    assert response.status_code == 422


# --- GET /todos/{id} ---


def test_get_todo(client, todo):
    response = client.get(f"/todos/{todo['id']}")

    assert response.status_code == 200
    assert response.json() == todo


def test_get_missing_todo_returns_404(client):
    response = client.get("/todos/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Todo not found"}


def test_get_todo_non_integer_id_returns_422(client):
    response = client.get("/todos/abc")

    assert response.status_code == 422


# --- GET /todos (list, filter, pagination) ---


def test_list_todos_empty(client):
    response = client.get("/todos")

    assert response.status_code == 200
    assert response.json() == []


def test_list_todos_returns_all_in_creation_order(client, make_todo):
    created = [make_todo("A"), make_todo("B"), make_todo("C")]

    response = client.get("/todos")

    assert response.json() == created


@pytest.mark.parametrize(
    ("completed", "expected_titles"),
    [("true", ["B", "D"]), ("false", ["A", "C"])],
)
def test_list_todos_filters_by_completed(client, make_todo, completed, expected_titles):
    make_todo("A")
    make_todo("B", completed=True)
    make_todo("C")
    make_todo("D", completed=True)

    response = client.get(f"/todos?completed={completed}")

    assert [t["title"] for t in response.json()] == expected_titles


@pytest.mark.parametrize(
    ("query", "expected_titles"),
    [
        ("limit=2", ["A", "B"]),
        ("limit=2&offset=2", ["C", "D"]),
        ("offset=4", ["E"]),
        ("offset=100", []),  # past the end: empty list, not an error
    ],
)
def test_list_todos_pagination(client, make_todo, query, expected_titles):
    for title in "ABCDE":
        make_todo(title)

    response = client.get(f"/todos?{query}")

    assert response.status_code == 200
    assert [t["title"] for t in response.json()] == expected_titles


def test_list_todos_default_limit_is_10(client, make_todo):
    for i in range(12):
        make_todo(f"Todo {i}")

    response = client.get("/todos")

    assert len(response.json()) == 10


def test_list_todos_filters_before_paginating(client, make_todo):
    make_todo("A")
    make_todo("B", completed=True)
    make_todo("C")
    make_todo("D", completed=True)

    response = client.get("/todos?completed=true&limit=2")

    # Paginating first would take A, B and then filter down to just [B]
    assert [t["title"] for t in response.json()] == ["B", "D"]


@pytest.mark.parametrize(
    "query",
    ["limit=0", "limit=101", "limit=abc", "offset=-1", "completed=maybe"],
)
def test_list_todos_invalid_query_returns_422(client, query):
    response = client.get(f"/todos?{query}")

    assert response.status_code == 422


# --- PATCH /todos/{id} ---


def test_patch_changes_only_sent_fields(client, todo):
    response = client.patch(f"/todos/{todo['id']}", json={"completed": True})

    assert response.status_code == 200
    assert response.json() == {**todo, "completed": True}


def test_patch_null_due_clears_it(client, todo):
    response = client.patch(f"/todos/{todo['id']}", json={"due": None})

    assert response.json()["due"] is None


def test_patch_empty_body_changes_nothing(client, todo):
    response = client.patch(f"/todos/{todo['id']}", json={})

    assert response.status_code == 200
    assert response.json() == todo


def test_patch_is_saved(client, todo):
    client.patch(f"/todos/{todo['id']}", json={"title": "Buy oat milk"})

    response = client.get(f"/todos/{todo['id']}")

    assert response.json()["title"] == "Buy oat milk"


@pytest.mark.parametrize("field", ["title", "completed"])
def test_patch_null_required_field_returns_422(client, todo, field):
    response = client.patch(f"/todos/{todo['id']}", json={field: None})

    assert response.status_code == 422
    # ...and the todo is unchanged
    assert client.get(f"/todos/{todo['id']}").json() == todo


def test_patch_missing_todo_returns_404(client):
    response = client.patch("/todos/999", json={"completed": True})

    assert response.status_code == 404


# --- PUT /todos/{id} ---


def test_put_replaces_whole_todo(client, todo):
    response = client.put(
        f"/todos/{todo['id']}", json={"title": "New title", "completed": True}
    )

    assert response.status_code == 200
    # `due` wasn't sent, so a replace resets it (a PATCH would have kept it)
    assert response.json() == {
        "id": todo["id"],
        "title": "New title",
        "completed": True,
        "due": None,
    }


def test_put_missing_field_returns_422(client, todo):
    response = client.put(f"/todos/{todo['id']}", json={"title": "Only title"})

    assert response.status_code == 422


def test_put_missing_todo_returns_404(client):
    response = client.put("/todos/999", json={"title": "x", "completed": False})

    assert response.status_code == 404


# --- DELETE /todos/{id} ---


def test_delete_todo(client, todo):
    response = client.delete(f"/todos/{todo['id']}")

    assert response.status_code == 204
    assert response.content == b""  # 204 means no body
    assert client.get(f"/todos/{todo['id']}").status_code == 404


def test_delete_missing_todo_returns_404(client):
    response = client.delete("/todos/999")

    assert response.status_code == 404


def test_delete_twice_returns_404(client, todo):
    client.delete(f"/todos/{todo['id']}")

    response = client.delete(f"/todos/{todo['id']}")

    assert response.status_code == 404
