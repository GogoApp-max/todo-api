# Python & FastAPI cheatsheet

Quick reference for a JS/TS developer, built up while working through `LEARNING_PLAN.md`.

**Contents**

- [Python](#python)
  - [dict: like a JS object / `Map`](#dict-like-a-js-object--map)
- [FastAPI](#fastapi)
  - [Path vs query vs body](#path-vs-query-vs-body)
  - [Status codes](#status-codes)
  - [Why 422?](#why-422)

---

# Python

## dict: like a JS object / `Map`

```python
todos = {1: "Buy milk", 2: "Walk dog"}
```

### Reading

| Python | JS equivalent | Notes |
|---|---|---|
| `d[k]` | `obj[k]` | Missing key → **raises `KeyError`** (JS gives `undefined`). Use when the key *must* exist |
| `d.get(k)` | `obj[k]` | Missing key → `None` |
| `d.get(k, default)` | `obj[k] ?? default` | Missing key → `default` |
| `k in d` | `k in obj` / `map.has(k)` | Checks **keys**, not values |
| `len(d)` | `Object.keys(obj).length` / `map.size` | |

### Iterating

| Python | JS equivalent | Returns |
|---|---|---|
| `d.keys()` | `Object.keys(obj)` | View of keys |
| `d.values()` | `Object.values(obj)` | View of values |
| `d.items()` | `Object.entries(obj)` | View of `(key, value)` tuples |
| `for k in d:` | `for (const k in obj)` | Loops over **keys** |
| `for k, v in d.items():` | `for (const [k, v] of Object.entries(obj))` | Tuple unpacking |

> **Views are live, not copies.** If the dict changes, the view changes too. Wrap the
> view in `list(...)` when you need a fixed snapshot, e.g. to return from an API:
> `list(todos.values())`.
>
> **Order is insertion order**, as in JS (guaranteed since Python 3.7).

### Writing

| Python | JS equivalent | Notes |
|---|---|---|
| `d[k] = v` | `obj[k] = v` | Adds the key, or overwrites it if it exists |
| `del d[k]` | `delete obj[k]` | Missing key → `KeyError` |
| `d.pop(k)` | — | Removes the key **and returns its value**. Missing key → `KeyError` |
| `d.pop(k, default)` | — | Missing key → returns `default`, no error |
| `d.update(other)` | `Object.assign(obj, other)` | Merges `other` **into** `d`, mutating it |
| `d \| other` | `{...obj, ...other}` | Returns a **new** merged dict. `other` wins on conflicts |
| `d.setdefault(k, [])` | `obj[k] ??= []` | Returns `d[k]`, setting it to the default first if missing |
| `d.copy()` | `{...obj}` | **Shallow** copy: nested lists/dicts are shared |
| `d.clear()` | — | Empties the dict in place |

### Creating

```python
{}                                   # empty dict
dict(a=1, b=2)                       # {"a": 1, "b": 2}  (string keys only)
dict([("a", 1), ("b", 2)])           # from pairs, like Object.fromEntries(...)
{t.id: t.title for t in todos}       # dict comprehension
```

### Gotchas

- **Don't add or remove keys while looping over the same dict.** It raises
  `RuntimeError: dictionary changed size during iteration`. Loop over a copy instead:
  `for k in list(d):`.
- **`if d.get(k):` vs `if k in d:`.** If the value can be `0`, `""`, `False` or `[]`,
  `.get()` returns something falsy even though the key exists. Use `k in d` or
  `d.get(k) is not None` (see `phase0/gotchas.py`).
- **Keys must be hashable**: `str`, `int`, `tuple` and the like. Lists can't be keys.
- **Shared mutable defaults:** `d.setdefault(k, [])` is safe because it creates a new `[]`
  on each call. Don't use a mutable value as a function's default argument
  (see `phase0/gotchas.py`).

### When to use a dict

**Store data in the shape that makes your lookups fast; return it in the shape the
client needs.** A dict keyed by `id` is a lookup by key (`todos[3]`), like a database
primary key index. A list needs a scan (`next(t for t in todos if t.id == 3)`). APIs
usually *store* collections as dicts or tables and *return* them as JSON arrays.

---

# FastAPI

## Path vs query vs body

```
GET  /todos/3                       GET  /todos?completed=true&limit=2
     └─────┘                             └────┘ └──────────────────┘
      path                                path      query string
   "todo number 3"                   "the todos"  "…only completed ones, max 2"
```

**The path says *which* thing; the query says *how* to show it; the body says *what* to save.**

React Router analogy: path parameter = `/todos/:id` → `useParams()`; query parameter =
`?tab=done&page=2` → `useSearchParams()`.

| | Path | Query | Body |
|---|---|---|---|
| Answers | *Which* resource? | *How* to show it? | *What* to save? |
| Examples | `/todos/3`, `/lists/5/todos` | `?completed=true`, `?limit=10&offset=20`, `?q=milk` | `{"title": "Buy milk"}` |
| Required? | Yes (part of the address) | Usually optional, with a default | Depends on the schema |
| Typical methods | All | Mostly GET | POST / PUT / PATCH (never GET) |
| Missing → | 404 (or no matching route) | Default value | 422 if required fields are missing |
| No match → | **404** | **200 with `[]`** | — |

### Which one? Ask this

> **Would it make sense to bookmark this as a *different thing*?**
> Yes → **path** (`/todos/3` and `/todos/4` are different todos).
> No, it's the *same thing filtered or arranged differently* → **query**.

### How FastAPI decides

You never label parameters. FastAPI looks at the name and the type:

```python
@app.patch("/todos/{todo_id}")
def update_todo(
    todo_id: int,                   # name matches {todo_id} in the path → path
    body: TodoUpdate,               # a BaseModel                         → body
): ...

@app.get("/todos")
def get_todos(
    completed: bool | None = None,                     # anything else → query
    limit: Annotated[int, Query(ge=1, le=100)] = 10,   # query, with constraints
): ...
```

> **Outdated pattern:** tutorials often write `limit: int = Query(10, ge=1)`.
> Current FastAPI recommends `Annotated[int, Query(ge=1)] = 10`.

### Common mistakes

| ❌ Don't | ✅ Do | Why |
|---|---|---|
| `GET /todos/completed` | `GET /todos?completed=true` | A filter isn't a resource. It also **clashes** with `/todos/{todo_id}`: `"completed"` would be parsed as an ID → 422 |
| `GET /todos?id=3` | `GET /todos/3` | The ID identifies the resource, so it belongs in the address |
| `GET /todos/page/2` | `GET /todos?offset=10&limit=10` | A page is a view of the collection, not a separate thing |
| `GET /getTodo/3` | `GET /todos/3` | The HTTP method is already the verb; the path names the resource |

## Status codes

| Code | Name | Meaning | Who sends it in our app |
|---|---|---|---|
| **200** | OK | Success, here's the data | FastAPI's default |
| **201** | Created | A new resource was created | `@app.post(..., status_code=201)` |
| **204** | No Content | Success, nothing to return | `@app.delete(..., status_code=204)` |
| **404** | Not Found | That resource doesn't exist | **Your code**: `raise HTTPException(404)` |
| **422** | Unprocessable Content | The request doesn't match the schema | **FastAPI/Pydantic**, automatically |
| **500** | Internal Server Error | The server crashed (a bug) | Any unhandled exception |

**4xx = the client's fault; 5xx = the server's fault.** Never signal an error with a 200
and an error body (`return {"error": ...}`): clients check the status, not the body.

## Why 422?

> **422 means "your request is well-formed HTTP and JSON, but its content doesn't match
> what the endpoint declared."** FastAPI sends it **automatically**, using Pydantic,
> **before your function runs**.

Everything you declare with type hints becomes a validation rule, and anything that
breaks a rule is a 422:

| Request | Rule it breaks |
|---|---|
| `GET /todos/abc` | path param `todo_id: int` |
| `GET /todos?limit=0` | `Query(ge=1)` |
| `POST /todos` with `{}` | `TodoCreate.title` is required |
| `POST /todos` with `{"due": "tomorrow"}` | `due: date` |
| `PUT /todos/1` without `completed` | `TodoReplace.completed` is required |
| `PATCH /todos/1` with `{"title": null}` | our `@field_validator` |

**422 vs 404:**

| | 422 | 404 |
|---|---|---|
| Question | Is the request **valid**? | Does the thing **exist**? |
| Checked by | FastAPI/Pydantic, from your type hints | **Your code**, after looking it up |
| When | **Before** your function runs | **Inside** your function |
| Example | `/todos/abc`: `abc` can never be an ID | `/todos/999`: a valid ID, but no such todo |

**The error body tells the client exactly what's wrong:**

```json
{"detail": [{
  "type": "greater_than_equal",
  "loc": ["query", "limit"],          // where: query / path / body, then the field
  "msg": "Input should be greater than or equal to 1",
  "input": "0"
}]}
```

`detail` is a **list**, so one response can report several bad fields at once. A React
form can map each `loc` to the matching input field and show `msg` under it.

**Why 422 rather than 400?** 400 Bad Request means "I can't even parse this", e.g.
broken JSON. 422 means "I parsed it fine, but the content is invalid". FastAPI uses 422
for validation errors by default.
