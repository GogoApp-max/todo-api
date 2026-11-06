# Backend cheatsheet: Python, FastAPI, Docker & PostgreSQL

Quick reference for a JS/TS developer, built up while working through `LEARNING_PLAN.md`.

**Contents**

- [Python](#python)
  - [dict: like a JS object / `Map`](#dict-like-a-js-object--map)
- [FastAPI](#fastapi)
  - [Path vs query vs body](#path-vs-query-vs-body)
  - [Status codes](#status-codes)
  - [Why 422?](#why-422)
- [Docker](#docker)
  - [What it is and why we use it](#what-it-is-and-why-we-use-it)
  - [`compose.yaml`](#composeyaml)
  - [Commands](#commands)
- [PostgreSQL](#postgresql)
  - [Server, client and psql](#server-client-and-psql)
  - [The two prompts](#the-two-prompts)
  - [Column types and constraints](#column-types-and-constraints)
  - [CRUD in SQL](#crud-in-sql)
  - [Running and testing SQL](#running-and-testing-sql)
- [Local vs production configuration](#local-vs-production-configuration)

---

# Python

## dict: like a JS object / `Map`

```python
todos = {1: "Buy milk", 2: "Walk dog"}
```

### Reading

| Python              | JS equivalent                          | Notes                                          |
| ------------------- | -------------------------------------- | ---------------------------------------------- |
| `d[k]`              | `obj[k]`                               | Missing key → **`KeyError`** (JS: `undefined`) |
| `d.get(k)`          | `obj[k]`                               | Missing key → `None`                           |
| `d.get(k, default)` | `obj[k] ?? default`                    | Missing key → `default`                        |
| `k in d`            | `k in obj` / `map.has(k)`              | Checks **keys**, not values                    |
| `len(d)`            | `Object.keys(obj).length` / `map.size` |                                                |

> Use `d[k]` when the key **must** exist (a missing key is a bug), and `.get()` when it may legitimately be missing.

### Iterating

| Python                   | JS equivalent                               | Returns                       |
| ------------------------ | ------------------------------------------- | ----------------------------- |
| `d.keys()`               | `Object.keys(obj)`                          | View of keys                  |
| `d.values()`             | `Object.values(obj)`                        | View of values                |
| `d.items()`              | `Object.entries(obj)`                       | View of `(key, value)` tuples |
| `for k in d:`            | `for (const k in obj)`                      | Loops over **keys**           |
| `for k, v in d.items():` | `for (const [k, v] of Object.entries(obj))` | Tuple unpacking               |

> **Views are live, not copies.** If the dict changes, the view changes too. Wrap the
> view in `list(...)` when you need a fixed snapshot, e.g. to return from an API:
> `list(todos.values())`.
>
> **Order is insertion order**, as in JS (guaranteed since Python 3.7).

### Writing

| Python                | JS equivalent               | Notes                                                               |
| --------------------- | --------------------------- | ------------------------------------------------------------------- |
| `d[k] = v`            | `obj[k] = v`                | Adds the key, or overwrites it if it exists                         |
| `del d[k]`            | `delete obj[k]`             | Missing key → `KeyError`                                            |
| `d.pop(k)`            | —                           | Removes the key **and returns its value**. Missing key → `KeyError` |
| `d.pop(k, default)`   | —                           | Missing key → returns `default`, no error                           |
| `d.update(other)`     | `Object.assign(obj, other)` | Merges `other` **into** `d`, mutating it                            |
| `d \| other`          | `{...obj, ...other}`        | Returns a **new** merged dict. `other` wins on conflicts            |
| `d.setdefault(k, [])` | `obj[k] ??= []`             | Returns `d[k]`, setting it to the default first if missing          |
| `d.copy()`            | `{...obj}`                  | **Shallow** copy: nested lists/dicts are shared                     |
| `d.clear()`           | —                           | Empties the dict in place                                           |

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

|                 | Path                         | Query                                               | Body                               |
| --------------- | ---------------------------- | --------------------------------------------------- | ---------------------------------- |
| Answers         | *Which* resource?            | *How* to show it?                                   | *What* to save?                    |
| Examples        | `/todos/3`, `/lists/5/todos` | `?completed=true`, `?limit=10&offset=20`, `?q=milk` | `{"title": "Buy milk"}`            |
| Required?       | Yes (part of the address)    | Usually optional, with a default                    | Depends on the schema              |
| Typical methods | All                          | Mostly GET                                          | POST / PUT / PATCH (never GET)     |
| Missing →       | 404 (or no matching route)   | Default value                                       | 422 if required fields are missing |
| No match →      | **404**                      | **200 with `[]`**                                   | —                                  |

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

| ❌ Don't               | ✅ Do                           | Why                                  |
| ---------------------- | ------------------------------- | ------------------------------------ |
| `GET /todos/completed` | `GET /todos?completed=true`     | A filter isn't a resource (see note) |
| `GET /todos?id=3`      | `GET /todos/3`                  | The ID identifies the resource       |
| `GET /todos/page/2`    | `GET /todos?offset=10&limit=10` | A page is a view, not a resource     |
| `GET /getTodo/3`       | `GET /todos/3`                  | The method is already the verb       |

> `GET /todos/completed` also **clashes** with `/todos/{todo_id}`: FastAPI would try to parse `"completed"` as an ID → 422.

## Status codes

| Code    | Name                  | Meaning                              | Who sends it in our app                   |
| ------- | --------------------- | ------------------------------------ | ----------------------------------------- |
| **200** | OK                    | Success, here's the data             | FastAPI's default                         |
| **201** | Created               | A new resource was created           | `@app.post(..., status_code=201)`         |
| **204** | No Content            | Success, nothing to return           | `@app.delete(..., status_code=204)`       |
| **404** | Not Found             | That resource doesn't exist          | **Your code**: `raise HTTPException(404)` |
| **422** | Unprocessable Content | The request doesn't match the schema | **FastAPI/Pydantic**, automatically       |
| **500** | Internal Server Error | The server crashed (a bug)           | Any unhandled exception                   |

**4xx = the client's fault; 5xx = the server's fault.** Never signal an error with a 200
and an error body (`return {"error": ...}`): clients check the status, not the body.

## Why 422?

> **422 means "your request is well-formed HTTP and JSON, but its content doesn't match
> what the endpoint declared."** FastAPI sends it **automatically**, using Pydantic,
> **before your function runs**.

Everything you declare with type hints becomes a validation rule, and anything that
breaks a rule is a 422:

| Request                                  | Rule it breaks                      |
| ---------------------------------------- | ----------------------------------- |
| `GET /todos/abc`                         | path param `todo_id: int`           |
| `GET /todos?limit=0`                     | `Query(ge=1)`                       |
| `POST /todos` with `{}`                  | `TodoCreate.title` is required      |
| `POST /todos` with `{"due": "tomorrow"}` | `due: date`                         |
| `PUT /todos/1` without `completed`       | `TodoReplace.completed` is required |
| `PATCH /todos/1` with `{"title": null}`  | our `@field_validator`              |

**422 vs 404:**

|            | 422                                    | 404                                        |
| ---------- | -------------------------------------- | ------------------------------------------ |
| Question   | Is the request **valid**?              | Does the thing **exist**?                  |
| Checked by | FastAPI/Pydantic, from your type hints | **Your code**, after looking it up         |
| When       | **Before** your function runs          | **Inside** your function                   |
| Example    | `/todos/abc`: `abc` can never be an ID | `/todos/999`: a valid ID, but no such todo |

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

---

# Docker

## What it is and why we use it

**Docker runs software in a *container*: an isolated mini Linux environment holding the
program and everything it needs.** We use it to run PostgreSQL without installing it on
the Mac.

| Without Docker (e.g. Homebrew)                      | With Docker                                                |
| --------------------------------------------------- | ---------------------------------------------------------- |
| One version installed system-wide                   | Each project picks its own version (like Node per project) |
| Leaves files and background services behind         | Remove the container and it's gone                         |
| Your setup differs from teammates' and production's | Every machine runs exactly the same image                  |

| Term               | What it is                                        | Analogy                       |
| ------------------ | ------------------------------------------------- | ----------------------------- |
| **Image**          | A read-only package, e.g. `postgres:18`           | A class / an npm package      |
| **Container**      | A running instance of an image                    | An object / a running process |
| **Docker Hub**     | Public registry of images                         | npm registry                  |
| **Volume**         | Storage that lives *outside* the container        | —                             |
| **Docker Desktop** | Mac app that runs a small Linux VM for containers | Must be **running** first     |

## `compose.yaml`

A recipe for the project's services, so you don't type long `docker run ...` commands.
It works like `package.json` scripts, but for services.

```yaml
services:
  db:                                # service name
    image: postgres:18               # which image to run
    environment:                     # read by the image at first start
      POSTGRES_USER: todo            #   → creates user "todo"
      POSTGRES_PASSWORD: todo
      POSTGRES_DB: todo              #   → creates database "todo"
    ports:
      - "5432:5432"                  # Mac port → container port
    volumes:
      - pgdata:/var/lib/postgresql   # data survives `docker compose down`
    healthcheck:                     # lets `up --wait` wait until Postgres is ready
      test: ["CMD-SHELL", "pg_isready -U todo -d todo"]
```

- **`ports`:** containers have their own isolated network. This opens `localhost:5432`
  on the Mac to Postgres inside the container. Use `"127.0.0.1:5432:5432"` to allow
  connections **only from this Mac** (the plain form also accepts other devices on the
  same Wi-Fi).
- **`volumes`:** containers are disposable; anything stored inside one disappears with
  it. A volume keeps the database files outside.

```
Your Mac
├── Terminal  ── docker compose exec … psql ──┐
├── TablePlus ── localhost:5432 ───────────────┤   (any client)
├── FastAPI app (Phase 4) ── localhost:5432 ───┤
│                                              ▼
└── Docker Desktop (a small Linux VM)
     └── container "todo-api-db-1"  ── PostgreSQL server, port 5432
            └── volume "pgdata"     ── the actual data files on disk
```

## Commands

Run these in your normal terminal, from the project folder:

| Command                       | What it does                                                       |
| ----------------------------- | ------------------------------------------------------------------ |
| `open -a Docker`              | Start Docker Desktop (needed after a reboot)                       |
| `docker compose up -d --wait` | Start the services in the background (`-d`) and wait until healthy |
| `docker compose ps`           | Show running services and their health                             |
| `docker compose logs db`      | Show the database's logs                                           |
| `docker compose down`         | Stop and remove the containers. **Data is kept** in the volume     |
| `docker compose down -v`      | Same, but **also delete the volume, and with it all data**         |

---

# PostgreSQL

## Server, client and psql

- **Server:** PostgreSQL itself, running in the container. It stores data and answers
  queries on port 5432. It has no user interface.
- **Client:** anything that connects to the server and sends SQL:
  - **psql**: the official command-line client, a REPL for SQL (like typing `node`).
    It's installed inside the container, so it doesn't need installing on the Mac.
  - TablePlus / DBeaver: graphical clients (host `localhost`, port `5432`,
    user/password/database `todo`).
  - Your FastAPI app, from Phase 4.

## The two prompts

**① The normal terminal (`%`): shell and Docker commands.**

```
% docker compose exec db psql -U todo -d todo
```

Meaning: in the running `db` service, **exec**ute `psql` as **U**ser `todo`, connected to
**d**atabase `todo`. This takes you to prompt ②.

**② The psql prompt (`todo=#`): SQL and psql commands.**

```
todo=# SELECT * FROM todos;     ← SQL: must end with ;
todo=# \d todos                 ← psql command: starts with \
todo=# \q                       ← quit, back to prompt ①
```

| psql command | What it does                                    |
| ------------ | ----------------------------------------------- |
| `\dt`        | List tables                                     |
| `\d todos`   | Show a table's columns, constraints and indexes |
| `\x`         | Toggle expanded display (one column per line)   |
| `\q`         | Quit                                            |

If psql seems stuck, it's waiting for a `;`. Type `;` and press Enter.

**Running a whole file**, from prompt ①, without entering psql:

```
docker compose exec -T db psql -U todo -d todo < sql/schema.sql
```

`<` feeds the file into psql as if you'd typed it. `-T` turns off interactive terminal
mode, which piping a file needs.

## Column types and constraints

| Need                 | ✅ Use                                | ❌ Outdated or risky      | Why                                    |
| -------------------- | ------------------------------------- | ------------------------- | -------------------------------------- |
| Auto-incrementing ID | `bigint GENERATED ALWAYS AS IDENTITY` | `SERIAL`, plain `integer` | Safe IDs that never run out (see note) |
| Text                 | `text`                                | `varchar(255)`            | Same speed; `CHECK` for limits         |
| A calendar date      | `date`                                |                           | Like Python's `date`                   |
| A moment in time     | **`timestamptz`**                     | `timestamp`               | An exact moment (see note)             |

> **IDs:** the database assigns them, so two inserts at the same moment can't collide (unlike `max(id) + 1`). Full column: `id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY`. `bigint` won't run out; `integer` stops at ~2.1 billion.
>
> **`timestamp` vs `timestamptz`:** `timestamp` is just a date and clock time with no time zone, so "10:00" is ambiguous. `timestamptz` stores an exact moment (internally in UTC) and shows it in your session's time zone. Always use `timestamptz`.

**Constraints** are rules the database enforces on **every** write, from any client.
They're like Pydantic validation that nothing can get around.

```sql
title      text NOT NULL CHECK (title <> ''),       -- required and not empty
completed  boolean NOT NULL DEFAULT false,          -- default when not given
due_date   date,                                    -- optional (NULL allowed)
created_at timestamptz NOT NULL DEFAULT now()       -- set automatically
```

| Constraint    | Means                                                             |
| ------------- | ----------------------------------------------------------------- |
| `NOT NULL`    | Required                                                          |
| `DEFAULT x`   | Value used when the INSERT doesn't mention the column             |
| `CHECK (...)` | Any rule you can write as a condition                             |
| `PRIMARY KEY` | Unique + not null + indexed: the row's identity (like a dict key) |
| `UNIQUE`      | No two rows may have the same value                               |

> ⚠️ **`DEFAULT` only applies on `INSERT`.** `updated_at timestamptz DEFAULT now()` is set
> when the row is created and then **never changes**, even after an `UPDATE`. To keep it
> current, the app sets it in every `UPDATE` (`SET ..., updated_at = now()`), or a
> database trigger does it.

**`NULL` works like `None`:**

```sql
WHERE due_date = NULL     -- ❌ never true, even for rows with no due date
WHERE due_date IS NULL    -- ✅ like Python's `is None`
```

**Style convention:** SQL keywords in UPPERCASE (`CREATE TABLE`, `NOT NULL`), names in
lowercase snake_case (`due_date`). Keywords aren't case-sensitive, but this makes queries
easier to scan.

## CRUD in SQL

| Endpoint                                       | SQL                                                                          |
| ---------------------------------------------- | ---------------------------------------------------------------------------- |
| `POST /todos`                                  | `INSERT INTO todos (title) VALUES ('Buy milk') RETURNING *;`                 |
| `GET /todos/1`                                 | `SELECT * FROM todos WHERE id = 1;`                                          |
| `GET /todos?completed=false&limit=10&offset=0` | `SELECT * FROM todos WHERE completed = false ORDER BY id LIMIT 10 OFFSET 0;` |
| `PATCH /todos/1`                               | `UPDATE todos SET completed = true WHERE id = 1 RETURNING *;`                |
| `DELETE /todos/1`                              | `DELETE FROM todos WHERE id = 1;`                                            |

- `RETURNING *` returns the affected row, the way POST returns the created todo.
- ⚠️ **`UPDATE` / `DELETE` without `WHERE` changes every row.** Write the `WHERE` first.
- Without `ORDER BY`, rows come back in **no guaranteed order**. Pagination always
  needs `ORDER BY`.

## Running and testing SQL

All commands run in the normal terminal (prompt ①), from the project folder.

| Goal                     | Command                                                                              |
| ------------------------ | ------------------------------------------------------------------------------------ |
| Run a schema file        | `docker compose exec -T db psql -U todo -d todo -v ON_ERROR_STOP=1 < sql/schema.sql` |
| Run test queries         | `docker compose exec -T db psql -U todo -d todo -e < sql/queries.sql`                |
| Run one command          | `docker compose exec db psql -U todo -d todo -c '\d todos'`                          |
| Experiment interactively | `docker compose exec db psql -U todo -d todo`                                        |

| Flag                 | Meaning                                                         | Use it for                                   |
| -------------------- | --------------------------------------------------------------- | -------------------------------------------- |
| `-v ON_ERROR_STOP=1` | Stop at the first error (default: report it and **keep going**) | Schema files                                 |
| `-e`                 | Echo each statement before its result                           | Test files, so results match up with queries |
| `-c '...'`           | Run one command, then exit                                      | Quick checks                                 |
| `-T`                 | No interactive terminal                                         | Required when piping a file with `<`         |

**Workflow:** edit `schema.sql` → run it (fresh, empty tables because it starts with
`DROP`) → check with `\d todos` → run `queries.sql` and confirm each statement succeeds
or fails the way you predicted. Leave out `ON_ERROR_STOP` for test files that contain
statements you *expect* to fail.

**Experiment safely with a transaction:**

```sql
BEGIN;                         -- start a transaction
DELETE FROM todos;             -- try anything...
SELECT count(*) FROM todos;    -- ...and look at the result
ROLLBACK;                      -- undo everything since BEGIN (COMMIT would save it)
```

**Make schema files all-or-nothing.** If `DROP TABLE` succeeds but `CREATE TABLE` has a
typo, you end up with **no table at all**. Postgres can run `CREATE` / `DROP` inside a
transaction (many databases can't), so wrap the file:

```sql
BEGIN;
DROP TABLE IF EXISTS todos;
CREATE TABLE todos (...);
COMMIT;
```

With `ON_ERROR_STOP=1`, an error stops psql before `COMMIT`, so the transaction is rolled
back and the old table is still there.

---

# Local vs production configuration

`compose.yaml` contains the password `todo` in a file committed to a public repo. That's
acceptable only because this database runs on your laptop, holds no real data, and can be
recreated at any time.

|                     | Local (now)                 | Production                                                     |
| ------------------- | --------------------------- | -------------------------------------------------------------- |
| Where it runs       | A container on your Mac     | A managed service (AWS RDS, Railway, Neon, …) with backups     |
| Password            | `todo`, in a committed file | Long and random, **never in git**                              |
| How the app gets it | Hard-coded                  | **Environment variables** or a secret manager, per environment |
| Who can connect     | This machine                | Only the app's servers, over encrypted connections             |
| Losing the data     | Doesn't matter              | A disaster                                                     |

**The rule: settings that differ between environments (database URL, passwords, API
keys) come from outside the code.** In Phase 4: pydantic-settings reads `DATABASE_URL`
from a `.env` file that is listed in `.gitignore`, so it never gets committed.
