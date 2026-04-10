# Tareas de Implementación — Explore Catalog

## Tarea 1: Schemas Pydantic para Explore
- [x] 1.1 Crear `backend/schemas/explore.py` con `ExploreItem` y `ExploreResult`
  - `ExploreItem`: title (str), media_type (str), year (int|None), creator (str|None), image_url (str|None), friends_have (int), friends_recommended (int)
  - `ExploreResult`: items (list[ExploreItem]), total (int), page (int), size (int), pages (int)
  - Requisitos: R1.3, R2.3, R7.1, R7.2

## Tarea 2: ExploreService — catálogo global con deduplicación y señales sociales
- [x] 2.1 Crear `backend/services/explore_service.py` con clase `ExploreService`
- [x] 2.2 Implementar método `list_global(session, user_id, media_type, search, sort, page, size) -> ExploreResult`
  - Deduplicación por `(LOWER(title), media_type)` con representante que prioriza image_path no nulo (R2.1, R2.2)
  - Cálculo de `friends_have`: COUNT DISTINCT de amigos que poseen items con mismo título+tipo (R7.1)
  - Cálculo de `friends_recommended`: COUNT DISTINCT de amigos que recomendaron items con mismo título+tipo (R7.2)
  - Filtrado por `media_type` cuando presente (R3.2)
  - Filtrado por `search` con ILIKE parcial en título (R4.2)
  - Ordenación: `title_asc` (default), `title_desc`, `friends` con desempate por título (R5, R6)
  - Paginación con total, pages, offset/limit (R1.2, R1.3)
  - Señales a 0 cuando usuario sin amigos (R6.4, R7.3)

## Tarea 3: Router y registro en main.py
- [x] 3.1 Crear `backend/routers/explore.py` con endpoint `GET /api/explore`
  - Parámetros: media_type (MediaType|None), search (str|None), sort (str, default "title_asc"), page (int, ge=1), size (int, ge=1, le=100)
  - Validar sort ∈ {title_asc, title_desc, friends}, devolver 400 si inválido
  - Inyectar `get_current_user` para autenticación (R1.4)
  - Requisitos: R1.1, R1.2, R1.4, R3.1, R3.4, R4.1, R5.1
- [x] 3.2 Registrar router en `backend/main.py` con `app.include_router(explore_router)`

### Checkpoint 1: Backend funcional
Verificar que `GET /api/explore` devuelve items deduplicados con señales sociales, filtros y ordenación correctos.

## Tarea 4: Property tests del servicio
- [ ]* 4.1 Crear `tests/test_property_explore.py` con Hypothesis
  - Propiedad 1: Deduplicación — no hay duplicados (LOWER(title), media_type) en resultado
  - Propiedad 2: Representante con imagen — si existe item con image_path, el representante lo tiene
  - Propiedad 3: Filtrado por tipo — todos los items del resultado tienen el media_type filtrado
  - Propiedad 4: Búsqueda por título — todos los items contienen el texto buscado (case-insensitive)
  - Propiedad 5: Ordenación alfabética — resultado ordenado por LOWER(title) asc/desc
  - Propiedad 6: Ordenación por amigos — resultado ordenado por suma de señales desc, desempate por título
  - Propiedad 7: Señales no negativas — friends_have >= 0 y friends_recommended >= 0
  - Propiedad 8: Paginación — total, pages, items count consistentes
  - Propiedad 9: Sin amigos → señales a cero
  - Patrón: sync def test_* con asyncio.run() + _fresh_session() (SQLite in-memory)
  - @settings(max_examples=100)
- [ ]* 4.2 Crear `tests/test_explore_router.py` con tests de integración HTTP
  - Propiedad 10: Autenticación requerida (401 sin token)
  - Test de integración: crear items de múltiples usuarios, verificar deduplicación en respuesta HTTP
  - Patrón: httpx.AsyncClient + ASGITransport + dependency_overrides

### Checkpoint 2: Backend con tests
Ejecutar `python -m pytest tests/test_property_explore.py tests/test_explore_router.py -v` — todos los tests pasan.

## Tarea 5: API client frontend
- [x] 5.1 Añadir función `listExplore(params)` en `frontend/src/api/media.js`
  - Parámetros: { media_type, search, sort, page, size }
  - Endpoint: `GET /explore` con query string

## Tarea 6: Composable useExplore
- [x] 6.1 Crear `frontend/src/composables/useExplore.js`
  - Estado: items, total, page, size, pages, loading, error, filters (media_type, search, sort)
  - Métodos: fetchExplore(), setFilters(), setPage(), setSort()
  - Patrón: refs independientes por invocación (sin estado compartido a nivel de módulo)

## Tarea 7: Componente ExploreCard
- [x] 7.1 Crear `frontend/src/components/ExploreCard.vue`
  - Props: item (ExploreItem)
  - Mostrar: título, tipo, año, creador, imagen (con placeholder por tipo)
  - Señales sociales: "N amigos lo tienen" y "N amigos te lo recomendaron" (solo si > 0)
  - Ocultar sección social si ambos son 0
  - Estilo consistente con MediaCard existente (grid card, scoped CSS, design tokens)
  - Requisitos: R9.1, R9.2, R9.3, R9.4, R9.5

## Tarea 8: Vista ExploreView y navegación
- [x] 8.1 Crear `frontend/src/views/ExploreView.vue`
  - Controles: filtro por tipo (select), búsqueda por título (input), ordenación (select con 3 opciones)
  - Grid de ExploreCard con Pagination existente
  - Estados: loading (role="status"), error (role="alert"), empty (mensaje sin resultados)
  - Requisitos: R8.1–R8.9
- [x] 8.2 Añadir ruta `/explore` en `frontend/src/router/index.js`
  - Lazy-loaded: `const ExploreView = () => import('../views/ExploreView.vue')`
  - Ruta protegida (sin meta.isAuth)
  - Requisito: R8.1
- [x] 8.3 Añadir enlace "Explore" en sidebar de `frontend/src/App.vue`
  - Ubicación: sección social (después de Feed, antes o después de Friends)
  - Icono SVG representativo (brújula o globo)
  - Etiqueta "Explore" con Transition fade-text
  - Atributo title="Explore" cuando collapsed
  - Requisitos: R10.1, R10.2, R10.3

### Checkpoint 3: Feature completa
Verificar en el navegador: navegar a /explore, ver items globales, filtrar por tipo, buscar por título, ordenar por amigos, paginación funcional, señales sociales visibles.
