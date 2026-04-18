# Personal Shelf (Shelfd) — Wiki

Personal Shelf es una plataforma social de **Media Tracking**: una aplicación web para catalogar películas, libros y series, hacer seguimiento de tu progreso, puntuar, etiquetar, descubrir contenido a través de amigos y obtener estadísticas de tu colección.

---

## Índice

1. [Arquitectura](#arquitectura)
2. [Stack tecnológico](#stack-tecnológico)
3. [Estructura del proyecto](#estructura-del-proyecto)
4. [Requisitos previos](#requisitos-previos)
5. [Arranque local para desarrollo](#arranque-local-para-desarrollo)
6. [Base de datos y migraciones](#base-de-datos-y-migraciones)
7. [API REST — Endpoints](#api-rest--endpoints)
8. [Servidor MCP](#servidor-mcp)
9. [Frontend](#frontend)
10. [Tests](#tests)
11. [Variables de entorno](#variables-de-entorno)
12. [Modelo de datos](#modelo-de-datos)
13. [Despliegue](#despliegue)
14. [Notas y decisiones técnicas](#notas-y-decisiones-técnicas)

---

## Arquitectura

```
┌─────────────────┐       ┌──────────────────┐       ┌────────────┐
│   Vue 3 SPA     │──────▶│  FastAPI Backend  │──────▶│ PostgreSQL │
│   (Vite dev)    │ proxy │  (uvicorn)        │ async │ (Neon.dev) │
│   :5173         │ /api  │  :8000            │ pg    │  :5432     │
└─────────────────┘       └──────────────────┘       └────────────┘
         │                        │
    Vercel (prod)                 ├── MCP Server (herramientas IA)
                                 ├── TMDB API (metadata + imágenes externas)
                                 ├── Open Library API (metadata + portadas externas)
                                 └── GitHub API (sugerencias + acceso)
```

El frontend en desarrollo corre en Vite (:5173) y hace proxy de `/api` al backend FastAPI (:8000). En producción, el frontend se despliega en Vercel y el backend en Render, con PostgreSQL en Neon.dev y DNS en Cloudflare. Las imágenes se sirven directamente desde las CDN externas de TMDB y Open Library (no hay almacenamiento local).

---

## Stack tecnológico

| Capa | Tecnología |
|------|-----------|
| Frontend | Vue 3 (Composition API), Vue Router 4, Vite 5, PWA (vite-plugin-pwa) |
| Backend | Python 3.11+, FastAPI, Uvicorn |
| ORM | SQLAlchemy 2.0 (async) |
| Base de datos | PostgreSQL 16 + asyncpg (Neon.dev en producción) |
| Migraciones | Alembic (async) |
| Autenticación | JWT (python-jose) + bcrypt |
| APIs externas | TMDB (películas/series), Open Library (libros), GitHub API (sugerencias/acceso) |
| Tests | pytest, Hypothesis (property-based), vitest + vue-test-utils (frontend) |
| Linting | Ruff (Python), ESLint + eslint-plugin-vue (JS/Vue) |
| MCP | mcp (Python) — herramientas para asistentes IA |
| Despliegue | Vercel (frontend), Render (backend), Neon.dev (DB), Cloudflare (DNS) |

---

## Estructura del proyecto

```
personal-shelf/
├── backend/
│   ├── config.py                # Configuración (DB, JWT, API keys, paths)
│   ├── db.py                    # Engine async + session factory
│   ├── main.py                  # App FastAPI, CORS, routers, health check
│   ├── dependencies.py          # get_current_user, require_admin (JWT)
│   ├── alembic.ini              # Config de Alembic
│   ├── requirements.txt         # Dependencias Python
│   ├── mcp/
│   │   └── server.py            # Servidor MCP con herramientas IA
│   ├── migrations/
│   │   ├── env.py               # Alembic async env
│   │   └── versions/
│   │       ├── 001_initial.py
│   │       ├── 002_social_login.py
│   │       ├── 003_add_recommendations_table.py
│   │       ├── 004_add_suggestions_table.py
│   │       ├── 005_recommendations_status_column.py
│   │       ├── 006_add_pending_at.py
│   │       └── 007_image_path_to_external_urls.py
│   ├── models/
│   │   ├── media.py             # MediaItem, Tag, media_tags
│   │   ├── user.py              # User, FriendRequest, friendships
│   │   ├── recommendation.py    # Recommendation
│   │   └── suggestion.py        # Suggestion
│   ├── routers/
│   │   ├── admin.py             # Dashboard admin (stats globales)
│   │   ├── auth.py              # Registro, login, refresh, solicitud de acceso
│   │   ├── media.py             # CRUD media items + metadata search
│   │   ├── stats.py             # Estadísticas del catálogo
│   │   ├── friends.py           # Solicitudes de amistad, amigos, búsqueda
│   │   ├── feed.py              # Feed social + colección de amigo
│   │   ├── recommendations.py   # Recomendaciones entre amigos
│   │   ├── explore.py           # Catálogo global + añadir a estantería
│   │   └── suggestions.py       # Buzón de sugerencias (feature/bug)
│   ├── schemas/
│   │   ├── admin.py             # AdminStatsResponse y sub-schemas
│   │   ├── auth.py              # UserRegister, UserLogin, TokenResponse, etc.
│   │   ├── media.py             # MediaCreate, MediaResponse, filtros, etc.
│   │   ├── social.py            # FriendRequest/Response, FeedEntry, etc.
│   │   ├── recommendation.py    # RecommendationCreate/Response, etc.
│   │   ├── explore.py           # ExploreItem, ExploreResult, ExploreAddRequest
│   │   └── suggestion.py        # SuggestionCreate/Response, SuggestionList
│   └── services/
│       ├── admin_stats_service.py    # Estadísticas globales para admin
│       ├── allowed_admins_service.py # Gestión de admins (fichero allowed_admins)
│       ├── auth_service.py           # Registro, login, JWT, bcrypt
│       ├── media_service.py          # CRUD + filtros + paginación + tags
│       ├── stats_service.py          # Agregaciones y estadísticas
│       ├── image_service.py          # URLs de imágenes externas (TMDB + Open Library)
│       ├── metadata_service.py       # Búsqueda de metadatos (TMDB + Open Library)
│       ├── friend_service.py         # Solicitudes, amistades, búsqueda de usuarios
│       ├── feed_service.py           # Feed social + colección de amigo
│       ├── recommendation_service.py # Envío/listado/aceptar/descartar recomendaciones
│       ├── explore_service.py        # Catálogo global deduplicado + señales sociales
│       ├── suggestion_service.py     # Sugerencias + integración GitHub Issues
│       └── github_service.py         # PRs de acceso + issues de sugerencias
├── frontend/
│   ├── package.json
│   ├── vite.config.js           # Proxy /api → backend, PWA config
│   ├── index.html
│   ├── eslint.config.js
│   └── src/
│       ├── main.js              # Entry point Vue
│       ├── App.vue              # Layout: sidebar colapsable, navegación, badge recomendaciones
│       ├── api/
│       │   ├── auth.js          # register, login, refresh, requestAccess
│       │   ├── media.js         # CRUD, filtros, metadata search, tags
│       │   ├── social.js        # Amigos, solicitudes, búsqueda, feed, colección
│       │   ├── recommendations.js # Enviar, listar, aceptar, descartar, unread count
│       │   ├── suggestions.js   # Crear, listar propias, listar todas
│       │   └── admin.js         # Estadísticas admin
│       ├── composables/
│       │   ├── useAuth.js       # Estado auth, login/register/logout, refresh automático
│       │   ├── useMedia.js      # CRUD media items
│       │   ├── useExplore.js    # Catálogo global con filtros
│       │   ├── useRecommendations.js # Recomendaciones recibidas + unread count
│       │   └── useSuggestions.js # Sugerencias del usuario
│       ├── components/
│       │   ├── FilterBar.vue    # Barra de filtros (tipo, estado, búsqueda, tag)
│       │   ├── MediaCard.vue    # Tarjeta de media item
│       │   ├── MediaForm.vue    # Formulario creación/edición con autofill de metadatos
│       │   ├── Pagination.vue   # Controles de paginación
│       │   ├── RatingInput.vue  # Selector de puntuación 1-10
│       │   ├── TagInput.vue     # Input de tags con autocompletado
│       │   ├── ConfirmDialog.vue # Diálogo de confirmación
│       │   ├── ExploreCard.vue  # Tarjeta de item en catálogo global
│       │   ├── RecommendModal.vue # Modal para recomendar a amigos
│       │   └── ReloadPrompt.vue # Notificación de actualización PWA
│       ├── router/
│       │   └── index.js         # Rutas + navigation guards (auth + admin)
│       └── views/
│           ├── LoginView.vue         # Login (email/username + contraseña)
│           ├── RegisterView.vue      # Registro de usuario
│           ├── CatalogView.vue       # Catálogo personal con filtros y paginación
│           ├── MediaDetailView.vue   # Detalle, creación y edición de items
│           ├── StatsView.vue         # Estadísticas del catálogo personal
│           ├── ExploreView.vue       # Catálogo global con señales sociales
│           ├── FriendsView.vue       # Gestión de amigos y solicitudes
│           ├── FriendCollectionView.vue # Colección de un amigo (solo lectura)
│           ├── FeedView.vue          # Feed social (redirige a Explore)
│           ├── RecommendationsView.vue # Recomendaciones recibidas
│           ├── SuggestionsView.vue   # Buzón de sugerencias
│           └── AdminView.vue         # Dashboard admin
├── tests/                       # 23 archivos de tests (pytest + Hypothesis)
├── allowed_admins               # Lista de emails con acceso admin
├── render.yaml                  # Config de despliegue en Render
├── DEPLOY.md                    # Guía de despliegue completa
└── .gitignore
```

---

## Requisitos previos

- **Python 3.11+**
- **Node.js 20+** y npm
- **PostgreSQL 16** (opciones en macOS):
  - Homebrew: `brew install postgresql@16`
  - Docker: `docker run -d --name pg16 -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:16`
  - [Postgres.app](https://postgresapp.com/) — descarga e instala, arranca con un click

---

## Arranque local para desarrollo

### 1. Clonar y entrar al proyecto

```bash
git clone <repo-url>
cd personal-shelf
```

### 2. Preparar PostgreSQL

Asegúrate de que PostgreSQL está corriendo en `localhost:5432`. Crea la base de datos:

```bash
createdb media_tracker
psql -U postgres -c "ALTER USER postgres WITH PASSWORD 'postgres';"
```

### 3. Backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
pip install ruff pytest

# Ejecutar migraciones
cd backend && alembic upgrade head && cd ..

# Arrancar el servidor
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Backend en `http://localhost:8000`. Swagger UI en `http://localhost:8000/docs`.

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend en `http://localhost:5173`. Vite hace proxy automático de `/api` al backend.

---

## Base de datos y migraciones

Conexión por defecto:
```
postgresql+asyncpg://postgres:postgres@localhost:5432/media_tracker
```

Sobreescribible con `DATABASE_URL`.

### Migraciones

| # | Archivo | Descripción |
|---|---------|-------------|
| 001 | `001_initial.py` | Tablas media_items, tags, media_tags |
| 002 | `002_social_login.py` | Tablas users, friendships, friend_requests + FK user_id en media_items |
| 003 | `003_add_recommendations_table.py` | Tabla recommendations |
| 004 | `004_add_suggestions_table.py` | Tabla suggestions con integración GitHub |
| 005 | `005_recommendations_status_column.py` | Migración de is_read boolean a status enum (pending/accepted/dismissed) |
| 006 | `006_add_pending_at.py` | Columna pending_at en media_items |
| 007 | `007_image_path_to_external_urls.py` | Nullifica image_path locales obsoletos (los que no empiezan con `http`) |

### Comandos de Alembic

```bash
cd backend
alembic upgrade head          # Aplicar todas las migraciones
alembic current               # Ver estado actual
alembic revision --autogenerate -m "descripción"  # Nueva migración
alembic downgrade -1          # Revertir última
```

---

## API REST — Endpoints

Base URL: `http://localhost:8000`

Todos los endpoints (excepto auth y health) requieren header `Authorization: Bearer <access_token>`.

### Autenticación

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/api/auth/register` | Registrar usuario (email, username, password) → tokens + user |
| `POST` | `/api/auth/login` | Login con email o username + password → tokens + user |
| `POST` | `/api/auth/refresh` | Renovar tokens con refresh_token |
| `POST` | `/api/auth/request-access` | Solicitar acceso (crea PR en GitHub) |

### Media Items

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/api/media` | Crear item (autofill de metadatos + imagen automática) |
| `GET` | `/api/media` | Listar con filtros y paginación |
| `GET` | `/api/media/{id}` | Obtener item por ID |
| `PUT` | `/api/media/{id}` | Actualizar item |
| `DELETE` | `/api/media/{id}` | Eliminar item |
| `PATCH` | `/api/media/{id}/status` | Cambiar estado (pending/in_progress/completed) |
| `PATCH` | `/api/media/{id}/rating` | Asignar puntuación (1-10) |
| `PUT` | `/api/media/{id}/tags` | Reemplazar tags |
| `GET` | `/api/media/{id}/image` | Obtener URL de imagen |
| `GET` | `/api/media/metadata-search` | Buscar metadatos en TMDB/Open Library |
| `GET` | `/api/media/tags` | Listar tags del usuario |

### Filtros de listado (`GET /api/media`)

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `media_type` | `movie` / `book` / `series` | Filtrar por tipo |
| `status` | `pending` / `in_progress` / `completed` | Filtrar por estado |
| `search` | string | Búsqueda por título (case-insensitive) |
| `tag` | string | Filtrar por nombre de tag |
| `page` | int (≥1) | Página (default: 1) |
| `size` | int (1-100) | Items por página (default: 20) |

### Amigos

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/api/friends/requests` | Enviar solicitud de amistad |
| `GET` | `/api/friends/requests/pending` | Solicitudes recibidas pendientes |
| `GET` | `/api/friends/requests/sent` | Solicitudes enviadas pendientes |
| `POST` | `/api/friends/requests/{id}/accept` | Aceptar solicitud |
| `POST` | `/api/friends/requests/{id}/reject` | Rechazar solicitud |
| `GET` | `/api/friends` | Listar amigos confirmados |
| `DELETE` | `/api/friends/{id}` | Eliminar amistad |
| `GET` | `/api/friends/search` | Buscar usuarios (excluye amigos y pendientes) |

### Feed social

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/api/feed` | Feed de actividad de amigos (últimos 30 días, max 20/página) |
| `GET` | `/api/feed/friends/{id}/collection` | Colección de un amigo (con filtros) |

### Recomendaciones

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/api/recommendations` | Enviar recomendación a un amigo |
| `GET` | `/api/recommendations` | Listar recomendaciones recibidas |
| `GET` | `/api/recommendations/unread-count` | Conteo de recomendaciones pendientes |
| `POST` | `/api/recommendations/{id}/accept` | Aceptar (añade item al catálogo) |
| `POST` | `/api/recommendations/{id}/dismiss` | Descartar recomendación |

### Explore (catálogo global)

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/api/explore` | Catálogo global deduplicado con señales sociales |
| `POST` | `/api/explore/add` | Añadir item del explore a tu estantería |

Filtros de explore: `media_type`, `search`, `tag`, `sort` (title_asc, title_desc, friends, activity), `page`, `size`.

### Sugerencias

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/api/suggestions` | Crear sugerencia (feature o bug) → crea issue en GitHub |
| `GET` | `/api/suggestions/mine` | Listar mis sugerencias |
| `GET` | `/api/suggestions` | Listar todas las sugerencias |

### Estadísticas

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/api/stats` | Estadísticas del catálogo personal |

### Admin

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/api/admin/stats` | Estadísticas globales (requiere rol admin) |

Incluye: métricas de usuarios (total, nuevos/activos esta semana), métricas de contenido (por tipo/estado, rating medio), métricas sociales (amistades, solicitudes, tags), rankings (top usuarios, top tags), actividad reciente.

### Health check

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/api/health` | Estado del backend y conexión a DB |

### Imágenes

Las imágenes se almacenan como URLs externas directas en `image_path` (e.g. `https://image.tmdb.org/t/p/w500/...`, `https://covers.openlibrary.org/b/id/...-L.jpg`). El `ImageService` busca la imagen en TMDB (películas/series) u Open Library (libros) y devuelve la URL externa sin descargar nada a disco. El frontend las muestra directamente desde las CDN de origen.

---

## Servidor MCP

El proyecto incluye un servidor MCP (Model Context Protocol) en `backend/mcp/server.py` que expone herramientas para que asistentes IA interactúen con el catálogo:

| Herramienta | Descripción |
|-------------|-------------|
| `create_media` | Crear un media item |
| `delete_media` | Eliminar un item |
| `update_media` | Actualizar un item |
| `list_media` | Listar con filtros |
| `update_status` | Cambiar estado |
| `rate_media` | Asignar puntuación |
| `manage_tags` | Gestionar tags |
| `get_stats` | Obtener estadísticas |

---

## Frontend

### Rutas

| Ruta | Vista | Descripción | Acceso |
|------|-------|-------------|--------|
| `/login` | LoginView | Login con email/username | Pública |
| `/register` | RegisterView | Registro de usuario | Pública |
| `/` | CatalogView | Catálogo personal con filtros, búsqueda y paginación | Protegida |
| `/media/new` | MediaDetailView | Formulario de creación con autofill de metadatos | Protegida |
| `/media/:id` | MediaDetailView | Detalle y edición de un item | Protegida |
| `/stats` | StatsView | Estadísticas visuales del catálogo | Protegida |
| `/explore` | ExploreView | Catálogo global con señales sociales | Protegida |
| `/friends` | FriendsView | Gestión de amigos, solicitudes y búsqueda | Protegida |
| `/friends/:id/collection` | FriendCollectionView | Colección de un amigo (solo lectura) | Protegida |
| `/recommendations` | RecommendationsView | Recomendaciones recibidas (aceptar/descartar) | Protegida |
| `/suggestions` | SuggestionsView | Buzón de sugerencias (feature/bug) | Protegida |
| `/admin` | AdminView | Dashboard admin con estadísticas globales | Admin |

### Componentes

- `FilterBar` — barra de filtros (tipo, estado, búsqueda, tag)
- `MediaCard` — tarjeta de media item en el catálogo
- `MediaForm` — formulario de creación/edición con búsqueda de metadatos y autofill
- `Pagination` — controles de paginación
- `RatingInput` — selector de puntuación 1-10
- `TagInput` — input de tags con autocompletado
- `ConfirmDialog` — diálogo de confirmación para acciones destructivas
- `ExploreCard` — tarjeta de item en el catálogo global (con señales sociales)
- `RecommendModal` — modal para recomendar items a amigos (selección múltiple + mensaje)
- `ReloadPrompt` — notificación de actualización PWA disponible

### Composables

- `useAuth` — estado de autenticación, login/register/logout, refresh automático de tokens, persistencia en localStorage
- `useMedia` — CRUD de media items, filtros, paginación
- `useExplore` — catálogo global con filtros y ordenación
- `useRecommendations` — recomendaciones recibidas, unread count, aceptar/descartar
- `useSuggestions` — crear y listar sugerencias

### Navegación

El sidebar colapsable incluye:
- Catalog, Explore, Friends, Recommendations (con badge de pendientes), Suggestions, Stats
- Panel admin (solo visible para admins)
- Username del usuario autenticado + botón de logout

### Build de producción

```bash
cd frontend
npm run build
```

Los archivos se generan en `frontend/dist/`. La app incluye soporte PWA (vite-plugin-pwa) con ReloadPrompt para actualizaciones.

---

## Tests

El proyecto usa pytest con Hypothesis para property-based testing en backend, y vitest con vue-test-utils para frontend. Los tests de backend corren contra SQLite in-memory (no necesitan PostgreSQL).

```bash
# Backend — todos los tests
python -m pytest tests/ -v

# Backend — solo property tests
python -m pytest tests/test_property_*.py -v

# Frontend — todos los tests
cd frontend && npm run test
```

### Archivos de test (23 archivos backend)

| Archivo | Cobertura |
|---------|-----------|
| `test_auth_router.py` | Registro, login, refresh, errores auth |
| `test_media_router.py` | CRUD endpoints HTTP |
| `test_friends_router.py` | Solicitudes, amistades, búsqueda |
| `test_feed_router.py` | Feed social, colección de amigo |
| `test_recommendation_router.py` | Envío, listado, aceptar, descartar |
| `test_stats_service.py` | Servicio de estadísticas |
| `test_stats_export_routers.py` | Endpoints de stats |
| `test_image_service.py` | Búsqueda de URLs de imágenes externas |
| `test_health_cors.py` | Health check y CORS |
| `test_property_auth.py` | Props 1-10: registro, login, tokens, refresh |
| `test_property_creation.py` | Props: creación de items |
| `test_property_update_delete.py` | Props: actualización y eliminación |
| `test_property_filtering.py` | Props: filtrado y búsqueda |
| `test_property_status_rating_tags.py` | Props: cambios de estado, rating, tags |
| `test_property_stats_export.py` | Props: estadísticas |
| `test_property_default_image.py` | Props: URL de imagen externa |
| `test_property_mcp.py` | Props: herramientas MCP |
| `test_property_multitenancy.py` | Props 11-14: aislamiento multi-usuario |
| `test_property_friends.py` | Props 15-23: sistema de amistades |
| `test_property_feed.py` | Props 24-27: feed social |
| `test_property_recommendations.py` | Props: recomendaciones |
| `test_property_datetime_bugfix.py` | Props: timestamps de estado |
| `test_property_preservation_bugfix.py` | Props: preservación de campos en update |

---

## Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/media_tracker` | URL de conexión a PostgreSQL |
| `ALLOWED_ORIGINS` | `None` (permite todo en dev) | Orígenes CORS separados por coma |
| `JWT_SECRET_KEY` | `super-secret-dev-key-change-in-production` | Clave secreta para firmar JWT |
| `TMDB_API_KEY` | `""` | API key de TMDB (metadatos + imágenes de películas/series) |
| `GITHUB_TOKEN` | `""` | Personal Access Token de GitHub (sugerencias + acceso) |
| `GITHUB_REPO` | `""` | Repositorio GitHub (formato `owner/repo`) |
| `GITHUB_DEFAULT_BRANCH` | `main` | Rama por defecto del repo |
| `VITE_API_BASE_URL` | (solo producción) | URL base del backend para el frontend |
| `VITE_IMAGES_BASE_URL` | (solo producción) | URL base para imágenes locales (obsoleta — las imágenes ahora son URLs externas directas) |

---

## Modelo de datos

### users

| Columna | Tipo | Notas |
|---------|------|-------|
| id | INTEGER PK | Autoincrement |
| email | VARCHAR(255) | UNIQUE, NOT NULL |
| username | VARCHAR(100) | UNIQUE, NOT NULL |
| password_hash | VARCHAR(255) | NOT NULL (bcrypt) |
| created_at | TIMESTAMP | server_default: now() |

### media_items

| Columna | Tipo | Notas |
|---------|------|-------|
| id | INTEGER PK | Autoincrement |
| user_id | INTEGER FK | → users.id, NOT NULL |
| title | VARCHAR(255) | NOT NULL |
| media_type | VARCHAR(20) | `movie`, `book`, `series` |
| status | VARCHAR(20) | `pending`, `in_progress`, `completed` (default: pending) |
| rating | INTEGER | Nullable, 1-10 |
| year | INTEGER | Nullable |
| creator | VARCHAR(255) | Nullable |
| notes | TEXT | Nullable |
| image_path | VARCHAR(500) | Nullable, URL externa (TMDB / Open Library) |
| created_at | TIMESTAMP | server_default: now() |
| updated_at | TIMESTAMP | server_default: now(), onupdate: now() |
| started_at | TIMESTAMP | Nullable (auto al cambiar a in_progress) |
| completed_at | TIMESTAMP | Nullable (auto al cambiar a completed) |
| pending_at | TIMESTAMP | Nullable (auto al cambiar a pending) |

### tags

| Columna | Tipo | Notas |
|---------|------|-------|
| id | INTEGER PK | Autoincrement |
| name | VARCHAR(100) | UNIQUE, NOT NULL |

### media_tags (M:N)

| Columna | Tipo | Notas |
|---------|------|-------|
| media_id | INTEGER FK | → media_items.id (CASCADE) |
| tag_id | INTEGER FK | → tags.id (CASCADE) |

### friendships (bidireccional)

| Columna | Tipo | Notas |
|---------|------|-------|
| user_id | INTEGER FK | → users.id (CASCADE), PK |
| friend_id | INTEGER FK | → users.id (CASCADE), PK |
| created_at | TIMESTAMP | server_default: now() |

### friend_requests

| Columna | Tipo | Notas |
|---------|------|-------|
| id | INTEGER PK | Autoincrement |
| from_user_id | INTEGER FK | → users.id (CASCADE) |
| to_user_id | INTEGER FK | → users.id (CASCADE) |
| status | VARCHAR(20) | `pending`, `accepted`, `rejected` |
| created_at | TIMESTAMP | server_default: now() |

### recommendations

| Columna | Tipo | Notas |
|---------|------|-------|
| id | INTEGER PK | Autoincrement |
| sender_id | INTEGER FK | → users.id (CASCADE) |
| receiver_id | INTEGER FK | → users.id (CASCADE) |
| media_item_id | INTEGER FK | → media_items.id (CASCADE) |
| message | TEXT | Nullable (max 500 chars) |
| status | VARCHAR(20) | `pending`, `accepted`, `dismissed` |
| created_at | TIMESTAMP | server_default: now() |
| UNIQUE | | (sender_id, receiver_id, media_item_id) |
| INDEX | | (receiver_id, status) |

### suggestions

| Columna | Tipo | Notas |
|---------|------|-------|
| id | INTEGER PK | Autoincrement |
| user_id | INTEGER FK | → users.id (CASCADE) |
| title | VARCHAR(255) | NOT NULL |
| description | TEXT | NOT NULL |
| type | VARCHAR(20) | `feature` o `bug` |
| github_issue_url | VARCHAR(500) | Nullable (auto-creada) |
| github_issue_number | INTEGER | Nullable |
| created_at | TIMESTAMP | server_default: now() |

---

## Despliegue

La app se despliega en:
- **Frontend**: Vercel (SPA con PWA)
- **Backend**: Render (Python web service)
- **Base de datos**: Neon.dev (PostgreSQL serverless)
- **DNS**: Cloudflare (shelfd.net)

Dominio: `shelfd.net`

Ver `DEPLOY.md` para la guía completa paso a paso.

---

## Notas y decisiones técnicas

- El backend usa SQLAlchemy 2.0 async con `asyncpg`. Todas las queries son async.
- Alembic está configurado para async con el patrón `async_engine_from_config` + `run_async_migrations()`.
- Los tags usan una relación many-to-many con `lazy="selectin"` para evitar N+1 queries.
- Las imágenes se obtienen como URLs externas de TMDB (películas/series) y Open Library (libros). `ImageService.fetch_image()` retorna `str | None` (URL completa o None). No hay almacenamiento local de imágenes — `image_path` en la DB contiene directamente la URL externa. Esto elimina problemas con filesystems efímeros (Render) y simplifica el despliegue.
- El frontend (`resolveImageUrl()` en `media.js`) detecta URLs que empiezan con `http` y las pasa directamente, por lo que el cambio a URLs externas fue transparente.
- Los metadatos (año, creador, descripción, géneros) se autocompletan desde TMDB (películas/series) y Open Library (libros) al crear un item.
- La autenticación usa JWT con access token (30 min) y refresh token (7 días). Las contraseñas se hashean con bcrypt.
- Multi-tenancy: cada usuario solo ve y modifica sus propios items. Los servicios filtran por `user_id` en todas las operaciones.
- Las amistades son bidireccionales: al aceptar una solicitud se insertan dos filas en `friendships` (A→B y B→A).
- Las recomendaciones usan un sistema de estados (pending → accepted/dismissed) en lugar de un simple boolean is_read.
- El catálogo Explore deduplica items por `(LOWER(title), media_type)` y calcula señales sociales (amigos que lo tienen, amigos que lo recomendaron).
- Las sugerencias se integran con GitHub Issues: al crear una sugerencia, se crea automáticamente una issue en el repositorio configurado.
- El sistema de acceso usa un fichero `allowed_admins` con emails autorizados. Las solicitudes de acceso crean PRs en GitHub para añadir el email.
- El frontend usa composables para compartir lógica de API entre vistas, con refs independientes por invocación para evitar state leakage.
- Los property tests usan `@given` de Hypothesis con `asyncio.run()` internamente (no `@pytest.mark.asyncio`) porque `@given` no es compatible con async fixtures.
- Los tests de router usan `httpx.AsyncClient` + `ASGITransport` con `app.dependency_overrides` para inyectar sesiones SQLite in-memory.
- Los routers se registran en `main.py` antes del health check.
- Vite hace proxy de `/api` al backend en desarrollo, evitando problemas de CORS.
- La app incluye soporte PWA con `vite-plugin-pwa` y un componente `ReloadPrompt` para notificar actualizaciones.
