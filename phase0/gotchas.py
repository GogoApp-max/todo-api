# --- 1. Mutable default argument ---


def add_item(item, items=[]):  # noqa: B006 — the bug on purpose
    items.append(item)
    return items


def add_item_fixed(item, items: list | None = None) -> list:
    if items is None:
        items = []  # a new list on every call
    items.append(item)
    return items


# --- 3. Falsy values: the real-world bug ---


def describe_priority_buggy(priority: int | None) -> str:
    if not priority:  # 0 is falsy, so 0 is treated as "missing"
        return "no priority"
    return f"priority {priority}"


def describe_priority(priority: int | None) -> str:
    if priority is None:  # only None means "missing"
        return "no priority"
    return f"priority {priority}"


if __name__ == "__main__":
    print("--- 1. mutable default ---")
    print(add_item("a"))  # ['a']
    print(add_item("b"))  # ['a', 'b'] — same list as the last call
    print(add_item("c", []))  # ['c'] — a list passed in works fine
    print(add_item("d"))  # ['a', 'b', 'd'] — the default list keeps growing
    print(add_item.__defaults__)  # (['a', 'b', 'd'],) — it is stored on the function

    print(add_item_fixed("a"))  # ['a']
    print(add_item_fixed("b"))  # ['b'] — a fresh list each time

    print("--- 2. is vs == ---")
    a = int("256")
    b = int("256")
    print(a == b)  # True — same value
    print(a is b)  # True! CPython caches ints -5..256, so both are one object

    a = int("1000")
    b = int("1000")
    print(a == b)  # True — same value
    print(a is b)  # False — outside the cache, two separate objects

    c = [1, 2]
    d = [1, 2]
    print(c == d)  # True — equal values
    print(c is d)  # False — two different lists in memory

    due = None
    print(due is None)  # True — the one place to use `is`

    print("--- 3. falsy values ---")
    for value in [0, "", [], {}, None, False, "0", [0], float("nan")]:
        print(f"{value!r:>15} → {bool(value)}")

    print(describe_priority_buggy(0))  # "no priority" — wrong, 0 is a real priority
    print(describe_priority(0))  # "priority 0" — correct

# Rule: use is only with None (if x is None). Use == for everything else
# The real-world bug: if not value: treats 0, "" and [] the same as "missing".
