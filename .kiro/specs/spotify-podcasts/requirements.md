# Requisitos — Integración Spotify: Podcasts como nuevo tipo de media

## Contexto

Personal Shelf permite catalogar películas, libros y series. Esta feature añade **podcast** como cuarto tipo de media, con integración de la Spotify Web API para autofill de metadatos (nombre, host/publisher, imagen, descripción, géneros). El enfoque es manual (Enfoque A): el usuario busca y añade podcasts como cualquier otro item. No hay OAuth de usuario ni sincronización automática.

## Glosario

| Término | Definición |
|---------|-----------|
| Spotify Web API | API REST de Spotify para buscar shows, episodios, etc. |
| Client Credentials Flow | Flujo OAuth de Spotify que usa `client_id` + `client_secret` para obtener un token de acceso sin usuario. Válido para búsquedas públicas. |
| Show | Término de Spotify para un podcast (serie completa). |
| `SPOTIFY_CLIENT_ID` | ID de la app registrada en Spotify Developer Dashboard. |
| `SPOTIFY_CLIENT_SECRET` | Secret de la app registrada en Spotify Developer Dashboard. |

---

## Requisitos funcionales

### Requisito 1 — Nuevo valor `podcast` en MediaType

El enum `MediaType` en `backend/schemas/media.py` debe incluir `podcast = "podcast"` como cuarto valor. Todos los endpoints, filtros, estadísticas y validaciones que usan `MediaType` deben aceptar `podcast` sin cambios adicionales (ya iteran sobre el enum).

### Requisito 2 — Spotify Client Credentials: obtención y cache de token

El backend debe implementar un método para obtener un access token de Spotify usando el Client Credentials flow (`POST https://accounts.spotify.com/api/token` con `grant_type=client_credentials`). El token dura 3600 segundos y debe cachearse en memoria (atributo de instancia del servicio) para evitar llamadas redundantes. Si `SPOTIFY_CLIENT_ID` o `SPOTIFY_CLIENT_SECRET` están vacíos, el servicio debe retornar lista vacía sin error.

### Requisito 3 — MetadataService: búsqueda de podcasts en Spotify

`MetadataService.search()` debe enrutar `media_type="podcast"` a un nuevo método `_search_spotify_metadata(title)` que:
1. Obtiene/renueva el token de acceso (Requisito 2).
2. Llama a `GET https://api.spotify.com/v1/search?type=show&q={title}&limit=5`.
3. Parsea cada resultado a `MetadataCandidate` con:
   - `title`: nombre del show
   - `year`: año de `copyrights` o None si no disponible
   - `creator`: campo `publisher`
   - `description`: campo `description` (truncado a 500 chars)
   - `image_url`: `images[0].url` (la de mayor resolución)
   - `genres`: lista vacía (Spotify no devuelve géneros para shows en la Search API)

### Requisito 4 — ImageService: soporte para podcasts

`ImageService.fetch_image()` debe enrutar `media_type="podcast"` a Spotify Search API (`type=show`) para obtener la imagen del podcast. El flujo es: buscar el show → extraer `images[0].url` → devolver la URL directamente (ya es una URL externa, consistente con el enfoque actual de TMDB/Open Library).

### Requisito 5 — Variables de entorno

Añadir a `backend/config.py`:
- `SPOTIFY_CLIENT_ID: str = os.getenv("SPOTIFY_CLIENT_ID", "")`
- `SPOTIFY_CLIENT_SECRET: str = os.getenv("SPOTIFY_CLIENT_SECRET", "")`

Añadir a `render.yaml` como env vars con `sync: false`.
Añadir a `.env.example`.

### Requisito 6 — Frontend: icono y filtro de podcast

- `MediaCard.vue`: añadir label "Podcast" en el mapa de tipos y color de borde para `type-podcast` (sugerir morado/violeta como color distintivo, consistente con la marca Spotify).
- `FilterBar.vue`: añadir opción "Podcast" en el select de tipo de media.
- `MediaForm.vue`: añadir opción "Podcast" en el select de tipo al crear/editar.
- `MediaDetailView.vue`: el tipo "podcast" debe mostrarse correctamente en la vista de detalle.

### Requisito 7 — Seed script: podcasts populares

Extender `backend/scripts/seed_explore.py` con una función `_fetch_spotify_podcasts()` que busque podcasts populares (e.g., "true crime", "technology", "comedy") y los añada al catálogo del sistema para el Explore.

### Requisito 8 — Compatibilidad con funcionalidades existentes

Todo el sistema existente debe funcionar con `podcast` sin cambios adicionales:
- CRUD (crear, leer, actualizar, eliminar)
- Cambio de estado (pending → in_progress → completed)
- Rating (1-10)
- Tags
- Recomendaciones entre amigos
- Explore (catálogo global)
- Estadísticas (by_type, by_status, avg_rating_by_type)
- MCP server tools

---

## Requisitos no funcionales

### Requisito 9 — Resiliencia ante fallos de Spotify API

Si la Spotify API no responde o las credenciales son inválidas, el servicio debe retornar lista vacía (metadatos) o None (imagen) sin propagar excepciones. El item se crea igualmente sin metadatos auto-rellenados.

### Requisito 10 — Sin migración de base de datos

El campo `media_type` es `VARCHAR(20)` en la DB, no un enum de PostgreSQL. Añadir `podcast` al enum de Pydantic es suficiente — no se necesita migración Alembic.

---

## Evolución futura (Enfoque B — fuera de alcance)

Para referencia, el Enfoque B incluiría:
- OAuth 2.0 PKCE flow para conectar la cuenta de Spotify del usuario
- Tabla `spotify_tokens` (user_id, access_token, refresh_token, expires_at)
- Sincronización automática de podcasts seguidos (`GET /v1/me/shows`)
- Historial de episodios escuchados (`GET /v1/me/player/recently-played`)
- Requiere revisión de app por Spotify si >25 usuarios
