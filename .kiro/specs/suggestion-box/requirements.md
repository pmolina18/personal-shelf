# Requisitos — Buzón de Sugerencias (IDEA-2)

## Descripción general

Permitir que los usuarios autenticados envíen sugerencias de nuevas funcionalidades o reportes de bugs desde la propia aplicación. Cada sugerencia se persiste en base de datos y automáticamente crea una issue en el repositorio de GitHub del proyecto, para que el propietario pueda priorizarlas y resolverlas.

## Glosario

| Término | Definición |
|---------|-----------|
| Sugerencia | Entrada creada por un usuario con título, descripción y tipo (feature o bug). |
| GitHub Issue | Issue creada automáticamente en el repositorio configurado en `GITHUB_REPO`. |
| GitHubService | Servicio existente (`backend/services/github_service.py`) que ya interactúa con la API de GitHub. |

---

## Requisitos funcionales

### Requisito 1 — Modelo de datos `Suggestion`

Crear un modelo SQLAlchemy `Suggestion` con los campos necesarios para persistir sugerencias.

**Criterios de aceptación (EARS):**
- CUANDO un usuario envía una sugerencia, ENTONCES se persiste en la tabla `suggestions` con: `id`, `user_id` (FK → users), `title` (VARCHAR 255, NOT NULL), `description` (TEXT, NOT NULL), `type` (VARCHAR 20: "feature" o "bug"), `github_issue_url` (VARCHAR 500, nullable), `github_issue_number` (INTEGER, nullable), `created_at` (TIMESTAMP, server_default now()).
- CUANDO se elimina un usuario, ENTONCES sus sugerencias se eliminan en cascada (ON DELETE CASCADE).

---

### Requisito 2 — Migración Alembic

Crear una migración Alembic para la tabla `suggestions`.

**Criterios de aceptación (EARS):**
- CUANDO se ejecuta `alembic upgrade head`, ENTONCES la tabla `suggestions` se crea con todas las columnas, FK e índices definidos en el Requisito 1.
- CUANDO se ejecuta `alembic downgrade -1`, ENTONCES la tabla `suggestions` se elimina.

---

### Requisito 3 — Schemas Pydantic

Definir los schemas de request/response para sugerencias.

**Criterios de aceptación (EARS):**
- `SuggestionType` — Enum con valores `feature` y `bug`.
- `SuggestionCreate` — `title` (str, 1-255 chars), `description` (str, 1-2000 chars), `type` (SuggestionType).
- `SuggestionResponse` — Todos los campos del modelo + `username` del autor.
- `SuggestionList` — Lista paginada con `items: list[SuggestionResponse]`, `total: int`, `page: int`, `size: int`.

---

### Requisito 4 — SuggestionService (capa de servicio)

Implementar la lógica de negocio para crear y listar sugerencias.

**Criterios de aceptación (EARS):**
- CUANDO se llama a `create_suggestion(session, user_id, data)`, ENTONCES se crea la sugerencia en BD y se devuelve el objeto creado con el username del autor.
- CUANDO se llama a `list_suggestions(session, page, size)`, ENTONCES se devuelven todas las sugerencias paginadas, ordenadas por `created_at` DESC, incluyendo el `username` de cada autor.
- CUANDO se llama a `list_my_suggestions(session, user_id, page, size)`, ENTONCES se devuelven solo las sugerencias del usuario indicado, paginadas y ordenadas por `created_at` DESC.

---

### Requisito 5 — Integración con GitHub Issues

Extender `GitHubService` para crear issues automáticamente al recibir una sugerencia.

**Criterios de aceptación (EARS):**
- CUANDO se crea una sugerencia y `GitHubService.is_configured` es True, ENTONCES se crea una issue en GitHub con: título = título de la sugerencia, body = descripción + metadata (tipo, usuario, fecha), labels = ["suggestion"] para features o ["bug"] para bugs.
- CUANDO la issue se crea exitosamente, ENTONCES se actualiza la sugerencia en BD con `github_issue_url` y `github_issue_number`.
- CUANDO `GitHubService.is_configured` es False (no hay token/repo), ENTONCES la sugerencia se crea igualmente en BD sin issue de GitHub, y se registra un warning en el log.
- CUANDO la API de GitHub falla, ENTONCES la sugerencia se crea igualmente en BD sin issue, se registra el error en el log, y se devuelve la sugerencia con `github_issue_url = null`.

---

### Requisito 6 — Router REST API

Exponer endpoints para crear y listar sugerencias.

**Criterios de aceptación (EARS):**
- `POST /api/suggestions` — Crea una sugerencia. Requiere autenticación. Body: `SuggestionCreate`. Response: `SuggestionResponse` (201).
- `GET /api/suggestions` — Lista todas las sugerencias (paginadas). Requiere autenticación. Query params: `page` (default 1), `size` (default 20). Response: `SuggestionList`.
- `GET /api/suggestions/mine` — Lista solo las sugerencias del usuario autenticado (paginadas). Requiere autenticación. Query params: `page`, `size`. Response: `SuggestionList`.

---

### Requisito 7 — Cliente API frontend

Crear el módulo `frontend/src/api/suggestions.js` con funciones para interactuar con los endpoints.

**Criterios de aceptación (EARS):**
- CUANDO se importa el módulo, ENTONCES expone: `createSuggestion(body)`, `listSuggestions(params)`, `listMySuggestions(params)`.
- CUANDO se llama a cualquier función, ENTONCES usa el patrón `request()` existente con autenticación Bearer.

---

### Requisito 8 — Composable `useSuggestions`

Crear `frontend/src/composables/useSuggestions.js` para gestionar el estado reactivo de sugerencias.

**Criterios de aceptación (EARS):**
- CUANDO se invoca `useSuggestions()`, ENTONCES devuelve refs independientes (no singleton): `suggestions`, `mySuggestions`, `loading`, `error`, `page`, `totalPages`.
- CUANDO se llama a `fetchAll(page)`, ENTONCES carga la lista global de sugerencias.
- CUANDO se llama a `fetchMine(page)`, ENTONCES carga solo las sugerencias del usuario.
- CUANDO se llama a `submit(data)`, ENTONCES crea la sugerencia y la añade al inicio de la lista local.

---

### Requisito 9 — Vista `SuggestionsView.vue`

Crear la vista principal del buzón de sugerencias.

**Criterios de aceptación (EARS):**
- CUANDO el usuario navega a `/suggestions`, ENTONCES ve dos pestañas: "Todas" (lista global) y "Mis sugerencias" (solo las suyas).
- CUANDO el usuario está en cualquier pestaña, ENTONCES ve un botón "Nueva sugerencia" que abre un formulario inline o modal.
- CUANDO el usuario envía el formulario con título, descripción y tipo (feature/bug), ENTONCES la sugerencia aparece en la lista y se muestra un mensaje de éxito.
- CUANDO una sugerencia tiene `github_issue_url`, ENTONCES se muestra un enlace/icono que abre la issue en una nueva pestaña.
- CUANDO la lista tiene más de 20 items, ENTONCES se muestra paginación.
- CUANDO hay un error al crear o cargar, ENTONCES se muestra un mensaje de error con `role="alert"`.

---

### Requisito 10 — Navegación en sidebar

Añadir entrada en el sidebar de `App.vue` para acceder al buzón de sugerencias.

**Criterios de aceptación (EARS):**
- CUANDO el sidebar está expandido, ENTONCES muestra un enlace "Suggestions" con icono SVG inline (estilo Lucide, consistente con los demás).
- CUANDO el sidebar está colapsado, ENTONCES muestra solo el icono con `title` tooltip.
- CUANDO el usuario hace click, ENTONCES navega a `/suggestions`.

---

### Requisito 11 — Ruta en Vue Router

Registrar la ruta `/suggestions` en el router.

**Criterios de aceptación (EARS):**
- CUANDO un usuario autenticado navega a `/suggestions`, ENTONCES se carga `SuggestionsView` (lazy import).
- CUANDO un usuario no autenticado navega a `/suggestions`, ENTONCES se redirige a `/login` (guard existente).

---

## Propiedades de correctitud (Hypothesis)

| # | Propiedad | Descripción |
|---|-----------|-------------|
| P1 | Persistencia de sugerencia | Para cualquier título válido (1-255 chars), descripción (1-2000 chars) y tipo (feature/bug), `create_suggestion` persiste la sugerencia y la devuelve con todos los campos correctos. |
| P2 | Paginación de sugerencias | Para cualquier conjunto de N sugerencias creadas, `list_suggestions(page, size)` devuelve el subconjunto correcto y `total` = N. |
| P3 | Filtrado por usuario | Para sugerencias de múltiples usuarios, `list_my_suggestions(user_id)` devuelve exactamente las del usuario indicado. |
| P4 | Orden cronológico | Las sugerencias se devuelven ordenadas por `created_at` DESC (la más reciente primero). |

---

## Fuera de alcance

- Edición o eliminación de sugerencias por parte de los usuarios.
- Votación o priorización de sugerencias dentro de la app.
- Sincronización bidireccional con GitHub (si se cierra la issue en GitHub, no se refleja en la app).
- Comentarios en sugerencias.
