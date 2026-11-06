import argparse
import json
import sys
from dataclasses import asdict
from datetime import date
from pathlib import Path

from models import Todo

# Always next to this script, no matter which directory you run it from
TODOS_FILE = Path(__file__).parent / "todos.json"


class TodoNotFoundError(Exception):
    """Raised when a todo with the specified ID is not found."""


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


def create_todo(title: str, completed: bool = False, due: date | None = None) -> Todo:
    todos = load_todos()
    new_id = max((todo.id for todo in todos), default=0) + 1
    new_todo = Todo(id=new_id, title=title, completed=completed, due=due)
    todos.append(new_todo)
    save_todos(todos)
    return new_todo


def list_todos() -> list[Todo]:
    return load_todos()


def update_todo(
    todo_id: int, title: str | None = None, completed: bool | None = None
) -> Todo:
    todos = load_todos()
    for todo in todos:
        if todo.id == todo_id:
            if title is not None:
                todo.title = title
            if completed is not None:
                todo.completed = completed
            save_todos(todos)
            return todo
    raise TodoNotFoundError(f"Todo with ID {todo_id} not found.")


def delete_todo(todo_id: int) -> None:
    todos = load_todos()
    new_todos = [todo for todo in todos if todo.id != todo_id]
    if len(new_todos) == len(todos):
        raise TodoNotFoundError(f"Todo with ID {todo_id} not found.")
    save_todos(new_todos)


def format_todo(todo: Todo) -> str:
    check = "x" if todo.completed else " "
    due = f"  (due {todo.due.isoformat()})" if todo.due is not None else ""
    return f"[{check}] {todo.id}  {todo.title}{due}"


def main() -> None:
    # 1. Define the commands first...
    parser = argparse.ArgumentParser(description="Todo CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Add a todo")
    add_parser.add_argument("title", help="Title of the todo")
    add_parser.add_argument(
        "--due", type=date.fromisoformat, help="Due date (YYYY-MM-DD)"
    )

    subparsers.add_parser("list", help="List all todos")

    done_parser = subparsers.add_parser("done", help="Mark a todo as done")
    done_parser.add_argument("id", type=int, help="ID of the todo")

    delete_parser = subparsers.add_parser("delete", help="Delete a todo")
    delete_parser.add_argument("id", type=int, help="ID of the todo")

    # 2. ...then parse the command line
    args = parser.parse_args()

    # 3. Dispatch to the CRUD functions
    try:
        if args.command == "add":
            todo = create_todo(args.title, due=args.due)
            print(f"Added {todo.id}: {todo.title}")
        elif args.command == "list":
            todos = list_todos()
            if not todos:
                print("No todos yet.")
            for todo in todos:
                print(format_todo(todo))
        elif args.command == "done":
            todo = update_todo(args.id, completed=True)
            print(f"Done {todo.id}: {todo.title}")
        elif args.command == "delete":
            delete_todo(args.id)
            print(f"Deleted {args.id}")
    except TodoNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)  # errors go to stderr, like console.error
        sys.exit(1)  # non-zero exit code = failure, like process.exit(1)


if __name__ == "__main__":
    main()
