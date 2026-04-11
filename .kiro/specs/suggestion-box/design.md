# Diseño — Buzón de Sugerencias (IDEA-2)

## 1. Arquitectura general

```
┌──────────────────┐     ┌──────────────────┐     ┌────────────┐     ┌────────────┐
│  SuggestionsView │────▶│  POST/GET         │────▶│ Suggestion │────▶│ PostgreSQL │
│  (Vue 3)         │     │  /api/suggestions │     │ Service    │     │ suggestions│
└──────────────────┘     └──────────────────┘     └─────┬──────┘     └────────────┘
                                                        │
                                                        ▼
                                                  ┌────────────┐
                                                  │ GitHub API  │
                                                  │ (create     │
                                                  │  issue)     │
                                                  └────────────┘
```

El flujo es: usuario envía sugerencia → router valida y delega → service persiste en BD → service llama a GitHubService para crear issue → devuelve respuesta con URL de la issue.

---

## 2. Modelo de datos

### Tabla `suggestions`

```sql
CREATE TABLE suggestions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    type VARCHAR(20) NOT NULL,  -- 'feature' o 'bug'
    github_issue_url VARCHAR(500),
    github_issue_number INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX ix_suggestions_user_id ON suggestions(user_id);
CREATE INDEX ix_suggestions_created_at ON suggestions(created_at DESC);
```

No se necesita `updated_at` porque las sugerencias son inmutables para los usuarios.

### Relación con User

```
User (1) ──── (N) Suggestion
```

La relación es unidireccional: `Suggestion.author` → `User`. No se añade relationship inversa en User para no cargar el modelo con relaciones que no se usan en el flujo principal.

---

## 3. Interfaces de componentes

### Backend

#### `backend/models/suggestion.py`

```python
class Suggestion(Base):
    __tablename__ = "suggestions"
    id: Mapped[int]           # PK autoincrement
    user_id: Mapped[int]      # FK → users.id, CASCADE
    title: Mapped[str]        # VARCHAR(255)
    description: Mapped[str]  # TEXT
    type: Mapped[str]         # VARCHAR(20): "feature" | "bug"
    github_issue_url: Mapped[str | None]    # VARCHAR(500)
    github_issue_number: Mapped[int | None] # INTEGER
    created_at: Mapped[datetime]            # server_default=func.now()
    author: Mapped["User"]    # relationship, lazy="selectin"
```

#### `backend/schemas/suggestion.py`

```python
class SuggestionType(str, Enum):
    feature = "feature"
    bug = "bug"

class SuggestionCreate(BaseModel):
    title: str          # Field(..., min_length=1, max_length=255)
    description: str    # Field(..., min_length=1, max_length=2000)
    type: SuggestionType

class SuggestionResponse(BaseModel):
    id: int
    user_id: int
    username: str
    title: str
    description: str
    type: SuggestionType
    github_issue_url: str | None
    github_issue_number: int | None
    created_at: datetime

class SuggestionList(BaseModel):
    items: list[SuggestionResponse]
    total: int
    page: int
    size: int
```

#### `backend/services/suggestion_service.py`

```python
class SuggestionService:
    async def create_suggestion(session, user_id, data) -> SuggestionResponse
    async def list_suggestions(session, page, size) -> SuggestionList
    async def list_my_suggestions(session, user_id, page, size) -> SuggestionList
```

#### `backend/services/github_service.py` (extensión)

```python
# Nuevo método en GitHubService:
async def create_issue(self, title, body, labels) -> dict | None
    # Retorna {"number": int, "html_url": str} o None si falla/no configurado
```

#### `backend/routers/suggestions.py`

```
POST /api/suggestions       → create_suggestion (201)
GET  /api/suggestions       → list_suggestions
GET  /api/suggestions/mine  → list_my_suggestions
```

### Frontend

#### `frontend/src/api/suggestions.js`

```javascript
export function createSuggestion(body)           // POST /api/suggestions
export function listSuggestions(params)           // GET /api/suggestions
export function listMySuggestions(params)         // GET /api/suggestions/mine
```

#### `frontend/src/composables/useSuggestions.js`

```javascript
export function useSuggestions() {
  // refs: suggestions, mySuggestions, loading, error, page, totalPages, myPage, myTotalPages
  // methods: fetchAll(page), fetchMine(page), submit(data)
}
```

#### `frontend/src/views/SuggestionsView.vue`

- Dos pestañas: "Todas" / "Mis sugerencias"
- Formulario inline para nueva sugerencia (título, descripción, tipo dropdown)
- Lista de sugerencias con: tipo badge, título, descripción truncada, autor, fecha, enlace a GitHub issue
- Paginación (componente `Pagination` existente)

---

## 4. Flujo de creación de sugerencia

```
Usuario                    Frontend                   Backend                    GitHub
  │                          │                          │                          │
  ├─ Rellena formulario ────▶│                          │                          │
  │                          ├─ POST /api/suggestions ─▶│                          │
  │                          │                          ├─ Valida schema            │
  │                          │                          ├─ INSERT suggestions       │
  │                          │                          ├─ create_issue() ─────────▶│
  │                          │                          │◀─ {number, html_url} ─────┤
  │                          │                          ├─ UPDATE github_issue_*    │
  │                          │◀─ SuggestionResponse ────┤                          │
  │◀─ Muestra en lista ──────┤                          │                          │
```

Si GitHub falla o no está configurado, el flujo continúa sin la issue (campos `github_issue_*` quedan null).

---

## 5. Manejo de errores

| Escenario | HTTP Status | Comportamiento |
|-----------|-------------|----------------|
| Título vacío o >255 chars | 422 | Validación Pydantic automática |
| Descripción vacía o >2000 chars | 422 | Validación Pydantic automática |
| Tipo inválido (no feature/bug) | 422 | Validación Pydantic automática |
| Usuario no autenticado | 401 | Guard existente (`get_current_user`) |
| GitHub API falla | — | Sugerencia se crea sin issue, log warning |
| GitHub no configurado | — | Sugerencia se crea sin issue, log warning |
| Error de BD | 500 | Error genérico |

---

## 6. Propiedades de correctitud

| # | Propiedad | Estrategia Hypothesis |
|---|-----------|----------------------|
| P1 | Persistencia | `@given` título (1-255 chars printable), descripción (1-2000 chars printable), tipo (sampled_from SuggestionType) → create devuelve todos los campos correctos |
| P2 | Paginación | Crear N sugerencias (1-50), listar con page/size → total correcto, items.length ≤ size |
| P3 | Filtrado por usuario | Crear sugerencias para 2+ usuarios → list_my_suggestions devuelve solo las del usuario indicado |
| P4 | Orden cronológico | Crear N sugerencias → listar → created_at[i] >= created_at[i+1] para todo i |

Todas las propiedades usan el patrón sync `def test_*` + `asyncio.run()` + `_fresh_session()` (SQLite in-memory).

---

## 7. Estrategia de testing

- **Property tests**: 4 propiedades en `tests/test_property_suggestions.py` con `@settings(max_examples=100)`.
- **Router tests**: `tests/test_suggestions_router.py` con `httpx.AsyncClient` + `ASGITransport` + `app.dependency_overrides`.
- **GitHub integration**: Mock de `GitHubService.create_issue` con `unittest.mock.patch` en los tests de servicio y router.

---

## 8. Archivos a crear/modificar

### Crear
- `backend/models/suggestion.py`
- `backend/schemas/suggestion.py`
- `backend/services/suggestion_service.py`
- `backend/routers/suggestions.py`
- `backend/migrations/versions/004_add_suggestions_table.py`
- `frontend/src/api/suggestions.js`
- `frontend/src/composables/useSuggestions.js`
- `frontend/src/views/SuggestionsView.vue`
- `tests/test_property_suggestions.py`
- `tests/test_suggestions_router.py`

### Modificar
- `backend/services/github_service.py` — añadir método `create_issue()`
- `backend/main.py` — registrar `suggestions_router`
- `backend/migrations/env.py` — importar modelo `Suggestion`
- `frontend/src/router/index.js` — añadir ruta `/suggestions`
- `frontend/src/App.vue` — añadir entrada en sidebar
