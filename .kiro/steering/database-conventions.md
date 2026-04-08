---
inclusion: fileMatch
fileMatchPattern: "backend/models/**/*.py,backend/migrations/**/*.py,backend/db.py"
---

# Database Conventions — Media Tracker

## SQLAlchemy Models
- Table names: snake_case, plural (e.g., `media_items`, `tags`).
- Primary keys: `id` as serial/autoincrement integer.
- Use `mapped_column()` with explicit types.
- String columns must have `max_length` constraints matching Pydantic schemas.

## Timestamps
- `created_at`: `server_default=func.now()`, never set manually.
- `updated_at`: `server_default=func.now()`, `onupdate=func.now()`.
- `started_at` and `completed_at`: nullable, set by service layer logic only.

## Relationships
- Many-to-many through association tables (e.g., `media_tags`).
- Use `relationship()` with `back_populates` for bidirectional access.
- Cascade deletes on association tables when parent is deleted.

## Alembic Migrations
- Every migration must have a descriptive message: `alembic revision --autogenerate -m "add_tags_table"`.
- Never edit a migration that has already been applied.
- Test migrations with `alembic upgrade head` and `alembic downgrade -1` round-trip.

## Queries
- Use SQLAlchemy `select()` statements — no raw SQL.
- Filters: use `ilike()` for case-insensitive text search.
- Pagination: use `offset()` and `limit()` with total count via `func.count()`.
- Always order by `created_at.desc()` for catalog listings.

## Connection Management
- Use async connection pool via `create_async_engine`.
- Session lifecycle managed by FastAPI dependency injection.
- Never hold sessions open across await boundaries unnecessarily.
