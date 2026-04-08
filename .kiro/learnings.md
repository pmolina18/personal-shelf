# Learnings

## What Has Worked

**[2026-04-07] — Hook and steering setup for Media Tracker spec**
- Observation: Creating hooks with `fileEdited` event type and glob patterns like `**/*.py` works correctly for targeting specific file types across the project tree.
- Action: Use double-star glob patterns for recursive file matching in hooks. Single-star patterns (e.g., `backend/schemas/*.py`) work for specific directories.
- Confidence: high

**[2026-04-07] — Steering file conditional inclusion**
- Observation: Steering files with `inclusion: fileMatch` and `fileMatchPattern` activate only when matching files are read into context, keeping irrelevant rules out of unrelated tasks (e.g., DB conventions don't load when editing Vue files).
- Action: Use `fileMatch` inclusion for domain-specific standards (backend, frontend, DB, tests). Use `auto` inclusion only for cross-cutting concerns (spec language, self-learning).
- Confidence: high

## What Has Failed
- (Nothing recorded yet)

**[2026-04-07] — Tool installation (ruff)**
- Observation: `ruff` was not pre-installed in the environment. The shell error `/bin/sh: ruff: command not found` indicated a missing Python tool dependency. `pip install ruff` resolved it immediately (v0.15.9).
- Action: When a hook or command fails with "command not found" for a Python tool, install it with `pip install <tool>` before investigating further. Consider adding such tools to `backend/requirements.txt` or a dev-dependencies file to prevent recurrence.
- Confidence: high

## Patterns and Preferences

**[2026-04-07] — Self-learning system bootstrap**
- Observation: The self-learning pattern requires two hooks working together: `promptSubmit` to read learnings at session start, and `agentStop` to write learnings at session end. Both are needed for the feedback loop to work.
- Action: Always keep both hooks active. If one is disabled, the learning cycle breaks.
- Confidence: high

**[2026-04-07] — MCP server availability**
- Observation: PostgreSQL and Filesystem MCP servers exist as published npm packages (`@modelcontextprotocol/server-postgres`, `@modelcontextprotocol/server-filesystem`) and can be configured via `npx -y`. The project's own MCP server (task 7.1) will be custom Python.
- Action: Use published MCP servers for standard infra (DB, filesystem). Only build custom MCP for project-specific tools.
- Confidence: high

**[2026-04-07] — MCP configuration file creation**
- Observation: MCP config goes in `.kiro/settings/mcp.json` at workspace level. The file is picked up automatically — no restart needed, just reconnect from the MCP Servers panel.
- Action: Always create the config at `.kiro/settings/mcp.json` for workspace-scoped servers. Use `~/.kiro/settings/mcp.json` only for user-global servers.
- Confidence: high

**[2026-04-07] — Filesystem MCP server debugging**
- Observation: `@modelcontextprotocol/server-filesystem` requires absolute paths and the target directory must exist before the server starts. Relative paths like `./backend/images` fail silently with ENOENT, and the server closes the connection immediately.
- Action: Always use absolute paths in filesystem MCP args. Ensure target directories exist before configuring the server (`mkdir -p`). Point to the workspace root for general-purpose file access rather than a narrow subdirectory.
- Confidence: high

**[2026-04-07] — Hook debugging: runCommand with missing directories**
- Observation: Hooks using `runCommand` with `cd backend && pytest tests/` fail with exit code 1 and no captured output when the target directory (`tests/`) doesn't exist. The `&&` chaining in hook commands can also suppress error output, making failures silent. Additionally, hooks targeting non-existent directories (e.g., `frontend/`) fail the same way.
- Action: Disable hooks that depend on directories not yet created (`"enabled": false`) and add a note in the description. Remove `cd <dir> &&` chaining from hook commands — use full paths relative to workspace root instead (e.g., `python -m pytest backend/tests/`). Re-enable hooks only after the required directories and files exist.
- Confidence: high

**[2026-04-07] — Task 2 execution: service layer + property tests with Hypothesis**
- Observation: Hypothesis `@given` does not work with `pytest-asyncio` async fixtures. The `@given` decorator controls test execution and cannot inject async fixtures. The workaround is to use sync test functions with `asyncio.run()` internally, creating a fresh in-memory SQLite session per example via an async generator helper (`_fresh_session()`).
- Action: For Hypothesis + async DB tests, always use sync `def test_*` with `asyncio.run()` inside. Do not combine `@given` with `@pytest.mark.asyncio` or async fixtures. Each example gets its own engine/session to avoid cross-contamination.
- Confidence: high

**[2026-04-07] — Python 3.11: `list[str]` in class body annotations**
- Observation: Python 3.11 raises `TypeError: 'function' object is not subscriptable` when using `list[str]` in type annotations inside a class body at runtime (e.g., method signatures in a class). This happens because PEP 585 generics are not fully supported in all runtime contexts in 3.11.
- Action: Always add `from __future__ import annotations` at the top of Python files that use generic type hints (`list[str]`, `dict[str, int]`, etc.) in class method signatures. This makes all annotations strings (lazy evaluation) and avoids the runtime error.
- Confidence: high

**[2026-04-07] — fsWrite import pruning**
- Observation: The `fsWrite` tool aggressively prunes imports it considers unused, even when they are used later in the file or in appended content. This caused repeated `NameError` failures (e.g., `AsyncSession`, `settings`, `given` not defined) because the tool removed imports from the initial write that were needed by code appended via `fsAppend`.
- Action: For files with many imports (especially test files), use `mcp_filesystem_write_file` instead of `fsWrite` — it writes content verbatim without pruning. Alternatively, write the complete file in one `mcp_filesystem_write_file` call rather than splitting across `fsWrite` + `fsAppend`.
- Confidence: high

**[2026-04-07] — Hypothesis: duplicate values in generated lists cause IntegrityError**
- Observation: `st.lists(st.text(...))` can generate duplicate strings. When these are used as tag names with a UNIQUE constraint in the DB, `_get_or_create_tags` tries to insert the same tag twice, causing `IntegrityError`. Fixed by adding `unique=True` to the strategy and deduplicating in the service method.
- Action: Always use `unique=True` on `st.lists()` when generated values map to unique DB columns. Also make the service layer defensive — deduplicate inputs before DB operations.
- Confidence: high

**[2026-04-07] — Hypothesis: MediaUpdate with explicit None vs unset fields**
- Observation: `st.builds(MediaUpdate, title=st.one_of(st.none(), ...))` explicitly sets `title=None`, which Pydantic treats as "set" (included in `model_dump(exclude_unset=True)`). This causes NOT NULL constraint violations when the None value is written to the DB. The fix is to use a `@st.composite` strategy that only includes fields probabilistically via `draw(st.booleans())`.
- Action: For Pydantic partial-update schemas, use `@st.composite` strategies that conditionally include fields in the constructor kwargs, rather than `st.builds` with `st.one_of(st.none(), ...)`. This correctly models "field not provided" vs "field set to None".
- Confidence: high

**[2026-04-07] — Hook path mismatch: `backend/tests/` vs `tests/`**
- Observation: The post-task-execution hook runs `pytest backend/tests/` but the actual test directory is `tests/` at the project root. This produces `ERROR: file or directory not found: backend/tests/` after every task. Exit code is 0 so it doesn't block.
- Action: The hook command path should be updated to `python -m pytest tests/` to match the actual test location. This is a config fix, not a code issue.
- Confidence: high

## Open Questions

- Will the `agentStop` hook reliably trigger on all session endings, including timeouts or user cancellations? Needs validation during implementation.
- The `promptSubmit` hook fires on every message — for long sessions this may cause repeated learnings reads. Monitor if this adds noticeable latency.

**[2026-04-07] — Task 1 execution: project scaffolding**
- Observation: The post-task-execution hook runs `pytest tests/` after every subtask, but the `tests/` directory doesn't exist until task 2. This produces a harmless `ERROR: file or directory not found: tests/` on every subtask in task 1. Exit code is 0 so it doesn't block execution.
- Action: This is expected and safe to ignore for tasks that precede test creation. No need to create an empty `tests/` dir or dummy test file just to silence it.
- Confidence: high

**[2026-04-07] — SQLAlchemy 2.0 async setup**
- Observation: The project uses SQLAlchemy 2.0 style (`DeclarativeBase`, `mapped_column()`, `async_sessionmaker`) with `asyncpg` driver. Alembic's async support requires the `async_engine_from_config` + `run_async_migrations()` pattern in `env.py`, plus adding the project root to `sys.path` so `backend.*` imports resolve.
- Action: For async Alembic setups, always use `sys.path.insert(0, str(Path(__file__).resolve().parents[2]))` in `env.py` to ensure backend package imports work regardless of working directory.
- Confidence: high

**[2026-04-07] — Session end: no new patterns**
- Observation: User asked about local PostgreSQL setup on macOS. Provided standard Homebrew install instructions and noted the mismatch between default Homebrew config (current OS user, no password) and the project's `DATABASE_URL` (postgres:postgres). No new technical patterns discovered — existing learnings held.
- Action: No changes needed. Existing patterns confirmed.
- Confidence: high

**[2026-04-07] — Environment: Homebrew requires Xcode CLI tools**
- Observation: `brew install` fails with "No developer tools installed" even when `xcode-select -p` reports `/Library/Developer/CommandLineTools` exists. Homebrew's own check is stricter. `sudo xcode-select --reset` requires interactive password, making it unusable from the agent. `--force-bottle` flag does not bypass this check.
- Action: When Homebrew is blocked by developer tools issues, fall back to Docker (`docker run postgres:16`) or Postgres.app as alternatives. Docker is preferred when already installed since it requires no compilation. Always check `docker --version` and `docker ps` as a fallback path before giving up.
- Confidence: high

**[2026-04-07] — Environment: Docker daemon state**
- Observation: Docker CLI can be installed (`/usr/local/bin/docker`) but the daemon may not be running. `docker ps` returns "Cannot connect to the Docker daemon" in this case. The agent cannot start Docker Desktop — the user must open it manually.
- Action: When Docker is the chosen path, verify daemon is running with `docker ps` before attempting `docker run`. If daemon is down, instruct the user to open Docker Desktop first, then provide the exact `docker run` command to copy-paste.
- Confidence: high

**[2026-04-07] — Environment: Postgres.app as Homebrew/Docker fallback**
- Observation: When Homebrew is blocked and Docker daemon is down, Postgres.app can be fully installed and started by the agent: `curl` the DMG from GitHub releases, `hdiutil attach`, `cp -R` to `/Applications/`, `open /Applications/Postgres.app`. It starts a PostgreSQL 16 server on localhost:5432 within ~5 seconds. The default `postgres` role exists but needs `ALTER USER postgres WITH PASSWORD 'postgres'` to match the project's `DATABASE_URL`. Database creation via `createdb` and Alembic migrations work immediately after.
- Action: Postgres.app is the best agent-automatable PostgreSQL option on macOS when Homebrew and Docker are unavailable. Use the binary at `/Applications/Postgres.app/Contents/Versions/16/bin/` for `psql`, `createdb`, and `pg_isready`. Check readiness with `pg_isready -h localhost` (not default socket path).
- Confidence: high

**[2026-04-07] — Hook debugging: exit code 1 with no output**
- Observation: User reported "Hook execution failed with exit code 1. No output was captured." The `python-lint-save` hook runs `ruff check --fix ${filePath}` on every `.py` save. Testing `ruff` manually showed it works fine (`ruff check --fix backend/main.py` → "All checks passed!"). The failure likely occurs on specific files where ruff finds unfixable errors, or when `${filePath}` resolves to an unexpected value. The "no output captured" pattern is consistent with the earlier learning about `runCommand` hooks suppressing stderr.
- Action: When debugging hook failures with no output, test the exact command manually with a representative file first. If the tool works, the issue is likely in variable resolution (`${filePath}`) or file-specific errors. Consider adding `2>&1` to hook commands to capture stderr alongside stdout.
- Confidence: medium

**[2026-04-08] — Task 3 execution: StatsService, ExportService, property tests**
- Observation: Existing patterns held. The `_to_response` helper in `media_service.py` was successfully imported by `export_service.py` to avoid duplication. The Hypothesis + `asyncio.run()` + `_fresh_session()` pattern from task 2 worked identically for Properties 10 and 11. The `backend/tests/` hook path mismatch continued (harmless, exit code 0). No new issues encountered.
- Action: No changes needed. For future services that need to serialize MediaItem → MediaResponse, import `_to_response` from `media_service` rather than duplicating. Consider refactoring it to a shared utils module if more services need it.
- Confidence: high

**[2026-04-08] — Task 4 execution: ImageService + Property 14**
- Observation: Existing patterns held. The service follows the same async class pattern as other services. For Property 14, `unittest.mock.patch.object` with `AsyncMock` works cleanly inside the `asyncio.run()` + sync `@given` pattern to mock async methods on the ImageService. No DB session needed since ImageService is stateless (no DB interaction). The `backend/tests/` hook mismatch continued (harmless). Full suite: 41 tests pass.
- Action: For property tests on services that don't touch the DB, skip the `_fresh_session()` helper entirely — just instantiate the service and mock external dependencies with `patch.object` + `AsyncMock`. This is simpler and faster than the DB-backed pattern.
- Confidence: high

**[2026-04-08] — Task 6 execution: REST API endpoints**
- Observation: Existing patterns held. Router files follow a clean separation — routers only handle HTTP concerns (request parsing, status codes, Depends injection), all logic stays in the service layer. The `app.mount("/images", StaticFiles(...))` for static files must come AFTER `app.include_router(...)` calls because mounts are catch-all and can intercept API routes if placed first. The `tests-after-task.kiro.hook` was fixed from `backend/tests/` to `tests/` and re-enabled. Test fixtures in `test_media_router.py` and `test_stats_export_routers.py` use `app.dependency_overrides[get_session]` to swap in an in-memory SQLite session — this pattern works cleanly with `httpx.AsyncClient` + `ASGITransport`. Three new Pydantic schemas (`StatusUpdate`, `RatingUpdate`, `TagsUpdate`) were added to `schemas/media.py` for the PATCH/PUT request bodies.
- Action: Always register routers before static file mounts in FastAPI. For router tests, use `app.dependency_overrides` with `ASGITransport` — no need for a running server. Keep request body schemas in `schemas/` even if small, to maintain the single-source-of-truth pattern.
- Confidence: high

**[2026-04-08] — Task 5 checkpoint: full test suite validation**
- Observation: All 41 tests (8 export/import, 11 image service, 2 creation properties, 2 default image properties, 2 filtering properties, 2 stats/export properties, 5 status/rating/tags properties, 2 update/delete properties, 4 stats service unit tests) pass in 28s. The `backend/tests/` hook path mismatch fired again (exit code 0, harmless) — already documented. No new failures or patterns discovered. Existing Hypothesis + asyncio.run() + in-memory SQLite approach remains stable across all property tests.
- Action: No changes needed. Existing patterns confirmed. The hook path fix (`backend/tests/` → `tests/`) remains a pending config change the user can address when ready.
- Confidence: high

**[2026-04-08] — Task 7 execution: MCP server + property tests (Properties 12, 13)**
- Observation: The `mcp` Python library (v1.27.0) uses `FastMCP` with a `@mcp_server.tool()` decorator for registering tools. Tools are plain async functions — no special base class needed. `mcp_server.call_tool(name, args_dict)` returns a list of `TextContent` objects with JSON in `.text`, which is the right interface for testing without a running server. For testing, monkey-patching `backend.mcp.server.async_session` with an in-memory SQLite `async_sessionmaker` works cleanly — each test gets an isolated DB. The `fsWrite` import pruning issue (documented earlier) recurred: writing the server file caused `MediaFilters`, `MediaStatus`, `MediaType`, and `MediaUpdate` imports to be dropped since they appeared only in function bodies, not at module level. Same issue hit the test file (lost `asyncio`, `given`, `settings` imports).
- Action: For MCP tool testing, use `mcp_server.call_tool()` + `json.loads(result[0].text)` — no HTTP transport needed. Patch `async_session` at the module level (`import backend.mcp.server as mcp_module; mcp_module.async_session = factory`) for DB isolation. Continue using `mcp_filesystem_write_file` or single-shot `fsWrite` with all imports present to avoid the pruning issue.
- Confidence: high

**[2026-04-08] — Cross-workspace config replication (hooks, steerings, learnings)**
- Observation: Hooks are workspace-scoped only (`.kiro/hooks/` per project). There is no `~/.kiro/hooks/` mechanism — Kiro does not support user-level hooks. Steerings, however, work at both levels: `~/.kiro/steering/` for user-global and `.kiro/steering/` for workspace-scoped. User-level steerings with `inclusion: auto` load in every project automatically, making them ideal for cross-cutting concerns (self-learning, spec language). The MCP filesystem server's `list_allowed_directories` only covers explicitly configured paths, so writing to `~/.kiro/` requires the workspace fsWrite tools, not the MCP filesystem tools.
- Action: For reusable config across all projects: put steerings in `~/.kiro/steering/` (works globally). For hooks, copy `.kiro/hooks/` per workspace or create a bootstrap script. Consider offering users a `kiro init` style script that scaffolds `.kiro/hooks/` + `.kiro/learnings.md` in new repos.
- Confidence: high

**[2026-04-08] — Steering deduplication: global vs workspace**
- Observation: Steerings with `inclusion: auto` in both `~/.kiro/steering/` and `.kiro/steering/` load twice in the same workspace, adding redundant context. Steerings with `inclusion: fileMatch` can coexist at both levels without conflict if the global version is generic and the workspace version is project-specific — they complement rather than duplicate because the workspace one adds project-specific detail (e.g., "Media Tracker" naming, specific file paths).
- Action: Keep `inclusion: auto` steerings (self-learning, spec-language) only at user level (`~/.kiro/steering/`). Keep `inclusion: fileMatch` steerings at both levels only when the workspace version adds project-specific content beyond the global generic version. Delete workspace copies that are identical to global ones.
- Confidence: high

**[2026-04-08] — Task 8 checkpoint: Hypothesis null byte edge case in filtering**
- Observation: Hypothesis generated `\x00` (null byte) as a search string in the combined filtering property test. SQLite's `LIKE` operator does not match null bytes the same way Python's `in` operator does — `'\x00' in '0'` is `False` in Python, but the SQL query returned the row because `LIKE '%\x00%'` behaves differently at the DB level. The fix was constraining the search strategy to printable Unicode categories (`L`, `N`, `P`, `Z`) which reflects realistic user input.
- Action: When generating text for SQL search/filter tests with Hypothesis, restrict to printable characters using `st.characters(whitelist_categories=("L", "N", "P", "Z"))` instead of bare `st.text()`. Control characters and null bytes are not realistic user input and expose DB-driver-specific behavior rather than application bugs.
- Confidence: high
