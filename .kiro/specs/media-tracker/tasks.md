# Implementation Plan: Media Tracker

## Overview

Incremental implementation of the Media Tracker application: database models and migrations first, then the service layer, REST API, MCP server, and finally the Vue.js frontend. Property-based tests with Hypothesis validate correctness properties from the design. Each task builds on the previous ones, ensuring no orphaned code.

## Tasks

- [x] 1. Set up project structure, database models, and schemas
  - [x] 1.1 Create backend project structure with FastAPI entry point and configuration
    - Create `backend/main.py` with FastAPI app, CORS middleware, and static file serving for images
    - Create `backend/config.py` with database URL, image storage path, and API key settings
    - Create `backend/db.py` with SQLAlchemy async engine and session configuration
    - Install dependencies: fastapi, uvicorn, sqlalchemy[asyncio], asyncpg, alembic, pydantic, hypothesis
    - _Requirements: 10.1_

  - [x] 1.2 Create SQLAlchemy models for media_items, tags, and media_tags
    - Create `backend/models/media.py` with MediaItem, Tag, and media_tags association table
    - MediaItem fields: id, title, media_type, status (default "pending"), rating, year, creator, notes, image_path, created_at, updated_at, started_at, completed_at
    - Tags as many-to-many relationship through media_tags
    - _Requirements: 1.1, 1.4, 6.1, 6.2, 8.1, 10.1_

  - [x] 1.3 Create Pydantic schemas for request/response validation
    - Create `backend/schemas/media.py` with MediaType enum, MediaStatus enum, MediaCreate, MediaUpdate, MediaResponse, MediaFilters, PaginatedResult, CatalogStats, ExportData, ImportResult, ErrorResponse
    - Enforce validation: title min_length=1 max_length=255, tags max_length=10, rating 1-10
    - _Requirements: 1.2, 1.3, 7.2, 8.3, 8.4_

  - [x] 1.4 Set up Alembic migrations and create initial migration
    - Initialize Alembic in `backend/migrations/`
    - Create initial migration for media_items, tags, and media_tags tables
    - _Requirements: 10.1_

- [x] 2. Implement core service layer
  - [x] 2.1 Implement MediaService with CRUD operations
    - Create `backend/services/media_service.py` with MediaService class
    - Implement `create`: validate input, set status="pending", save to DB, return created item
    - Implement `get`: fetch by ID, raise 404 if not found
    - Implement `list`: paginated query with filters (media_type, status, search text case-insensitive on title, tag), ordered by created_at descending
    - Implement `update`: partial update of provided fields, validate same rules as create
    - Implement `delete`: remove item, return 204, raise 404 if not found
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 5.2, 5.3_

  - [x] 2.2 Implement status management and rating in MediaService
    - Implement `update_status`: validate status value, auto-set started_at on "in_progress" (only if null), auto-set completed_at on "completed"
    - Implement `update_rating`: validate range 1-10, save rating
    - Implement `update_tags`: validate max 10 tags, create missing tags, update associations
    - _Requirements: 6.1, 6.2, 6.3, 7.1, 7.2, 8.1, 8.3, 8.4_

  - [x] 2.3 Write property tests for creation and validation (Properties 1, 2)
    - **Property 1: Creation preserves data and assigns pending status**
    - **Property 2: Rejection of invalid Media_Type**
    - Use Hypothesis strategies to generate random valid MediaCreate inputs and invalid media_type strings
    - **Validates: Requirements 1.1, 1.3, 1.4, 4.3**

  - [x] 2.4 Write property tests for filtering and listing (Properties 3, 15)
    - **Property 3: Combined filtering with AND logic**
    - **Property 15: Descending order by creation date**
    - Generate random catalogs and filter combinations with Hypothesis
    - **Validates: Requirements 2.1, 3.1, 3.2, 3.3, 3.4, 8.2**

  - [x] 2.5 Write property tests for update and deletion (Properties 4, 5)
    - **Property 4: Update preserves modified fields**
    - **Property 5: Deletion removes the item**
    - **Validates: Requirements 4.1, 4.3, 5.2**

  - [x] 2.6 Write property tests for status, rating, and tags (Properties 6, 7, 8, 9)
    - **Property 6: Status transition automatically records dates**
    - **Property 7: Rejection of invalid status**
    - **Property 8: Rating within valid range**
    - **Property 9: Tags with limit of 10**
    - **Validates: Requirements 6.1, 6.2, 6.3, 7.1, 7.2, 8.1, 8.3, 8.4**

- [x] 3. Implement statistics and export/import services
  - [x] 3.1 Implement StatsService
    - Create `backend/services/stats_service.py` with StatsService class
    - Implement `get_stats`: count by media_type, count by status, average rating by media_type (only items with rating)
    - _Requirements: 9.1, 9.2, 9.3_

  - [x] 3.2 Implement ExportService
    - Create `backend/services/export_service.py` with ExportService class
    - Implement `export_catalog`: generate ExportData JSON with version, timestamp, and all items including image URLs
    - Implement `import_catalog`: parse JSON, validate, create items, return ImportResult with created count and errors
    - _Requirements: 10.2, 10.3, 10.4, 12.6_

  - [x] 3.3 Write property tests for statistics and export/import (Properties 10, 11)
    - **Property 10: Statistics consistent with the catalog**
    - **Property 11: JSON round-trip**
    - **Validates: Requirements 9.1, 9.2, 9.3, 10.4**

- [x] 4. Implement Image Service
  - [x] 4.1 Implement ImageService with external API search and local storage
    - Create `backend/services/image_service.py` with ImageService class
    - Implement `fetch_image`: search external APIs (TMDB, Open Library, Google) by title and media_type, download and store locally, return local path
    - Implement `get_default_image`: return default image path based on media_type (movie, book, series)
    - Handle errors gracefully: log failures, fall back to default image without interrupting main operation
    - _Requirements: 12.1, 12.2, 12.3, 12.5_

  - [x] 4.2 Write property test for default image fallback (Property 14)
    - **Property 14: Default image based on Media_Type**
    - Mock failing image service, verify default image assigned per media_type
    - **Validates: Requirement 12.5**

- [x] 5. Checkpoint
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Implement REST API endpoints
  - [x] 6.1 Implement media CRUD endpoints
    - Create `backend/routers/media.py` with POST /api/media, GET /api/media, GET /api/media/{id}, PUT /api/media/{id}, DELETE /api/media/{id}
    - Wire endpoints to MediaService methods
    - Trigger ImageService.fetch_image on create and on title/type update
    - Return proper HTTP status codes (201, 200, 204, 400, 404)
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.3, 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 5.2, 5.3, 12.1, 12.2_

  - [x] 6.2 Implement status, rating, and tag endpoints
    - Add PATCH /api/media/{id}/status, PATCH /api/media/{id}/rating, PUT /api/media/{id}/tags to `backend/routers/media.py` or `backend/routers/tags.py`
    - Wire to MediaService.update_status, update_rating, update_tags
    - _Requirements: 6.1, 6.2, 6.3, 7.1, 7.2, 8.1, 8.3, 8.4_

  - [x] 6.3 Implement stats, export/import, and image endpoints
    - Create `backend/routers/stats.py` with GET /api/stats
    - Create `backend/routers/export_import.py` with GET /api/export and POST /api/import
    - Add GET /api/media/{id}/image endpoint for querying a media item's image
    - Wire to StatsService, ExportService, and ImageService
    - _Requirements: 9.1, 9.2, 9.3, 10.2, 10.3, 12.3, 12.7_

  - [x] 6.4 Register all routers in FastAPI main app
    - Include all routers in `backend/main.py`
    - Configure static file serving for stored images
    - _Requirements: 1.1, 2.1_

- [x] 7. Implement MCP Server
  - [x] 7.1 Create MCP server with all tools registered
    - Create `backend/mcp/server.py` using the Python `mcp` library
    - Register tools: create_media, delete_media, update_media, list_media, update_status, rate_media, manage_tags, get_stats, export_catalog, import_catalog
    - Each tool delegates to the corresponding service layer method
    - Each tool has a name, natural language description, and JSON parameter schema per MCP spec
    - Return descriptive error messages for invalid parameters
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7, 11.8, 11.9, 11.10, 11.11, 11.12_

  - [x] 7.2 Write property tests for MCP-REST equivalence (Properties 12, 13)
    - **Property 12: MCP-REST equivalence**
    - **Property 13: MCP rejects invalid parameters with descriptive message**
    - **Validates: Requirements 11.2, 11.3, 11.4, 11.5, 11.6, 11.7, 11.8, 11.9, 11.10, 11.11**

- [x] 8. Checkpoint
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 9. Implement Vue.js frontend
  - [ ] 9.1 Set up frontend project structure and API client
    - Create Vue.js 3 project in `frontend/` with Composition API
    - Create `frontend/src/api/media.js` with axios/fetch HTTP client wrapping all backend endpoints
    - Set up Vue Router in `frontend/src/router/index.js` with routes for catalog, detail, stats, import/export
    - _Requirements: 2.1, 2.3_

  - [ ] 9.2 Implement CatalogView with MediaCard, FilterBar, and Pagination
    - Create `frontend/src/views/CatalogView.vue` with paginated media list
    - Create `frontend/src/components/MediaCard.vue` displaying title, media_type, status, rating, and image
    - Create `frontend/src/components/FilterBar.vue` with media_type, status, tag, and search text filters
    - Create `frontend/src/components/Pagination.vue` for page navigation
    - Show empty state message with "add first item" button when catalog is empty
    - _Requirements: 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 3.4, 12.4_

  - [ ] 9.3 Implement MediaForm and MediaDetailView for create/edit
    - Create `frontend/src/components/MediaForm.vue` with fields: title, media_type, year, creator, notes
    - Create `frontend/src/views/MediaDetailView.vue` for viewing and editing a media item
    - Include `frontend/src/components/TagInput.vue` for managing tags (max 10)
    - Include `frontend/src/components/RatingInput.vue` for rating (1-10), disabled when status is "pending"
    - Include `frontend/src/components/ConfirmDialog.vue` for delete confirmation
    - _Requirements: 1.1, 4.1, 5.1, 7.1, 7.3, 8.1_

  - [ ] 9.4 Implement StatsView and ImportExportView
    - Create `frontend/src/views/StatsView.vue` displaying counts by type, by status, and average ratings
    - Create `frontend/src/views/ImportExportView.vue` with export download button and import file upload
    - _Requirements: 9.1, 9.2, 9.3, 10.2, 10.3_

  - [ ] 9.5 Create useMedia composable for shared state and operations
    - Create `frontend/src/composables/useMedia.js` encapsulating media CRUD, filters, pagination state, and API calls
    - Wire composable into CatalogView and MediaDetailView
    - _Requirements: 2.1, 3.1_

- [ ] 10. Final checkpoint
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate the 15 correctness properties from the design using Hypothesis
- The service layer is built first so both REST API and MCP server can reuse it
