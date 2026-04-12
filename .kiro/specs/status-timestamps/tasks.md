# Plan de Implementación: Status Timestamps

## Visión General

Esta feature completa la gestión de timestamps de estado en Personal Shelf. Actualmente `started_at` y `completed_at` ya existen pero la lógica es inconsistente (`started_at` solo se setea si es `None`, `completed_at` siempre se sobreescribe) y falta el campo `pending_at`. Los cambios son: añadir `pending_at` al modelo vía migración Alembic, unificar la lógica de `update_status` para que siempre sobreescriba el timestamp destino (incluido `started_at`), setear `pending_at` al crear un item, exponer `pending_at` en la API, y mostrar una mini-timeline visual en `MediaDetailView.vue`. Las tareas siguen un orden incremental: migración → modelo/schema → servicio → checkpoint → property tests → frontend → MCP → checkpoint final.

## Tareas

- [x] 1. Migración Alembic — añadir columna `pending_at` a `media_items`
  - [x] 1.1 Crear archivo de migración `backend/migrations/versions/006_add_pending_at.py` con `revision="006"` y `down_revision="005"`
    - `upgrade`: `op.add_column("media_items", sa.Column("pending_at", sa.DateTime(), nullable=True))`
    - `downgrade`: `op.drop_column("media_items", "pending_at")`
    - Los registros existentes quedan con `pending_at = NULL`
    - _Req 1 (CA3, CA4)_

  - [x] 1.2 Ejecutar `alembic upgrade head` contra la BD de desarrollo y verificar que la columna `pending_at` existe en `media_items`
    - Confirmar con `alembic current` que la revisión activa es `006`
    - _Req 1 (CA3)_

- [x] 2. Modelo + Schema + `_to_response` — añadir `pending_at`
  - [x] 2.1 Añadir campo `pending_at` al modelo `MediaItem` en `backend/models/media.py`
    - Añadir `pending_at: Mapped[datetime | None] = mapped_column(nullable=True)` después de `completed_at`
    - Actualizar el docstring de la clase para incluir `pending_at`
    - _Req 1 (CA1, CA2)_

  - [x] 2.2 Añadir campo `pending_at` al schema `MediaResponse` en `backend/schemas/media.py`
    - Añadir `pending_at: datetime | None` después de `completed_at`
    - Actualizar el docstring de la clase para incluir `pending_at`
    - _Req 4 (CA1, CA3)_

  - [x] 2.3 Añadir mapeo de `pending_at` en la función `_to_response` en `backend/services/media_service.py`
    - Añadir `pending_at=item.pending_at` al constructor de `MediaResponse`
    - Esto propaga `pending_at` a todos los endpoints que devuelven `MediaResponse` automáticamente
    - _Req 4 (CA2, CA4)_

- [x] 3. Servicio — setear `pending_at` en creación + unificar lógica de `update_status`
  - [x] 3.1 Modificar `MediaService.create` en `backend/services/media_service.py` para setear `pending_at = datetime.utcnow()` después de construir el objeto `MediaItem`
    - El item nace con `status="pending"`, así que `pending_at` refleja ese momento
    - `started_at` y `completed_at` permanecen `None` (comportamiento actual, sin cambios)
    - _Req 2 (CA1, CA2, CA3)_

  - [x] 3.2 Reescribir el bloque de timestamps en `MediaService.update_status` en `backend/services/media_service.py`
    - Añadir detección de no-op: si `item.status == status`, retornar `_to_response(item)` sin modificar nada ni hacer commit
    - Cambiar la asignación de `item.status = status` para que ocurra solo si el estado cambia
    - Reemplazar el bloque condicional actual por lógica unificada:
      - Si `status == "pending"` → `item.pending_at = now`
      - Si `status == "in_progress"` → `item.started_at = now` (siempre, eliminando la condición `if item.started_at is None`)
      - Si `status == "completed"` → `item.completed_at = now`
    - Solo se toca el timestamp del estado destino; los otros dos no se modifican
    - _Req 3 (CA1, CA2, CA3, CA4, CA5)_

- [x] 4. Checkpoint backend — verificar que la API devuelve `pending_at` correctamente
  - [x] 4.1 Arrancar el servidor de desarrollo (`python -m uvicorn backend.main:app --reload --port 8000`) y verificar manualmente:
    - `POST /api/media` devuelve `pending_at` no nulo en la respuesta
    - `GET /api/media/{id}` incluye `pending_at` en la respuesta
    - `PATCH /api/media/{id}/status` con cambio de estado actualiza el timestamp correcto y no toca los otros
    - `PATCH /api/media/{id}/status` con el mismo estado actual no modifica ningún timestamp (no-op)
    - _Req 1, Req 2, Req 3, Req 4_

  - [x] 4.2 Ejecutar los tests existentes (`pytest tests/`) y confirmar que no hay regresiones
    - Los property tests existentes de status/timestamps (Property 6 en `test_property_media.py`) deben seguir pasando
    - _Req 3_

- [ ] 5. *Property tests — 5 propiedades de correctitud (opcional)
  - [ ] 5.1 *Crear archivo `tests/test_property_status_timestamps.py` con helper `_fresh_session()` para SQLite in-memory aislado
    - Importar `MediaService`, `MediaCreate`, `MediaStatus`, `MediaResponse` y modelos necesarios
    - Patrón: `def test_*` con `asyncio.run()` interno (nunca combinar `@given` con `@pytest.mark.asyncio`)
    - `@settings(max_examples=100)` mínimo en cada propiedad
    - _Req 1-5_

  - [ ] 5.2 *Propiedad 1: Creación siempre setea `pending_at`
    - `# Feature: media-tracker, Property 1: Creación siempre setea pending_at`
    - Estrategia: `title` texto válido, `media_type` sampled_from `["movie","book","series"]`, `year` y `creator` opcionales
    - Verificar: `result.pending_at is not None`, `result.pending_at <= datetime.utcnow()`, `result.started_at is None`, `result.completed_at is None`
    - _Req 2 (CA1, CA2, CA3)_

  - [ ] 5.3 *Propiedad 2: Cambio de estado sobreescribe exactamente el timestamp destino
    - `# Feature: media-tracker, Property 2: Cambio de estado sobreescribe exactamente el timestamp destino`
    - Estrategia: crear item, llevarlo a estado inicial aleatorio, elegir estado destino diferente, guardar timestamps antes del cambio
    - Verificar: timestamp destino es no nulo y ≥ valor previo; timestamps de los otros dos estados son exactamente iguales a sus valores previos
    - _Req 3 (CA1, CA2, CA3, CA4)_

  - [ ] 5.4 *Propiedad 3: Idempotencia — mismo estado no modifica timestamps
    - `# Feature: media-tracker, Property 3: Idempotencia — cambiar al mismo estado no modifica timestamps`
    - Estrategia: crear item, llevarlo a estado aleatorio, guardar timestamps, ejecutar `update_status` con el mismo estado
    - Verificar: los tres timestamps son exactamente iguales a sus valores previos
    - _Req 3 (CA5)_

  - [ ] 5.5 *Propiedad 4: Ciclo completo produce tres timestamps no nulos ordenados
    - `# Feature: media-tracker, Property 4: Ciclo completo de estados produce tres timestamps no nulos`
    - Estrategia: crear item con título y tipo aleatorios
    - Verificar: tras `pending` → `in_progress` → `completed`, los tres timestamps son no nulos y `pending_at <= started_at <= completed_at`
    - _Req 2 (CA1), Req 3 (CA1, CA2, CA3)_

  - [ ] 5.6 *Propiedad 5: `pending_at` en respuesta API coincide con el modelo
    - `# Feature: media-tracker, Property 5: pending_at en respuesta API coincide con el modelo`
    - Usar `httpx.AsyncClient` + `ASGITransport` + `app.dependency_overrides[get_session]` con sesión SQLite in-memory
    - Verificar: crear item vía `POST /api/media`, obtener vía `GET /api/media/{id}`, consultar `session.get(MediaItem, id)`, comparar `response_json["pending_at"]` con `item.pending_at`
    - _Req 4 (CA1, CA2, CA4)_

- [x] 6. Mini-Timeline en `MediaDetailView.vue`
  - [x] 6.1 Añadir computed `hasTimeline` en el bloque `<script setup>` de `frontend/src/views/MediaDetailView.vue`
    - `const hasTimeline = computed(() => currentItem.value?.pending_at || currentItem.value?.started_at || currentItem.value?.completed_at)`
    - _Req 5 (CA1)_

  - [x] 6.2 Añadir función `formatDate(iso)` en el bloque `<script setup>` de `MediaDetailView.vue`
    - Usar `new Date(iso).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })`
    - Retornar string vacío si `iso` es falsy
    - _Req 5 (CA5)_

  - [x] 6.3 Añadir markup de la mini-timeline en el `<template>`, dentro de `.detail-main`, entre la card de Status y el componente `RatingInput`
    - Contenedor `div.card` con `v-if="hasTimeline"` y label "Timeline"
    - Tres hitos (`Pending`, `In Progress`, `Completed`) conectados por líneas, con `role="list"` y `role="listitem"`
    - Cada hito muestra dot coloreado, label, y fecha formateada (si el timestamp existe)
    - Hitos activos (timestamp no nulo): clase `timeline-step--active` con color y fecha
    - Hitos inactivos (timestamp nulo): opacidad reducida, sin fecha
    - `aria-label` descriptivo en cada hito (ej: "Pending since 12 mar 2026" o "Pending — no date")
    - _Req 5 (CA1, CA2, CA3, CA4, CA5, CA6)_

  - [x] 6.4 Añadir estilos scoped para la mini-timeline en `<style scoped>` de `MediaDetailView.vue`
    - Layout horizontal con flexbox, dots coloreados por estado usando variables CSS existentes (`--color-status-pending-*`, `--color-status-in-progress-*`, `--color-status-completed-*`)
    - Media query `@media (max-width: 500px)` para layout vertical con línea conectora vertical
    - Transiciones suaves con `var(--transition-fast)`
    - _Req 5 (CA7, CA8)_

- [x] 7. Verificación MCP — confirmar que `pending_at` se propaga correctamente
  - [x] 7.1 Verificar que no se requieren cambios en `backend/mcp/server.py`
    - Las herramientas `create_media` y `update_status` delegan en `MediaService`, que ya gestiona `pending_at`
    - La serialización `result.model_dump(mode="json")` incluye `pending_at` automáticamente al estar en `MediaResponse`
    - _Req 6 (CA1, CA2, CA3)_

  - [x] 7.2 Verificar manualmente con `mcp_server.call_tool("create_media", {...})` que la respuesta incluye `pending_at` no nulo
    - Verificar con `mcp_server.call_tool("update_status", {...})` que el timestamp correcto se actualiza
    - _Req 6 (CA1, CA2, CA3)_

- [x] 8. Checkpoint final — todos los tests pasan
  - [x] 8.1 Ejecutar `pytest tests/` y confirmar que todos los tests (existentes + nuevos) pasan sin errores
    - _Req 1-6_

  - [x] 8.2 Ejecutar `ruff check backend/` para confirmar que no hay errores de linting
    - _Req 1-4_

  - [x] 8.3 Verificar visualmente la mini-timeline en el frontend: hitos activos con color y fecha, hitos inactivos grises, layout responsive en < 500px
    - _Req 5_

  - [x] 8.4 Confirmar que `alembic current` muestra revisión `006` y que `alembic downgrade -1` + `alembic upgrade head` funciona sin errores
    - _Req 1 (CA4)_

## Notas

- Las tareas marcadas con `*` son opcionales (property tests) y pueden omitirse para avance más rápido
- Cada tarea referencia requisitos específicos para trazabilidad
- Los checkpoints (tareas 4 y 8) aseguran validación incremental
- No se requieren cambios en el MCP server — la propagación es automática vía `MediaService` + `MediaResponse`
- Items existentes previos a la migración tendrán `pending_at = NULL` — la timeline los muestra como hitos inactivos
