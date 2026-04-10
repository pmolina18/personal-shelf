# Documento de Diseño — Explore Catalog

## 1. Visión General de la Arquitectura

La funcionalidad Explore se implementa como una capa de solo lectura sobre la infraestructura existente de `MediaItem`, `Recommendation` y `friendships`. No requiere nuevos modelos de base de datos ni migraciones Alembic.

```
┌──────────────┐     ┌──────────────────┐     ┌────────────────┐
│ ExploreView  │────▶│ GET /api/explore  │────▶│ ExploreService │
│ (Vue 3)      │     │ (explore router)  │     │                │
│              │     │                   │     │ - deduplicación│
│ ExploreCard  │     │ Params:           │     │ - señales soc. │
│ useExplore   │     │  media_type       │     │ - filtrado     │
│              │     │  search           │     │ - ordenación   │
└──────────────┘     │  sort             │     │ - paginación   │
                     │  page, size       │     └────────────────┘
                     └──────────────────┘              │
                                                       ▼
                                              ┌────────────────┐
                                              │  media_items    │
                                              │  friendships    │
                                              │  recommendations│
                                              └────────────────┘
```

## 2. Componentes del Sistema

### 2.1 Backend

| Componente | Archivo | Responsabilidad |
|---|---|---|
| ExploreService | `backend/services/explore_service.py` | Query global, deduplicación, señales sociales, filtrado, ordenación, paginación |
| Explore Router | `backend/routers/explore.py` | Endpoint HTTP, validación de parámetros, inyección de dependencias |
| Explore Schemas | `backend/schemas/explore.py` | Schemas Pydantic para request/response del explore |

### 2.2 Frontend

| Componente | Archivo | Responsabilidad |
|---|---|---|
| ExploreView | `frontend/src/views/ExploreView.vue` | Vista principal con filtros, búsqueda, ordenación, grid y paginación |
| ExploreCard | `frontend/src/components/ExploreCard.vue` | Tarjeta de item con señales sociales |
| useExplore | `frontend/src/composables/useExplore.js` | Estado reactivo, llamadas API, gestión de filtros |
| API client | `frontend/src/api/media.js` | Función `listExplore(params)` |

## 3. Modelo de Datos

No se crean nuevos modelos. Se reutilizan las tablas existentes:

- `media_items` — fuente de items globales (todos los usuarios)
- `friendships` — para calcular `friends_have` (amigos que poseen un item)
- `recommendations` — para calcular `friends_recommended` (amigos que recomendaron un item)

### 3.1 Schema de Respuesta: ExploreItem

```python
class ExploreItem(BaseModel):
    title: str
    media_type: str
    year: int | None
    creator: str | None
    image_url: str | None
    friends_have: int      # amigos del usuario que poseen este título+tipo
    friends_recommended: int  # amigos que le recomendaron este título+tipo
```

### 3.2 Schema de Respuesta Paginada: ExploreResult

```python
class ExploreResult(BaseModel):
    items: list[ExploreItem]
    total: int
    page: int
    size: int
    pages: int
```

## 4. Interfaces de los Componentes

### 4.1 ExploreService

```python
class ExploreService:
    async def list_global(
        self,
        session: AsyncSession,
        user_id: int,
        media_type: str | None = None,
        search: str | None = None,
        sort: str = "title_asc",
        page: int = 1,
        size: int = 20,
    ) -> ExploreResult:
        """Devuelve el catálogo global deduplicado con señales sociales."""
```

### 4.2 Explore Router

```python
@router.get("/api/explore", response_model=ExploreResult)
async def list_explore(
    media_type: MediaType | None = Query(None),
    search: str | None = Query(None),
    sort: str = Query("title_asc"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> ExploreResult:
```

### 4.3 API Client (frontend)

```javascript
export function listExplore(params = {}) {
  // params: { media_type, search, sort, page, size }
  const query = new URLSearchParams()
  // ... build query string
  return request(`/explore${qs ? `?${qs}` : ''}`)
}
```

## 5. Estrategia de Deduplicación

La deduplicación se realiza en SQL usando `GROUP BY LOWER(title), media_type`:

1. Agrupar todos los `media_items` por `(LOWER(title), media_type)`
2. Para cada grupo, seleccionar un representante priorizando items con `image_path IS NOT NULL`
3. Usar `FIRST_VALUE` o subconsulta con `ORDER BY (image_path IS NOT NULL) DESC, id ASC` para elegir el representante

### Query conceptual (simplificado)

```sql
-- Paso 1: Items deduplicados con representante
WITH deduped AS (
    SELECT DISTINCT ON (LOWER(title), media_type)
        title, media_type, year, creator, image_path
    FROM media_items
    ORDER BY LOWER(title), media_type,
             (image_path IS NOT NULL) DESC, id ASC
)
SELECT d.*, 
       COALESCE(fh.cnt, 0) AS friends_have,
       COALESCE(fr.cnt, 0) AS friends_recommended
FROM deduped d
LEFT JOIN (...) fh ON ...  -- conteo de amigos que lo tienen
LEFT JOIN (...) fr ON ...  -- conteo de amigos que lo recomendaron
```

### Implementación en SQLAlchemy

Se usará una combinación de:
- `func.lower(MediaItem.title)` para normalización case-insensitive
- Subconsultas con `func.count()` y `distinct()` para señales sociales
- `DISTINCT ON` (PostgreSQL) o subconsulta con `ROW_NUMBER()` para seleccionar representante

## 6. Cálculo de Señales Sociales

### 6.1 friends_have

Cantidad de amigos del usuario actual que poseen un item con el mismo `LOWER(title)` y `media_type`:

```python
# Subconsulta: IDs de amigos
friend_ids = select(friendships.c.friend_id).where(
    friendships.c.user_id == user_id
)

# Conteo por (lower_title, media_type)
friends_have_q = (
    select(
        func.lower(MediaItem.title).label("lower_title"),
        MediaItem.media_type,
        func.count(func.distinct(MediaItem.user_id)).label("cnt"),
    )
    .where(MediaItem.user_id.in_(friend_ids))
    .group_by(func.lower(MediaItem.title), MediaItem.media_type)
)
```

### 6.2 friends_recommended

Cantidad de amigos que le han recomendado un item con el mismo `LOWER(title)` y `media_type`:

```python
friends_recommended_q = (
    select(
        func.lower(MediaItem.title).label("lower_title"),
        MediaItem.media_type,
        func.count(func.distinct(Recommendation.sender_id)).label("cnt"),
    )
    .select_from(Recommendation)
    .join(MediaItem, Recommendation.media_item_id == MediaItem.id)
    .where(
        Recommendation.receiver_id == user_id,
        Recommendation.sender_id.in_(friend_ids),
    )
    .group_by(func.lower(MediaItem.title), MediaItem.media_type)
)
```

## 7. Ordenación

| Valor de `sort` | Criterio SQL |
|---|---|
| `title_asc` (default) | `ORDER BY LOWER(title) ASC` |
| `title_desc` | `ORDER BY LOWER(title) DESC` |
| `friends` | `ORDER BY (friends_have + friends_recommended) DESC, LOWER(title) ASC` |

## 8. Propiedades de Correctitud

### Propiedad 1: Deduplicación correcta
Para cualquier conjunto de media items, el catálogo global no contiene dos items con el mismo `LOWER(title)` y `media_type`. Formalmente: `∀ i, j ∈ resultado: i ≠ j → (LOWER(i.title), i.media_type) ≠ (LOWER(j.title), j.media_type)`.

### Propiedad 2: Representante con imagen preferido
Cuando existen múltiples items con el mismo título normalizado y tipo, si al menos uno tiene `image_path` no nulo, el representante seleccionado tiene `image_url` no nulo.

### Propiedad 3: Filtrado por tipo correcto
Cuando se aplica un filtro `media_type`, todos los items del resultado tienen ese `media_type`. Formalmente: `∀ i ∈ resultado: i.media_type == filtro`.

### Propiedad 4: Búsqueda por título correcta
Cuando se aplica un filtro `search`, todos los items del resultado contienen el texto de búsqueda en su título (case-insensitive). Formalmente: `∀ i ∈ resultado: search.lower() in i.title.lower()`.

### Propiedad 5: Ordenación alfabética correcta
Cuando `sort=title_asc`, la lista está ordenada por `LOWER(title)` ascendente. Cuando `sort=title_desc`, descendente.

### Propiedad 6: Ordenación por amigos correcta
Cuando `sort=friends`, la lista está ordenada por `(friends_have + friends_recommended)` descendente, con desempate por título ascendente.

### Propiedad 7: Señales sociales no negativas
Para todo item en el resultado: `friends_have >= 0` y `friends_recommended >= 0`.

### Propiedad 8: Paginación consistente
El total reportado coincide con la cantidad real de items deduplicados que cumplen los filtros. `pages == ceil(total / size)`. La cantidad de items en la página es `min(size, total - (page-1)*size)`.

### Propiedad 9: Usuario sin amigos tiene señales a cero
Cuando el usuario no tiene amigos, todos los items tienen `friends_have == 0` y `friends_recommended == 0`.

### Propiedad 10: Autenticación requerida
El endpoint devuelve 401 cuando no se proporciona token de autenticación.

## 9. Manejo de Errores

| Escenario | Código HTTP | Detalle |
|---|---|---|
| Usuario no autenticado | 401 | "Not authenticated" |
| `media_type` inválido | 422 | Validación automática de FastAPI (enum) |
| `sort` inválido | 400 | "Invalid sort. Allowed: title_asc, title_desc, friends" |
| `page` < 1 o `size` fuera de rango | 422 | Validación automática de FastAPI (Query ge/le) |
| Error interno de BD | 500 | Error genérico (no exponer detalles) |

## 10. Estrategia de Testing

### 10.1 Property Tests (Hypothesis)
- Archivo: `tests/test_property_explore.py`
- Patrón: sync `def test_*` con `asyncio.run()` interno + `_fresh_session()` (SQLite in-memory)
- Propiedades 1-9 como tests individuales con `@settings(max_examples=100)`

### 10.2 Router Tests
- Archivo: `tests/test_explore_router.py`
- Patrón: `httpx.AsyncClient` + `ASGITransport` + `app.dependency_overrides[get_session]`
- Propiedad 10 (autenticación) + tests de integración HTTP

### 10.3 Frontend
- Composable `useExplore`: mock de API, verificar estado reactivo
- ExploreView: mount con stubs, verificar estados (loading, error, empty, data)
- ExploreCard: props → render correcto de señales sociales

## 11. Plan de Integración

1. Crear schemas (`backend/schemas/explore.py`)
2. Crear servicio (`backend/services/explore_service.py`)
3. Crear router (`backend/routers/explore.py`) y registrar en `main.py`
4. Crear función API frontend (`listExplore` en `media.js`)
5. Crear composable (`useExplore.js`)
6. Crear componente `ExploreCard.vue`
7. Crear vista `ExploreView.vue`
8. Añadir ruta `/explore` al router frontend
9. Añadir enlace "Explore" al sidebar en `App.vue`
10. Escribir property tests y router tests
