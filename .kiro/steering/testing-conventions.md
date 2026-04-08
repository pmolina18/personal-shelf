---
inclusion: fileMatch
fileMatchPattern: "backend/tests/**/*.py"
---

# Testing Conventions — Media Tracker

## Property-Based Tests (Hypothesis)
- Each property test must reference the design property:
  ```python
  # Feature: media-tracker, Property N: <description>
  ```
- Minimum 100 examples: `@settings(max_examples=100)`.
- Use `@given()` with Hypothesis strategies for input generation.
- Pydantic model generation: use `from_model()` or custom strategies.
- Each property maps to specific requirements — include them in comments.

## Test File Organization
- Property tests: `backend/tests/test_properties.py` or split by domain (e.g., `test_properties_crud.py`, `test_properties_status.py`).
- Unit tests: `backend/tests/test_unit_*.py`.
- Integration tests: `backend/tests/test_integration_*.py`.

## Fixtures (conftest.py)
- `db_session`: async SQLAlchemy session with test database, rolled back after each test.
- `media_service`: MediaService instance wired to test session.
- `sample_media_item`: factory fixture for creating test MediaItems with random valid data.
- Use `@pytest.fixture` with `scope="function"` for isolation.

## Async Tests
- All async tests use `@pytest.mark.asyncio`.
- Use `pytest-asyncio` plugin.

## Assertions
- Be specific: assert exact field values, not just "no error".
- For property tests, assert the property holds for ALL generated inputs.
- For 400 errors, assert both status code AND error message content.
- For 404 errors, assert `"Item not found"` in detail.

## Running Tests
- Full suite: `pytest backend/tests/ -x --tb=short`
- Property tests only: `pytest backend/tests/ -k "property" -x`
- With verbose Hypothesis output: `pytest --hypothesis-show-statistics`
