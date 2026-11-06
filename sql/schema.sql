-- Run: docker compose exec -T db psql -U todo -d todo -v ON_ERROR_STOP=1 < sql/schema.sql
-- All-or-nothing: if any statement fails, the DROP is rolled back too.
BEGIN;

DROP TABLE IF EXISTS todos;

CREATE TABLE todos (
    id         bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title      text NOT NULL CHECK (title <> ''),
    completed  boolean NOT NULL DEFAULT false,
    due_date   date,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()  -- set on INSERT only; UPDATEs must set it
);

COMMIT;
