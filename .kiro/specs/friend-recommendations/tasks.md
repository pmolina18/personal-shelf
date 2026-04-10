# Tareas de Implementación — Recomendaciones entre Amigos

## Tarea 1: Modelo + Migración + Schemas (Backend foundation)

Requisitos: Req 1, Req 2, Req 3

- [x] 1.1 Crear `backend/models/recommendation.py` con el modelo `Recommendation` (tabla, FKs, índice compuesto, UNIQUE constraint, relaciones con `lazy="selectin"`)
- [x] 1.2 Importar `Recommendation` en `backend/models/user.py` o en el `env.py` de Alembic para que `autogenerate` lo detecte
- [x] 1.3 Generar migración: `alembic revision --autogenerate -m "add recommendations table"` desde `backend/`
- [x] 1.4 Crear `backend/schemas/recommendation.py` con `RecommendationCreate`, `RecommendationSender`, `RecommendationMediaItem`, `RecommendationResponse`, `RecommendationListResponse`, `UnreadCountResponse`

## Tarea 2: Servicio de recomendaciones

Requisitos: Req 4, Req 6

- [x] 2.1 Crear `backend/services/recommendation_service.py` con la clase `RecommendationService`
- [x] 2.2 Implementar `send()` con validaciones: auto-recomendación (400), receiver existe (404), media_item existe (404), amistad confirmada (403), duplicado (409), INSERT + response
- [x] 2.3 Implementar `list_received()` con paginación, filtro `unread_only`, ORDER BY `created_at` DESC
- [x] 2.4 Implementar `get_unread_count()` con SELECT COUNT WHERE receiver_id + is_read=false
- [x] 2.5 Implementar `mark_as_read()` con verificación de ownership (404 si no pertenece al usuario)
- [x] 2.6 Implementar `mark_all_as_read()` con UPDATE masivo
- [x] 2.7 Implementar helper `_to_response()` para convertir ORM → RecommendationResponse (calcular image_url desde image_path)

## Tarea 3: Router + registro en main.py

Requisitos: Req 5

- [x] 3.1 Crear `backend/routers/recommendations.py` con los 5 endpoints (POST send, GET list, GET unread-count, PATCH mark-read, POST mark-all-read)
- [x] 3.2 Registrar el router en `backend/main.py` con `app.include_router(recommendations_router)` después de `feed_router`

## Checkpoint 1: Backend funcional

Verificar que los endpoints responden correctamente con curl o tests manuales. Ejecutar `python -m pytest tests/` para confirmar que los tests existentes siguen pasando.

---

## Tarea 4: Property tests (Hypothesis)

Requisitos: Props 1–6

- [ ]* 4.1 Crear `tests/test_property_recommendations.py` con helpers: `_fresh_session()`, `_create_user()`, `_create_media_item()`, `_create_friendship()`
- [ ]* 4.2 Propiedad 1: Solo amigos pueden recomendar → 403
- [ ]* 4.3 Propiedad 2: No duplicar recomendación → 409
- [ ]* 4.4 Propiedad 3: Unread count consistente con is_read=false
- [ ]* 4.5 Propiedad 4: Mark-as-read reduce count en 1
- [ ]* 4.6 Propiedad 5: Mark-all-read → count = 0
- [ ]* 4.7 Propiedad 6: No auto-recomendación → 400

## Tarea 5: Tests de router (integration)

- [ ]* 5.1 Crear `tests/test_recommendation_router.py` con httpx.AsyncClient + ASGITransport + dependency_overrides
- [ ]* 5.2 Tests: 201 send, 200 list, 200 unread-count, 200 mark-read, 200 mark-all-read, 400/403/404/409 errores

## Checkpoint 2: Backend completo con tests

Ejecutar `python -m pytest tests/` — todos los tests (existentes + nuevos) deben pasar.

---

## Tarea 6: API client + Composable (Frontend foundation)

Requisitos: Req 7, Req 8

- [x] 6.1 Crear `frontend/src/api/recommendations.js` con las 5 funciones (sendRecommendation, listRecommendations, getUnreadCount, markAsRead, markAllAsRead)
- [x] 6.2 Crear `frontend/src/composables/useRecommendations.js` con refs independientes y métodos async (optimistic updates en markRead y markAllRead)

## Tarea 7: RecommendModal + botón en detalle

Requisitos: Req 9, Req 10

- [x] 7.1 Crear `frontend/src/components/RecommendModal.vue` (Teleport, listFriends, checkboxes, textarea con contador, envío múltiple, errores inline, accesibilidad)
- [x] 7.2 Modificar `frontend/src/views/MediaDetailView.vue` — añadir botón "Recomendar a amigo" + importar/renderizar RecommendModal

## Tarea 8: Badge en sidebar + enlace

Requisitos: Req 11

- [x] 8.1 Modificar `frontend/src/App.vue` — importar useRecommendations, fetchUnreadCount en onMounted + setInterval 60s, clearInterval en onUnmounted
- [x] 8.2 Añadir `<router-link to="/recommendations">` en sidebar (sección social, después de Friends) con badge condicional

## Tarea 9: Vista de recomendaciones + ruta

Requisitos: Req 12, Req 13

- [x] 9.1 Crear `frontend/src/views/RecommendationsView.vue` (lista, estados leída/no leída, marcar leída, marcar todas, paginación, estado vacío)
- [x] 9.2 Modificar `frontend/src/router/index.js` — añadir ruta `/recommendations` con lazy loading

## Checkpoint 3: Feature completa

Verificar flujo end-to-end: enviar recomendación desde detalle → badge se actualiza → vista de recomendaciones muestra la nueva → marcar como leída → badge se actualiza. Ejecutar `python -m pytest tests/` para confirmar que todo sigue verde.
