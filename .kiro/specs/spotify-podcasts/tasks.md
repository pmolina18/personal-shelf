# Tareas — Integración Spotify: Podcasts como nuevo tipo de media

## Tarea 1 — Schema + Config (Requisitos 1, 5, 10)

- [x] 1.1 Añadir `podcast = "podcast"` al enum `MediaType` en `backend/schemas/media.py`
- [x] 1.2 Añadir `SPOTIFY_CLIENT_ID` y `SPOTIFY_CLIENT_SECRET` a `backend/config.py`
- [x] 1.3 Añadir las variables a `.env.example`
- [x] 1.4 Añadir las variables a `render.yaml` con `sync: false`
- [x] 1.5 Verificar con `getDiagnostics` que no hay errores

## Tarea 2 — Spotify Auth helper (Requisito 2)

- [x] 2.1 Crear `backend/services/spotify_auth.py` con `get_spotify_token()`:
  - Client Credentials flow (`POST https://accounts.spotify.com/api/token`)
  - Cache en variables de módulo (`_token`, `_expires_at`)
  - Retorna `None` si las credenciales están vacías
  - Renueva automáticamente si el token está a <60s de expirar
- [x] 2.2 Verificar con `getDiagnostics`

## Tarea 3 — MetadataService: búsqueda de podcasts (Requisito 3)

- [x] 3.1 Añadir `_search_spotify_metadata()` a `MetadataService`:
  - Usa `get_spotify_token()` de `spotify_auth`
  - `GET https://api.spotify.com/v1/search?type=show&q={title}&limit=5`
  - Parsea a `MetadataCandidate` (title, publisher→creator, description, images[0].url, genres=[])
- [x] 3.2 Actualizar `search()` para enrutar `media_type="podcast"` al nuevo método
- [x] 3.3 Verificar con `getDiagnostics`

## Tarea 4 — ImageService: imágenes de podcasts (Requisito 4)

- [x] 4.1 Añadir `_search_spotify_image()` a `ImageService`:
  - Usa `get_spotify_token()` de `spotify_auth`
  - `GET https://api.spotify.com/v1/search?type=show&q={title}&limit=1`
  - Retorna `images[0].url` o None
- [x] 4.2 Actualizar `_search_image_url()` para enrutar `media_type="podcast"` al nuevo método
- [x] 4.3 Verificar con `getDiagnostics`

### Checkpoint 1 — Backend funcional

Verificar que:
- `MediaType.podcast` existe y es aceptado por los endpoints
- `MetadataService.search("serial", "podcast")` retorna candidatos (con Spotify credentials)
- `ImageService.fetch_image("serial", "podcast")` retorna una URL de Spotify
- CRUD completo funciona con `media_type=podcast`

## Tarea 5 — Frontend: soporte visual para podcasts (Requisito 6)

- [x] 5.1 Añadir CSS custom properties en `App.vue`:
  - `--color-type-podcast`, `--color-type-podcast-bg`, `--color-type-podcast-text`
- [x] 5.2 Actualizar `MediaCard.vue`: label "Podcast" + borde `.type-podcast`
- [x] 5.3 Actualizar `FilterBar.vue`: opción "Podcast" en el select de tipo
- [x] 5.4 Actualizar `MediaForm.vue`: opción "Podcast" en el select de tipo
- [x] 5.5 Actualizar `ExploreCard.vue`: label "Podcast" en el mapa de tipos
- [x] 5.6 Verificar con `getDiagnostics` en todos los archivos modificados

### Checkpoint 2 — Feature completa end-to-end

Verificar que:
- Se puede crear un podcast desde el formulario
- El autofill de metadatos funciona (busca en Spotify)
- La imagen se asigna correctamente (URL externa de Spotify)
- El filtro por tipo "Podcast" funciona en el catálogo
- Las estadísticas incluyen podcasts
- Se puede recomendar un podcast a un amigo

## Tarea 6 — Seed script (Requisito 7)

- [x] 6.1 Añadir `_fetch_spotify_podcasts()` a `seed_explore.py`
- [x] 6.2 Integrar en `main()` junto con movies, series y books

## Tarea 7 — Tests (Requisitos 8, 9)

- [ ]* 7.1 Property test P1: CRUD de podcast funciona igual que otros tipos
- [ ]* 7.2 Property test P5: resiliencia ante fallos de Spotify API
- [ ]* 7.3 Unit test: `get_spotify_token()` cachea y renueva correctamente
- [ ]* 7.4 Unit test: `_search_spotify_metadata()` parsea resultados correctamente
- [ ]* 7.5 Unit test: `_search_spotify_image()` retorna URL o None

> `*` = tests opcionales, implementar si hay tiempo.

### Checkpoint 3 — Todo verde

- Todos los tests existentes siguen pasando
- Los nuevos tests (si se implementaron) pasan
- `ruff check` limpio en todos los archivos modificados
