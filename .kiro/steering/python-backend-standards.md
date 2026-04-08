---
inclusion: fileMatch
fileMatchPattern: "backend/**/*.py"
---

# Python Backend Standards — Media Tracker

## Framework & Async
- Use FastAPI with full async/await in all service layer methods, routers, and DB operations.
- Never use synchronous SQLAlchemy calls — always use `AsyncSession`.
- Use `async with` for database session management.

## Project Structure
- Routers only handle HTTP concerns (request parsing, response formatting, status codes).
- All business logic lives in the service layer (`backend/services/`).
- Models in `backend/models/`, schemas in `backend/schemas/`.

## Error Handling
- Use `HTTPException` from FastAPI for all error responses.
- Validation errors: 400 with descriptive `detail` message.
- Not found: 404 with `"Item not found"`.
- Never expose internal stack traces to the client.

## Imports
- Group imports: stdlib → third-party → local, separated by blank lines.
- Use absolute imports from the `backend` package root.

## Pydantic Schemas
- All request/response models use Pydantic `BaseModel`.
- Use `Field(...)` for required fields with constraints.
- Enums for `MediaType` and `MediaStatus` — never raw strings.

## SQLAlchemy Models
- Table names: snake_case, plural (e.g., `media_items`, `tags`, `media_tags`).
- Use `mapped_column()` for column definitions.
- Timestamps with `server_default=func.now()` for `created_at`.
- Always include `updated_at` with `onupdate=func.now()`.

## Docstrings
- Use Google-style docstrings for service methods.
- Include parameter types and return types.

## Testing
- All property tests use Hypothesis.
- Each property test file must include a comment: `# Feature: media-tracker, Property N: <description>`.
- Minimum 100 iterations per property test (`@settings(max_examples=100)`).
- Use `@pytest.mark.asyncio` for async tests.
- Test fixtures for DB sessions go in `conftest.py`.
