DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS admins;
DROP TABLE IF EXISTS events;
DROP TABLE IF EXISTS event_requests;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);

CREATE TABLE admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);

CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    registration_deadline TEXT NOT NULL
);

CREATE TABLE event_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_title TEXT NOT NULL,
    department TEXT NOT NULL,
    student_id TEXT NOT NULL,
    event_description TEXT NOT NULL,
    rehearsal_date TEXT NOT NULL,
    participants_names TEXT NOT NULL,
    practice_timing TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    FOREIGN KEY (student_id) REFERENCES users (student_id)
);
