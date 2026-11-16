-- UniResolve database schema (SQLite)
-- Two tables: one for people, one for their complaints.

CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    username    TEXT    NOT NULL UNIQUE,
    password    TEXT    NOT NULL,              -- SHA-256 hash, never plain text
    name        TEXT    NOT NULL,
    role        TEXT    NOT NULL CHECK (role IN ('student', 'admin')),
    reg_no      TEXT,                          -- only for students
    email       TEXT,
    department  TEXT
);

CREATE TABLE IF NOT EXISTS complaints (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id),
    title       TEXT    NOT NULL,
    category    TEXT    NOT NULL,
    location    TEXT    NOT NULL,
    priority    TEXT    NOT NULL CHECK (priority IN ('Low', 'Medium', 'High')),
    description TEXT    NOT NULL,
    status      TEXT    NOT NULL DEFAULT 'Pending'
                        CHECK (status IN ('Pending', 'In Progress', 'Resolved')),
    remarks     TEXT    DEFAULT '',
    created_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);
