# Diseño — Integración Spotify: Podcasts como nuevo tipo de media

## 1. Arquitectura

```
Usuario → MediaForm (tipo: podcast) → POST /api/media
                                         ↓
                                    media router
                                    ├── MetadataService._search_spotify_metadata()
                                    │     ↓
                                    │   Spotify API (Client Credentials)
                                    │   GET /v1/search?type=show
                                    │     ↓
                                    │   MetadataCandidate (title, publisher, image, desc)
                                    └── ImageService.fetch_image(title, "podcast")
                                          ↓
                                        Spotify API → images[0].url (URL externa directa)
```

## 2. Cambios por componente

### 2.1 Backend — Schema (`backend/schemas/media.py`)

```python
class MediaType(str, Enum):
    movie = "movie"
    book = "book"
    series = "series"
    podcast = "podcast"  # NUEVO
```

Sin otros cambios en schemas. `MediaCreate`, `MediaUpdate`, `MediaFilters`, `MediaResponse` ya usan `MediaType` como tipo.

### 2.2 Backend — Config (`backend/config.py`)

```python
# Spotify API (Client Credentials)
SPOTIFY_CLIENT_ID: str = os.getenv("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET: str = os.getenv("SPOTIFY_CLIENT_SECRET", "")
```

### 2.3 Backend — MetadataService (`backend/services/metadata_service.py`)

Nuevo método `_search_spotify_metadata()` + helper `_get_spotify_token()`:

```python
async def _get_spotify_token(self) -> str | None:
    """Obtiene/renueva token de Spotify via Client Credentials flow."""
    # Cache en self._spotify_token y self._spotify_token_expires
    # POST https://accounts.spotify.com/api/token
    # Body: grant_type=client_credentials
    # Header: Authorization: Basic base64(client_id:client_secret)

async def _search_spotify_metadata(self, title: str) -> list[MetadataCandidate]:
    """Busca podcasts (shows) en Spotify."""
    # GET https://api.spotify.com/v1/search?type=show&q={title}&limit=5
    # Header: Authorization: Bearer {token}
    # Parsea: name, publisher, description, images[0].url
```

Routing en `search()`:
```python
if media_type == "podcast":
    return await self._search_spotify_metadata(title)
```

### 2.4 Backend — ImageService (`backend/services/image_service.py`)

Nuevo método `_search_spotify_image()`:

```python
async def _search_spotify_image(self, title: str) -> str | None:
    """Busca imagen de podcast en Spotify."""
    # Reutiliza _get_spotify_token() del MetadataService
    # O implementa su propio token cache
    # GET /v1/search?type=show&q={title}&limit=1
    # Retorna images[0].url
```

Routing en `_search_image_url()`:
```python
if media_type == "podcast":
    return await self._search_spotify_image(title)
```

### 2.5 Backend — Token compartido

Para evitar duplicar la lógica de token, crear un helper module `backend/services/spotify_auth.py`:

```python
"""Spotify Client Credentials token management."""
import base64, time, httpx
from backend.config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET

_token: str | None = None
_expires_at: float = 0

async def get_spotify_token() -> str | None:
    """Retorna un token válido o None si las credenciales no están configuradas."""
    global _token, _expires_at
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        return None
    if _token and time.time() < _expires_at - 60:  # 60s margen
        return _token
    # POST https://accounts.spotify.com/api/token
    # ...
```

Tanto `MetadataService` como `ImageService` importan `get_spotify_token()`.

### 2.6 Frontend — MediaCard.vue

Añadir al mapa de tipos:
```javascript
const typeLabels = { movie: 'Película', book: 'Libro', series: 'Serie', podcast: 'Podcast' }
```

CSS para borde de podcast:
```css
.type-podcast { border-left-color: var(--color-type-podcast); }
```

En `App.vue` (design tokens):
```css
--color-type-podcast: #9b59b6;        /* violeta */
--color-type-podcast-bg: #f3e5f5;     /* violeta claro */
--color-type-podcast-text: #6a1b9a;   /* violeta oscuro */
```

### 2.7 Frontend — FilterBar.vue, MediaForm.vue

Añadir opción `podcast` en los selects de tipo de media. Ambos componentes ya iteran sobre opciones hardcodeadas — solo añadir la nueva entrada.

### 2.8 Seed script

Nueva función `_fetch_spotify_podcasts()` que busca 3-4 categorías populares y crea items con `media_type="podcast"`.

## 3. Propiedades de corrección

| # | Propiedad | Descripción |
|---|-----------|-------------|
| P1 | Podcast CRUD | Crear, leer, actualizar y eliminar un item con `media_type=podcast` funciona igual que movie/book/series |
| P2 | Spotify token cache | Dos llamadas consecutivas a `get_spotify_token()` no hacen dos requests HTTP si el token no ha expirado |
| P3 | Metadata search routing | `MetadataService.search(title, "podcast")` llama a Spotify, no a TMDB ni Open Library |
| P4 | Image search routing | `ImageService.fetch_image(title, "podcast")` llama a Spotify, no a TMDB ni Open Library |
| P5 | Resiliencia | Si Spotify API falla, `search()` retorna `[]` y `fetch_image()` retorna `None` sin excepción |
| P6 | Stats incluyen podcast | `GET /api/stats` incluye `podcast` en `by_type` cuando hay items de ese tipo |
| P7 | Filtro por podcast | `GET /api/media?media_type=podcast` solo retorna podcasts |

## 4. Manejo de errores

| Escenario | Comportamiento |
|-----------|---------------|
| `SPOTIFY_CLIENT_ID` vacío | `get_spotify_token()` retorna None, servicios retornan [] / None |
| Token expirado | Se renueva automáticamente en la siguiente llamada |
| Spotify API 429 (rate limit) | Log warning, retorna [] / None |
| Spotify API 5xx | Log exception, retorna [] / None |
| Show sin imágenes | `image_url` = None en MetadataCandidate |

## 5. Archivos afectados

| Archivo | Cambio |
|---------|--------|
| `backend/schemas/media.py` | Añadir `podcast` a `MediaType` |
| `backend/config.py` | Añadir `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET` |
| `backend/services/spotify_auth.py` | NUEVO — token management |
| `backend/services/metadata_service.py` | Nuevo `_search_spotify_metadata()` + routing |
| `backend/services/image_service.py` | Nuevo `_search_spotify_image()` + routing |
| `backend/scripts/seed_explore.py` | Nueva `_fetch_spotify_podcasts()` |
| `frontend/src/App.vue` | CSS custom properties para podcast |
| `frontend/src/components/MediaCard.vue` | Label + borde podcast |
| `frontend/src/components/FilterBar.vue` | Opción podcast en filtro |
| `frontend/src/components/MediaForm.vue` | Opción podcast en select |
| `frontend/src/components/ExploreCard.vue` | Label podcast |
| `.env.example` | Nuevas vars |
| `render.yaml` | Nuevas env vars |
