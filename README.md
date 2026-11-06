# FastAPI Todo API

Python FastAPI task-management REST API with JWT auth, PostgreSQL, and Docker Compose.

## Stack

- **Backend:** Python 3.11+, FastAPI, Uvicorn
- **Auth:** JWT + hashed passwords
- **DB:** PostgreSQL via SQLAlchemy 2.0
- **Tests:** pytest (SQLite in-memory)
- **Runtime:** Docker Compose

## Features

- Register / login with JWT access tokens
- Task CRUD with ownership isolation
- Filter by `done` and paginated listing
- Indexed `(owner_id, done)` query path

## Quick start

```bash
docker compose up --build
```

API docs: http://localhost:8000/docs

```bash
pytest -q
```

## Author

Pooja Sharma — [Pooja101117](https://github.com/Pooja101117)
