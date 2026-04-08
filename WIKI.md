# Personal Shelf — Wiki

Personal Shelf es un **Media Tracker** personal: una aplicación web para catalogar películas, libros y series, hacer seguimiento de tu progreso de consumo, puntuar, etiquetar y obtener estadísticas de tu colección.

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
13. [Notas y decisiones técnicas](#notas-y-decisiones-técnicas)

---

## Arquitectura

```
┌─────────────────┐       ┌──────────────────┐       ┌────────────┐
│   Vue 3 SPA     │──────▶│  FastAPI Backend  │──────▶│ PostgreSQL │
│   (Vite dev)    │ proxy │  (uvicorn)        │ async │            │
│   :5173         │ /api  │  :8000            │ pg    │  :5432     │
└─────────────────┘       └──────────────────┘       └────────────┘
                                │
                                ├── /images (static files)
                                └── MCP Server (herramientas IA)
```

El frontend en desarrollo corre en Vite (:5173) y hace proxy de `/api` y `/images` al backend FastAPI (:8000). El backend se conecta a PostgreSQL vía `asyncpg`.

---

## Stack tecnológico

| Capa | Tecnología |
|------|-----------|
| Frontend | Vue 3, Vue Router 4, Vite 5 |
| Backend | Python 3.11+, FastAPI, Uvicorn |
| ORM | SQLAlchemy 2.0 (async) |
| Base de datos | PostgreSQL 16 + asyncpg |
| Migraciones | Alembic (async) |
| Tests | pytest, Hypothesis (property-based testing) |
| Linting | Ruff (Python), ESLint + eslint-plugin-vue (JS/Vue) |
| MCP | mcp (Python) — herramientas para asistentes IA |

---

## Estructura del proyecto

```
personal-shelf/
├── backend/
│   ├── config.py              # Configuración (DB URL, paths, API keys)
│   ├── db.py                  # Engine async + session factory
│   ├── main.py                # App FastAPI, CORS, routers, static files
│   ├── alembic.ini            # Config de Alembic
│   ├── requirements.txt       # Dependencias Python
│   ├── images/                # Almacenamiento de imágenes descargadas
│   ├── mcp/
│   │   └── server.py          # Servidor MCP con herramientas IA
│   ├── migrations/
│   │   ├── env.py             # Alembic async env
│   │   └── versions/
│   │       └── 001_initial.py # Migración inicial
│   ├── models/
│   │   └── media.py           # Modelos SQLAlchemy (MediaItem, Tag)
│   ├── routers/
│   │   ├── media.py           # CRUD de media items
│   │   ├── stats.py           # Estadísticas del catálogo
│   │   └── export_import.py   # Export/import JSON
│   ├── schemas/
│   │   └── media.py           # Schemas Pydantic (request/response)
│   └── services/
│       ├── media_service.py   # Lógica CRUD + filtros + paginación
│       ├── stats_service.py   # Agregaciones y estadísticas
│       ├── export_service.py  # Serialización export/import
│       └── image_service.py   # Descarga automática de imágenes
├── frontend/
│   ├── package.json
│   ├── vite.config.js         # Proxy /api y /images → backend
│   ├── index.html
│   ├── eslint.config.js
│   └── src/
│       ├── main.js            # Entry point Vue
│       ├── App.vue            # Layout principal
│       ├── api/
│       │   └── media.js       # Cliente HTTP (fetch wrapper)
│       ├── composables/
│       │   └── useMedia.js    # Composable compartido
│       ├── components/
│       │   ├── FilterBar.vue
│       │   ├── MediaCard.vue
│       │   ├── MediaForm.vue
│       │   ├── Pagination.vue
│       │   ├── RatingInput.vue
│       │   ├── TagInput.vue
│       │   └── ConfirmDialog.vue
│       ├── router/
│       │   └── index.js       # Rutas Vue Router
│       └── views/
│           ├── CatalogView.vue
│           ├── MediaDetailView.vue
│           ├── StatsView.vue
│           └── ImportExportView.vue
├── tests/
│   ├── conftest.py            # Fixtures compartidos
│   ├── test_media_router.py
│   ├── test_stats_service.py
│   ├── test_export_service.py
│   ├── test_image_service.py
│   ├── test_stats_export_routers.py
│   └── test_property_*.py     # 7 archivos de property-based tests
└── .gitignore
```

---

## Requisitos previos

Antes de arrancar necesitas tener instalado:

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

Asegúrate de que PostgreSQL está corriendo en `localhost:5432`. Crea la base de datos y configura el usuario:

```bash
# Si usas Postgres.app o Homebrew:
createdb media_tracker

# Si el usuario postgres no tiene password, ponle uno:
psql -U postgres -c "ALTER USER postgres WITH PASSWORD 'postgres';"
```

Si usas Docker:
```bash
docker run -d --name pg16 \
  -p 5432:5432 \
  -e POSTGRES_PASSWORD=postgres \
  postgres:16

# Espera unos segundos y crea la DB:
docker exec pg16 createdb -U postgres media_tracker
```

### 3. Backend

```bash
# Crear entorno virtual
python3 -m venv .venv
source .venv/bin/activate

# Instalar dependencias
pip install -r backend/requirements.txt

# Instalar herramientas de desarrollo
pip install ruff pytest

# Ejecutar migraciones
cd backend
alembic upgrade head
cd ..

# Arrancar el servidor
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

El backend estará disponible en `http://localhost:8000`. La documentación interactiva de la API en `http://localhost:8000/docs`.

### 4. Frontend

En otra terminal:

```bash
cd frontend

# Instalar dependencias
npm install

# Arrancar servidor de desarrollo
npm run dev
```

El frontend estará en `http://localhost:5173`. Vite hace proxy automático de `/api` y `/images` al backend.

### 5. Verificar que todo funciona

- Abre `http://localhost:5173` — deberías ver el catálogo vacío
- Abre `http://localhost:8000/docs` — Swagger UI con todos los endpoints
- Crea un media item desde la UI o con curl:

```bash
curl -X POST http://localhost:8000/api/media \
  -H "Content-Type: application/json" \
  -d '{"title": "Dune", "media_type": "movie", "year": 2021, "tags": ["sci-fi"]}'
```

---

## Base de datos y migraciones

La conexión por defecto es:
```
postgresql+asyncpg://postgres:postgres@localhost:5432/media_tracker
```

Se puede sobreescribir con la variable de entorno `DATABASE_URL`.

### Comandos de Alembic

```bash
cd backend

# Aplicar todas las migraciones pendientes
alembic upgrade head

# Ver el estado actual
alembic current

# Crear una nueva migración (autogenerate)
alembic revision --autogenerate -m "descripción del cambio"

# Revertir la última migración
alembic downgrade -1
```

---

## API REST — Endpoints

Base URL: `http://localhost:8000`

### Media Items

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/api/media` | Crear un media item |
| `GET` | `/api/media` | Listar con filtros y paginación |
| `GET` | `/api/media/{id}` | Obtener un item por ID |
| `PUT` | `/api/media/{id}` | Actualizar un item |
| `DELETE` | `/api/media/{id}` | Eliminar un item |
| `PATCH` | `/api/media/{id}/status` | Cambiar estado (pending/in_progress/completed) |
| `PATCH` | `/api/media/{id}/rating` | Asignar puntuación (1-10) |
| `PUT` | `/api/media/{id}/tags` | Reemplazar tags |
| `GET` | `/api/media/{id}/image` | Obtener URL de la imagen |

### Filtros de listado (`GET /api/media`)

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `media_type` | `movie` / `book` / `series` | Filtrar por tipo |
| `status` | `pending` / `in_progress` / `completed` | Filtrar por estado |
| `search` | string | Búsqueda por título (case-insensitive) |
| `tag` | string | Filtrar por nombre de tag |
| `page` | int (≥1) | Página (default: 1) |
| `size` | int (1-100) | Items por página (default: 20) |

### Estadísticas y Export/Import

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/api/stats` | Estadísticas del catálogo (conteos por tipo/estado, media de rating) |
| `GET` | `/api/export` | Exportar catálogo completo como JSON |
| `POST` | `/api/import` | Importar items desde JSON |

### Imágenes estáticas

Las imágenes se sirven en `/images/{filename}` como archivos estáticos.

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
| `export_catalog` | Exportar catálogo |
| `import_catalog` | Importar catálogo |

---

## Frontend

### Rutas

| Ruta | Vista | Descripción |
|------|-------|-------------|
| `/` | CatalogView | Catálogo principal con filtros, búsqueda y paginación |
| `/media/new` | MediaDetailView | Formulario de creación |
| `/media/:id` | MediaDetailView | Detalle y edición de un item |
| `/stats` | StatsView | Estadísticas visuales del catálogo |
| `/import-export` | ImportExportView | Exportar/importar catálogo JSON |

### Componentes

- `FilterBar` — barra de filtros (tipo, estado, búsqueda, tag)
- `MediaCard` — tarjeta de media item en el catálogo
- `MediaForm` — formulario de creación/edición
- `Pagination` — controles de paginación
- `RatingInput` — selector de puntuación 1-10
- `TagInput` — input de tags con autocompletado
- `ConfirmDialog` — diálogo de confirmación para acciones destructivas

### Build de producción

```bash
cd frontend
npm run build
```

Los archivos se generan en `frontend/dist/`. Para servir el frontend desde FastAPI en producción, puedes montar `dist/` como archivos estáticos adicionales.

---

## Tests

El proyecto usa pytest con Hypothesis para property-based testing. Los tests corren contra una base de datos SQLite in-memory (no necesitan PostgreSQL).

```bash
# Ejecutar todos los tests
python -m pytest tests/ -v

# Ejecutar solo los property tests
python -m pytest tests/test_property_*.py -v

# Ejecutar un archivo específico
python -m pytest tests/test_media_router.py -v
```

### Cobertura de tests (85 tests)

- **Unit tests**: servicios (media, stats, export, image)
- **Router tests**: endpoints HTTP con httpx + ASGITransport
- **Property tests** (Hypothesis): 15 propiedades de correctitud que validan creación, actualización, eliminación, filtrado, estadísticas, export/import, imágenes, MCP, etc.

---

## Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/media_tracker` | URL de conexión a PostgreSQL |
| `TMDB_API_KEY` | `""` (vacío) | API key de TMDB para descarga automática de imágenes |

---

## Modelo de datos

### media_items

| Columna | Tipo | Notas |
|---------|------|-------|
| id | INTEGER PK | Autoincrement |
| title | VARCHAR(255) | NOT NULL |
| media_type | VARCHAR(20) | `movie`, `book`, `series` |
| status | VARCHAR(20) | `pending`, `in_progress`, `completed` (default: pending) |
| rating | INTEGER | Nullable, 1-10 |
| year | INTEGER | Nullable |
| creator | VARCHAR(255) | Nullable |
| notes | TEXT | Nullable |
| image_path | VARCHAR(500) | Nullable |
| created_at | TIMESTAMP | server_default: now() |
| updated_at | TIMESTAMP | server_default: now(), onupdate: now() |
| started_at | TIMESTAMP | Nullable |
| completed_at | TIMESTAMP | Nullable |

### tags

| Columna | Tipo | Notas |
|---------|------|-------|
| id | INTEGER PK | Autoincrement |
| name | VARCHAR(100) | UNIQUE, NOT NULL |

### media_tags (tabla de relación M:N)

| Columna | Tipo | Notas |
|---------|------|-------|
| media_id | INTEGER FK | → media_items.id (CASCADE) |
| tag_id | INTEGER FK | → tags.id (CASCADE) |

---

## Notas y decisiones técnicas

- El backend usa SQLAlchemy 2.0 async con `asyncpg`. Todas las queries son async.
- Alembic está configurado para async con el patrón `async_engine_from_config` + `run_async_migrations()`.
- Los tags usan una relación many-to-many con `lazy="selectin"` para evitar N+1 queries.
- Las imágenes se descargan automáticamente al crear/actualizar un item (si `TMDB_API_KEY` está configurada) y se almacenan en `backend/images/`.
- El frontend usa composables (`useMedia`) para compartir lógica de API entre vistas, con refs independientes por invocación para evitar state leakage.
- Los property tests usan `@given` de Hypothesis con `asyncio.run()` internamente (no `@pytest.mark.asyncio`) porque `@given` no es compatible con async fixtures.
- Los tests de router usan `httpx.AsyncClient` + `ASGITransport` con `app.dependency_overrides` para inyectar sesiones SQLite in-memory.
- El mount de `/images` como `StaticFiles` va después de los routers en `main.py` porque los mounts son catch-all.
- Vite hace proxy de `/api` y `/images` al backend en desarrollo, evitando problemas de CORS.
