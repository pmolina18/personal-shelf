# Plan de Implementación: Media Metadata Autofill

## Resumen

Implementación incremental del autocompletado de metadatos: primero el servicio `MetadataService` que consulta TMDB y Open Library, luego el schema `MetadataCandidate`, el endpoint de búsqueda, la integración en los flujos de creación y actualización, y finalmente el dropdown de sugerencias en el frontend. Los tests de propiedad con Hypothesis validan las 6 propiedades de correctitud del diseño.

## Tareas

- [x] 1. Implementar MetadataService y schema MetadataCandidate
  - [x] 1.1 Crear el schema `MetadataCandidate` en `backend/schemas/media.py`
    - Añadir clase Pydantic `MetadataCandidate` con campos: `title` (str, obligatorio), `year` (int | None), `creator` (str | None), `description` (str | None), `image_url` (str | None)
    - _Requisitos: 6.1, 6.2_

  - [x] 1.2 Crear `backend/services/metadata_service.py` con la clase `MetadataService`
    - Implementar método `search(title, media_type)` que enruta a TMDB (movie/series) u Open Library (book)
    - Implementar `_search_tmdb_metadata(title, tmdb_type)`: busca en `/search/movie` o `/search/tv`, extrae título, año, creador (director vía `/movie/{id}/credits` para movies, `created_by` para series), descripción (`overview`) e `image_url` (poster)
    - Implementar `_search_open_library_metadata(title)`: busca en `/search.json`, extrae título, año (`first_publish_year`), autor (`author_name[0]`), descripción (`subject[0]`) e `image_url` (cover)
    - Limitar resultados a máximo 5 candidatos
    - Usar `httpx.AsyncClient(timeout=10.0)` consistente con `ImageService`
    - Si `TMDB_API_KEY` está vacío, omitir TMDB y devolver `[]`
    - Capturar todos los errores (HTTP 4xx/5xx, timeout, conexión) con `try/except`, loguear con `logger.exception()` y devolver `[]`
    - _Requisitos: 1.1, 1.2, 1.3, 2.1, 2.2, 3.2, 3.4, 8.1, 8.2, 8.3_

  - [ ]* 1.3 Escribir test de propiedad para transformación TMDB
    - **Propiedad 1: Transformación TMDB preserva campos**
    - Generar dicts con estructura TMDB (title/name, release_date/first_air_date, overview, poster_path) con campos opcionales usando Hypothesis
    - Verificar que los campos se extraen correctamente y que los ausentes se mapean a `None`
    - **Valida: Requisitos 1.1, 1.2**

  - [ ]* 1.4 Escribir test de propiedad para transformación Open Library
    - **Propiedad 2: Transformación Open Library preserva campos**
    - Generar dicts con estructura Open Library (title, first_publish_year, author_name, subject, cover_i) con campos opcionales usando Hypothesis
    - Verificar que los campos se extraen correctamente y que los ausentes se mapean a `None`
    - **Valida: Requisitos 2.1, 2.2**

  - [ ]* 1.5 Escribir test de propiedad para invariante de máximo 5 candidatos
    - **Propiedad 3: Invariante de máximo 5 candidatos**
    - Generar listas de 0 a 20 resultados mock y verificar que `len(result) <= 5` siempre
    - **Valida: Requisito 3.2**

  - [ ]* 1.6 Escribir test de propiedad para resiliencia ante errores
    - **Propiedad 6: Resiliencia ante errores de API externa**
    - Generar diferentes tipos de excepciones (`httpx.TimeoutException`, `httpx.ConnectError`, `httpx.HTTPStatusError`) y verificar que siempre devuelve `[]` sin propagar excepciones
    - **Valida: Requisitos 8.1, 8.2, 8.3**

- [x] 2. Checkpoint — Verificar MetadataService
  - Asegurar que todos los tests pasan, preguntar al usuario si surgen dudas.

- [-] 3. Implementar endpoint de búsqueda y integración en
 creación
  - [x] 3.1 Añadir endpoint `GET /api/media/metadata-search` en `backend/routers/media.py`
    - Registrar el endpoint antes de las rutas con `{media_id}` para evitar conflictos de path matching
    - Aceptar parámetros `title` (obligatorio, min_length=1) y `media_type` (obligatorio, enum MediaType)
    - Devolver `list[MetadataCandidate]` con máximo 5 resultados
    - Devolver HTTP 400 con mensaje descriptivo si `title` está vacío
    - Requiere autenticación (`get_current_user`)
    - Instanciar `MetadataService` a nivel de módulo como `_metadata_service`
    - _Requisitos: 3.1, 3.2, 3.3_

  - [x] 3.2 Integrar autocompletado en `POST /api/media` (create_media)
    - Antes de llamar a `_media_service.create()`, verificar si `year`, `creator` o `notes` son `None`
    - Si hay campos vacíos, invocar `_metadata_service.search(title, media_type)` y rellenar con el primer candidato
    - Preservar siempre los valores proporcionados por el usuario (no sobreescribir)
    - Si `MetadataService` no encuentra resultados o falla, crear el item sin metadatos
    - _Requisitos: 4.1, 4.2, 4.3_

  - [ ]* 3.3 Escribir test de propiedad para autocompletado en creación
    - **Propiedad 4: Autocompletado en creación preserva valores del usuario**
    - Generar `MediaCreate` con combinaciones aleatorias de campos None/proporcionados + mock de `MetadataService`
    - Verificar que los campos del usuario permanecen intactos y solo los `None` se rellenan
    - **Valida: Requisitos 4.1, 4.2, 4.3**

- [x] 4. Integrar autocompletado en actualización
  - [x] 4.1 Integrar re-obtención de metadatos en `PUT /api/media/{id}` (update_media)
    - Detectar si `title` o `media_type` cambiaron en el payload de actualización
    - Si cambiaron, invocar `_metadata_service.search()` con título y tipo efectivos
    - Rellenar `year`, `creator` y `notes` con el primer candidato solo si no fueron proporcionados explícitamente en la petición
    - Si no cambiaron `title` ni `media_type`, omitir la búsqueda de metadatos
    - _Requisitos: 5.1, 5.2_

  - [ ]* 4.2 Escribir test de propiedad para preservación en update
    - **Propiedad 5: Re-obtención en update preserva valores proporcionados**
    - Generar `MediaUpdate` con title/media_type + campos opcionales + mock de `MetadataService`
    - Verificar que los campos explícitos permanecen intactos y solo los no-incluidos se actualizan
    - **Valida: Requisitos 5.1, 5.2**

- [x] 5. Checkpoint — Verificar backend completo
  - Asegurar que todos los tests pasan, preguntar al usuario si surgen dudas.

- [x] 6. Implementar sugerencias de metadatos en el frontend
  - [x] 6.1 Añadir función `searchMetadata` en `frontend/src/api/media.js`
    - Implementar `searchMetadata(title, mediaType)` que llama a `GET /api/media/metadata-search` con query params
    - Seguir el patrón existente de la función `request()` del módulo
    - _Requisitos: 3.1, 7.1_

  - [x] 6.2 Añadir dropdown de sugerencias en `frontend/src/components/MediaForm.vue`
    - Añadir refs para `suggestions` (array) y `showSuggestions` (boolean)
    - Implementar debounce de 500ms con `setTimeout`/`clearTimeout` al cambiar `form.title` o `form.media_type`
    - Cuando ambos campos tienen valor, llamar a `searchMetadata(title, media_type)`
    - Mostrar lista desplegable (`<ul>` con `role="listbox"`) debajo del campo de título con título, año y creador de cada candidato
    - Al seleccionar un candidato (`@click`), rellenar `form.year`, `form.creator` y `form.notes` con los valores del candidato
    - Ocultar la lista si no hay resultados o hay error (sin mostrar mensaje de error)
    - Permitir al usuario editar libremente los campos después de seleccionar
    - Seguir las convenciones de accesibilidad: `role="listbox"`, `role="option"`, `aria-label`
    - _Requisitos: 7.1, 7.2, 7.3, 7.4, 7.5_

  - [ ]* 6.3 Escribir tests unitarios para el frontend
    - Test: debounce de 500ms en MediaForm al cambiar título/tipo
    - Test: selección de candidato rellena campos year, creator, notes
    - Test: lista vacía oculta dropdown sin error
    - _Requisitos: 7.1, 7.2, 7.3, 7.5_

- [x] 7. Checkpoint final — Verificar integración completa
  - Asegurar que todos los tests pasan, preguntar al usuario si surgen dudas.

## Notas

- Las tareas marcadas con `*` son opcionales y pueden omitirse para un MVP más rápido
- Cada tarea referencia requisitos específicos para trazabilidad
- Los checkpoints aseguran validación incremental
- Los tests de propiedad validan las 6 propiedades de correctitud del diseño usando Hypothesis
- `MetadataService` sigue el mismo patrón que `ImageService`: servicio async puro sin dependencia de DB
