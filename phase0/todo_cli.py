import json
from dataclasses import asdict
from datetime import date
from pathlib import Path

from models import Todo

# Always next to this script, no matter which directory you run it from
TODOS_FILE = Path(__file__).parent / "todos.json"


def todo_to_dict(todo: Todo) -> dict:
    d = asdict(todo)  # a new dict, so changing it doesn't touch the Todo
    if d["due"] is not None:
        d["due"] = d["due"].isoformat()  # date(2026, 11, 5) -> "2026-11-05"
    return d


def todo_from_dict(d: dict) -> Todo:
    if d.get("due") is not None:
        d["due"] = date.fromisoformat(d["due"])  # "2026-11-05" -> date(2026, 11, 5)
    return Todo(**d)  # unpack dict into keyword args


def load_todos() -> list[Todo]:
    if not TODOS_FILE.exists():
        return []
    with open(TODOS_FILE) as f:
        data = json.load(f)
    return [todo_from_dict(item) for item in data]


def save_todos(todos: list[Todo]) -> None:
    # Build the data first: open(..., "w") empties the file immediately,
    # so a crash during conversion would otherwise wipe it.
    data = [todo_to_dict(todo) for todo in todos]
    with open(TODOS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def create_todo(title: str, completed: bool = False) -> Todo:
    todos = load_todos()
    new_id = max((todo.id for todo in todos), default=0) + 1
    new_todo = Todo(id=new_id, title=title, completed=completed)
    todos.append(new_todo)
    save_todos(todos)
    return new_todo


def list_todos() -> list[Todo]:
    return load_todos()


def update_todo(
    todo_id: int, title: str | None = None, completed: bool | None = None
) -> Todo | None:
    todos = load_todos()
    for todo in todos:
        if todo.id == todo_id:
            if title is not None:
                todo.title = title
            if completed is not None:
                todo.completed = completed
            save_todos(todos)
            return todo
    return None


def delete_todo(todo_id: int) -> bool:
    todos = load_todos()
    new_todos = [todo for todo in todos if todo.id != todo_id]
    if len(new_todos) == len(todos):
        return False  # No todo was deleted
    save_todos(new_todos)
    return True


if __name__ == "__main__":
    # Step 1 check: a date survives a save -> load round trip
    save_todos(
        [
            Todo(id=1, title="Buy milk", due=date(2026, 11, 5)),
            Todo(id=2, title="Walk dog"),
        ]
    )
    todos = load_todos()
    print(todos)
    print(type(todos[0].due))  # <class 'datetime.date'>
    print(type(todos[1].due))  # <class 'NoneType'>
