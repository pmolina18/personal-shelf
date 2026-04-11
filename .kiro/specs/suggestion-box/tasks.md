# Tareas — Buzón de Sugerencias (IDEA-2)

> **Estado**: Tareas 1-5 (backend) y 8-9 (frontend) COMPLETADAS. Faltan: tests opcionales (6, 7) y migración local (10).

## Tarea 1 — Modelo + Migración (Requisitos 1, 2)

- [x] 1.1 Crear `backend/models/suggestion.py` con el modelo `Suggestion` (id, user_id FK, title, description, type, github_issue_url, github_issue_number, created_at, relationship author → User con lazy="selectin").
- [x] 1.2 Importar `Suggestion` en `backend/migrations/env.py` para que Alembic lo registre en `Base.metadata`.
- [x] 1.3 Crear migración manual `backend/migrations/versions/004_add_suggestions_table.py` con CREATE TABLE, FK, índices (user_id, created_at DESC) y downgrade con DROP TABLE.

---

## Tarea 2 — Schemas Pydantic (Requisito 3)

- [x] 2.1 Crear `backend/schemas/suggestion.py` con `SuggestionType` (enum), `SuggestionCreate`, `SuggestionResponse`, `SuggestionList`.

---

## Tarea 3 — GitHubService: método `create_issue` (Requisito 5)

- [x] 3.1 Añadir método `async def create_issue(self, title: str, body: str, labels: list[str]) -> dict | None` a `GitHubService`. Usa `POST /repos/{repo}/issues` de la API de GitHub. Retorna `{"number": int, "html_url": str}` en éxito, `None` si no configurado o falla (log warning/error).

---

## Tarea 4 — SuggestionService (Requisito 4)

- [x] 4.1 Crear `backend/services/suggestion_service.py` con `SuggestionService`:
  - `create_suggestion(session, user_id, data)` — INSERT + join User para username + llama a GitHubService.create_issue() + UPDATE github_issue_* si éxito.
  - `list_suggestions(session, page, size)` — SELECT con join User, ORDER BY created_at DESC, paginado.
  - `list_my_suggestions(session, user_id, page, size)` — igual pero filtrado por user_id.

---

## Tarea 5 — Router REST (Requisito 6)

- [x] 5.1 Crear `backend/routers/suggestions.py` con:
  - `POST /api/suggestions` (201) — `get_current_user` + `SuggestionCreate` → `SuggestionResponse`.
  - `GET /api/suggestions` — paginado → `SuggestionList`.
  - `GET /api/suggestions/mine` — paginado, filtrado por user → `SuggestionList`.
- [x] 5.2 Registrar el router en `backend/main.py` (`app.include_router(suggestions_router)`).

---

## Checkpoint 1 — Backend funcional

Verificar: `python -m pytest tests/test_suggestions_router.py -v` pasa. Los endpoints responden correctamente con datos de prueba.

---

## Tarea 6 — Property tests (Propiedades P1-P4)

- [ ]* 6.1 Crear `tests/test_property_suggestions.py` con las 4 propiedades:
  - P1: Persistencia de sugerencia (título, descripción, tipo válidos → campos correctos).
  - P2: Paginación (N sugerencias → page/size correcto).
  - P3: Filtrado por usuario (multi-user → solo las del usuario indicado).
  - P4: Orden cronológico (created_at DESC).
  Patrón: sync def + asyncio.run() + _fresh_session() (SQLite in-memory). Mock de GitHubService.create_issue.

---

## Tarea 7 — Router tests

- [ ]* 7.1 Crear `tests/test_suggestions_router.py` con tests de los 3 endpoints:
  - POST crea sugerencia y devuelve 201.
  - GET lista paginada.
  - GET /mine filtra por usuario.
  - POST sin auth devuelve 401.
  Patrón: httpx.AsyncClient + ASGITransport + dependency_overrides.

---

## Checkpoint 2 — Backend + tests

Verificar: `python -m pytest tests/test_property_suggestions.py tests/test_suggestions_router.py -v` pasa.

---

## Tarea 8 — Frontend: API client + composable (Requisitos 7, 8)

- [x] 8.1 Crear `frontend/src/api/suggestions.js` con `createSuggestion`, `listSuggestions`, `listMySuggestions`. Patrón request() con Bearer token.
- [x] 8.2 Crear `frontend/src/composables/useSuggestions.js` con refs independientes y métodos `fetchAll`, `fetchMine`, `submit`.

---

## Tarea 9 — Frontend: vista + navegación (Requisitos 9, 10, 11)

- [x] 9.1 Crear `frontend/src/views/SuggestionsView.vue` con:
  - Dos pestañas (Todas / Mis sugerencias).
  - Formulario inline para nueva sugerencia (título, descripción, tipo select).
  - Lista de sugerencias con badge de tipo, título, descripción, autor, fecha, enlace GitHub.
  - Paginación con componente `Pagination` existente.
  - Estados: loading, error, empty, content.
- [x] 9.2 Añadir ruta `/suggestions` en `frontend/src/router/index.js` (lazy import, protegida por guard existente).
- [x] 9.3 Añadir entrada "Suggestions" en sidebar de `frontend/src/App.vue` con icono SVG inline (estilo Lucide, lightbulb o message-square).

---

## Checkpoint 3 — Feature completa

Verificar: la app funciona end-to-end. Crear sugerencia desde la UI → aparece en la lista → issue creada en GitHub (si configurado).

---

## Tarea 10 — Migración local

- [x] 10.1 Ejecutar `alembic upgrade head` desde `backend/` para aplicar la migración a la BD local.
