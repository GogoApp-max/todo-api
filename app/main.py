from datetime import date
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, field_validator


class TodoCreate(BaseModel):
    title: str
    due: date | None = None


class TodoRead(BaseModel):
    id: int
    title: str
    completed: bool
    due: date | None = None


class TodoUpdate(BaseModel):
    """PATCH body: every field is optional; only the fields sent are changed."""

    title: str | None = None
    completed: bool | None = None
    due: date | None = None  # null is allowed here: it clears the due date

    @field_validator("title", "completed")
    @classmethod
    def not_null(cls, value: object) -> object:
        # Runs only for fields the client actually sent (defaults aren't
        # validated), so leaving a field out is fine but sending null is a 422.
        if value is None:
            raise ValueError("may be omitted, but not null")
        return value


class TodoReplace(BaseModel):
    """PUT body: the complete todo, so every field except `due` is required."""

    title: str
    completed: bool
    due: date | None = None


app = FastAPI()

# In-memory storage for todos.
# Use a dict for O(1) access by ID, instead of a list which needs an O(n) search.
# Store data in the shape that makes your lookups fast, and return it in the
# shape the client needs. You'll see this split again between database tables
# and response schemas.
todos: dict[int, TodoRead] = {}


def get_todo_or_404(todo_id: int) -> TodoRead:
    todo = todos.get(todo_id)
    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo


@app.get("/todos")
def get_todos(
    completed: bool | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[TodoRead]:
    result = list(todos.values())
    if completed is not None:  # filter first...
        result = [todo for todo in result if todo.completed == completed]
    return result[offset : offset + limit]  # ...then paginate


@app.get("/todos/{todo_id}")
def get_todo(todo_id: int) -> TodoRead:
    return get_todo_or_404(todo_id)


@app.post("/todos", status_code=201)
def create_todo(todo: TodoCreate) -> TodoRead:
    new_id = max(todos.keys(), default=0) + 1
    new_todo = TodoRead(id=new_id, title=todo.title, completed=False, due=todo.due)
    todos[new_id] = new_todo
    return new_todo


@app.put("/todos/{todo_id}")
def update_todo(todo_id: int, todo: TodoReplace) -> TodoRead:
    get_todo_or_404(todo_id)  # 404 if missing; the old values aren't needed
    updated_todo = TodoRead(
        id=todo_id, title=todo.title, completed=todo.completed, due=todo.due
    )
    todos[todo_id] = updated_todo
    return updated_todo


@app.delete("/todos/{todo_id}", status_code=204)
def delete_todo(todo_id: int) -> None:
    get_todo_or_404(todo_id)
    del todos[todo_id]


@app.patch("/todos/{todo_id}")
def patch_todo(todo_id: int, todo: TodoUpdate) -> TodoRead:
    existing_todo = get_todo_or_404(todo_id)
    changes = todo.model_dump(exclude_unset=True)  # only the fields that were sent
    updated_todo = existing_todo.model_copy(update=changes)  # {...todo, ...changes}
    todos[todo_id] = updated_todo
    return updated_todo
