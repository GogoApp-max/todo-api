todos = [
    {"id": 1, "title": "Buy milk", "completed": False},
    {"id": 2, "title": "Learn Python", "completed": True},
    {"id": 3, "title": "Walk dog", "completed": False},  # dict
]
# list

# uv run python phase0/basics.py
# uv run ruff format phase0


def summarize(todos: list[dict]) -> str:  # function
    completed_count = sum(1 for t in todos if t["completed"])
    remaining_count = len(todos) - completed_count
    return (
        f"{len(todos)} todos, {completed_count} completed, {remaining_count} remaining"
    )


# f"{n} todos". Any expression can go inside {}.

if __name__ == "__main__":
    # Code inside runs only when the file is run directly, not when it's imported.
    print(summarize(todos))

    # for t in todos -> loop through the list
    # list comprehension -> [t["title"] for t in todos if not t["completed"]]
    print([t["title"] for t in todos if not t["completed"]])

    print(
        {t["id"]: t["title"] for t in todos if not t["completed"]}
    )  # dict comprehension

    print(todos[0].get("due"))
    print(todos[0].get("due", "No due date"))

    try:
        print(todos[0]["due"])
    except KeyError as e:
        print(f"KeyError: {e}")
# .get() is for keys that are expected to be missing sometimes, while [] says the key must exist and should fail loudly if it doesn't.
