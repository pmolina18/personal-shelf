# Tareas de Implementación — Feed Unificado en Explore

## Resumen

Extender el catálogo Explore con indicadores de amigos activos (`friends_reading`), añadir ordenación por actividad, eliminar el enlace Feed de la sidebar, y redirigir `/feed` a `/explore`. Backend en Python (FastAPI), frontend en Vue 3 (Composition API).

## Tareas

- [x] 1. Extender schemas backend con FriendReading
  - [x] 1.1 Añadir clase `FriendReading(BaseModel)` con `user_id: int` y `username: str` en `backend/schemas/explore.py`
    - _Requisitos: 2.1_
  - [x] 1.2 Añadir campo `friends_reading: list[FriendReading] = Field(default_factory=list)` a `ExploreItem`
    - Mantener todos los campos existentes sin modificaciones
    - Serializar como lista vacía `[]` cuando no hay amigos activos
    - _Requisitos: 2.1, 2.2, 2.3_

- [x] 2. Implementar lógica de friends_reading en ExploreService
  - [x] 2.1 Añadir import de `User` y `FriendReading` en `backend/services/explore_service.py`
    - _Requisitos: 1.1, 1.2_
  - [x] 2.2 Construir `reading_map: dict[tuple[str, str], list[FriendReading]]` en `list_global()`
    - Query: SELECT LOWER(title), media_type, user_id, username FROM media_items JOIN users WHERE user_id IN (friend_ids) AND status='in_progress'
    - GROUP BY LOWER(title), media_type, user_id, username
    - Insertar después de `have_map` y `rec_map`
    - _Requisitos: 1.1, 1.2, 1.3, 1.4, 1.5_
  - [x] 2.3 Asignar `friends_reading=reading_map.get(key, [])` en el bucle de deduplicación
    - _Requisitos: 1.1, 1.3_
  - [x] 2.4 Añadir rama de ordenación `"activity"` en la sección de sort
    - Criterio primario: `-len(friends_reading)` (descendente)
    - Desempate 1: `-(friends_have + friends_recommended)` (descendente)
    - Desempate 2: `title.lower()` (ascendente)
    - _Requisitos: 4.1, 4.2, 4.3_
  - [x] 2.5 Añadir `"activity"` a `_VALID_SORTS` en `backend/routers/explore.py`
    - Actualizar mensaje de error 400 para incluir "activity" en la lista de valores permitidos
    - _Requisitos: 4.4_

- [x] 3. Checkpoint — Backend funcional
  - Verificar que `GET /api/explore?sort=activity` devuelve items con `friends_reading` poblado correctamente
  - Verificar que `GET /api/feed` sigue funcionando sin cambios (Requisito 7.1, 7.2)
  - Asegurar que todos los tests existentes pasan, preguntar al usuario si surgen dudas

- [x] 4. Indicador de actividad en ExploreCard (Frontend)
  - [x] 4.1 Añadir sección de indicadores de actividad en `frontend/src/components/ExploreCard.vue`
    - Template: `<div v-if="item.friends_reading && item.friends_reading.length > 0">` con icono 👀 y texto computed
    - Clase BEM: `.explore-card__activity`, `.explore-card__activity-icon`, `.explore-card__activity-text`
    - Atributo `aria-label` descriptivo en la sección de actividad
    - _Requisitos: 3.1, 3.6, 3.7, 8.2, 8.3_
  - [x] 4.2 Implementar computed `activityText` con formato de texto según número de amigos
    - 1 amigo: `"{username} lo está leyendo/viendo"`
    - 2 amigos: `"{u1} y {u2} lo están leyendo/viendo"`
    - 3+ amigos: `"{u1}, {u2} y N más lo están leyendo/viendo"`
    - Verbo: `"leyendo"` para `book`, `"viendo"` para `movie`/`series`
    - _Requisitos: 3.2, 3.3, 3.4, 3.5_
  - [x] 4.3 Aplicar estilo visual diferenciado cuando `friends_reading` no está vacío
    - Borde sutil con `var(--color-primary-light)` en la card
    - Estilos scoped con BEM: `.explore-card--active`
    - _Requisitos: 8.1_

- [x] 5. Opción de ordenación y navegación (Frontend)
  - [x] 5.1 Añadir `<option value="activity">Por actividad</option>` al select de ordenación en `frontend/src/views/ExploreView.vue`
    - _Requisitos: 4.4_
  - [x] 5.2 Reemplazar ruta `/feed` con redirect a `/explore` en `frontend/src/router/index.js`
    - Cambiar `{ path: '/feed', name: 'feed', component: FeedView }` por `{ path: '/feed', redirect: '/explore' }`
    - Eliminar import lazy de `FeedView`
    - _Requisitos: 5.3_
  - [x] 5.3 Eliminar el bloque `<router-link to="/feed">` de la sidebar en `frontend/src/App.vue`
    - Mantener el enlace "Explore" y todos los demás enlaces sin cambios
    - _Requisitos: 5.1, 5.2, 5.4_

- [x] 6. Checkpoint — Feature completa
  - Verificar funcionalidad existente de Explore: filtros, búsqueda, paginación, "Add to shelf", deduplicación, señales sociales (Requisitos 6.1–6.7)
  - Verificar indicadores de actividad visibles en ExploreCard cuando hay amigos activos
  - Verificar que `/feed` redirige a `/explore`
  - Verificar que el enlace Feed no aparece en la sidebar
  - Asegurar que todos los tests pasan, preguntar al usuario si surgen dudas

- [ ] 7. Property-based tests (Hypothesis)
  - [ ]* 7.1 Crear `tests/test_property_unified_explore.py` con helpers reutilizables
    - Helpers: `_fresh_session()`, `_create_user()`, `_create_media_item()`, `_create_friendship()`
    - Patrón: sync def test_* con `asyncio.run()` + `_fresh_session()` (SQLite in-memory)
    - `@settings(max_examples=100, deadline=None)`
    - _Requisitos: 9.1–9.5_
  - [ ]* 7.2 Propiedad 1: Correctitud de friends_reading
    - **Propiedad 1: Correctitud de friends_reading**
    - Cada entrada en `friends_reading` corresponde a un amigo confirmado con item `in_progress` coincidente por `(LOWER(title), media_type)`
    - Cada entrada tiene `user_id` (int) y `username` (str no vacío)
    - **Valida: Requisitos 1.1, 1.2, 1.3, 1.4, 1.5, 9.1**
  - [ ]* 7.3 Propiedad 2: Cota superior de friends_reading
    - **Propiedad 2: Cota superior de friends_reading**
    - `len(friends_reading) <= número total de amigos del usuario`
    - **Valida: Requisito 9.2**
  - [ ]* 7.4 Propiedad 3: Ordenación por actividad
    - **Propiedad 3: Ordenación por actividad**
    - Con `sort="activity"`, item N tiene `len(friends_reading) >= len(friends_reading)` del item N+1
    - Desempate por `friends_have + friends_recommended` desc, luego `LOWER(title)` asc
    - **Valida: Requisitos 4.1, 4.2, 4.3, 9.3**
  - [ ]* 7.5 Propiedad 4: Exclusión del propio usuario
    - **Propiedad 4: Exclusión del propio usuario**
    - `friends_reading` no contiene el `user_id` del usuario autenticado
    - **Valida: Requisito 9.4**
  - [ ]* 7.6 Propiedad 5: Unicidad en friends_reading
    - **Propiedad 5: Unicidad en friends_reading**
    - No existen dos entradas con el mismo `user_id` en `friends_reading` de un mismo item
    - **Valida: Requisito 9.5**

- [x] 8. Checkpoint final
  - Ejecutar `python -m pytest tests/ -v` — todos los tests (existentes + nuevos) deben pasar
  - Asegurar que todos los tests pasan, preguntar al usuario si surgen dudas

## Notas

- Las tareas marcadas con `*` son opcionales y pueden omitirse para un MVP más rápido
- Cada tarea referencia requisitos específicos para trazabilidad
- Los checkpoints aseguran validación incremental
- Los property tests validan propiedades universales de correctitud
- El endpoint `GET /api/feed` se mantiene sin cambios para compatibilidad (Requisito 7)
