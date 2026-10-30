# dataclasses, methods with self, and decorators.

import functools
from dataclasses import dataclass, field
from datetime import date


def log_call(fn):
    @functools.wraps(fn)  # copies fn's __name__, docstring, etc. onto wrapper
    def wrapper(*args, **kwargs):  # collect any positional + keyword args
        print(f"Calling {fn.__name__} with args={args} kwargs={kwargs}")
        result = fn(*args, **kwargs)  # spread them back into the original
        print(f"{fn.__name__} returned {result!r}")
        return result

    return wrapper  # the function itself, not wrapper() — that would call it now


def log_call_no_wraps(fn):
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)

    return wrapper


@dataclass  # decorator that adds methods to the class, like __init__ and __repr__
class Todo:
    id: int
    title: str
    completed: bool = False
    due: date | None = None
    tags: list[str] = field(default_factory=list)  # a new list per instance

    @log_call
    def mark_done(self) -> None:  # self: Python's explicit "this"
        self.completed = True


@log_call
def add(a: int, b: int) -> int:
    return a + b


@log_call_no_wraps
def subtract(a: int, b: int) -> int:
    return a - b


if __name__ == "__main__":
    print("--- dataclass + method + decorator ---")
    todo = Todo(id=1, title="Buy milk")
    print(todo)  # auto-generated __repr__
    todo.mark_done()
    print(todo)  # completed=True
    add(2, b=3)  # args=(2,) kwargs={'b': 3}

    print("--- equality ---")
    t1 = Todo(id=2, title="Walk dog", due=date(2026, 10, 30))
    t2 = Todo(id=2, title="Walk dog", due=date(2026, 10, 30))
    print(t1 == t2)  # True — @dataclass generates __eq__ comparing fields
    print(t1 is t2)  # False — still two separate objects

    print("--- missing required field ---")
    try:
        Todo(title="x")  # type: ignore[call-arg]
    except TypeError as e:
        print(f"TypeError: {e}")

    print("--- functools.wraps ---")
    print(todo.mark_done.__name__)  # mark_done
    print(add.__name__)  # add
    print(subtract.__name__)  # wrapper — the original name is lost

    print("--- mutable default in a dataclass ---")
    try:
        # A decorator runs when the class is defined, so the error happens here,
        # before any instance is created.
        @dataclass
        class BadTodo:
            tags: list[str] = []  # noqa: RUF008 — the bug on purpose

    except ValueError as e:
        print(f"ValueError: {e}")

    a = Todo(id=3, title="a")
    b = Todo(id=4, title="b")
    a.tags.append("home")
    print(a.tags, b.tags)  # ['home'] [] — each instance got its own list
