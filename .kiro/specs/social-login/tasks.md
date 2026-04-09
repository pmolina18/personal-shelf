# Plan de Implementación: Social Login

## Visión General

Implementación incremental para transformar Personal Shelf de una app mono-usuario a una plataforma multi-usuario con capacidades sociales. Se construye en capas: primero modelos y migración, luego servicios de autenticación, multi-tenancy sobre servicios existentes, sistema de amistades, feed social, y finalmente el frontend con auth, guards y vistas sociales. Los tests de propiedad con Hypothesis validan las 27 propiedades de correctitud del diseño.

## Tareas

- [x] 1. Modelos de datos, schemas y migración
  - [x] 1.1 Crear modelo User, tabla friendships y modelo FriendRequest
    - Crear `backend/models/user.py` con clase `User` (id, email, username, password_hash, created_at), tabla `friendships` (user_id, friend_id, created_at como tabla asociativa con dos PKs), y clase `FriendRequest` (id, from_user_id, to_user_id, status, created_at)
    - Añadir relación `media_items` en User con back_populates
    - Usar `from __future__ import annotations` para type hints genéricos
    - _Requisitos: 1.1, 6.1, 7.1, 8.1, 12.1_

  - [x] 1.2 Añadir user_id FK a MediaItem existente
    - Modificar `backend/models/media.py`: añadir `user_id: Mapped[int]` con FK a `users.id` y relación `owner` con back_populates a User
    - _Requisitos: 5.1, 5.4, 12.2_

  - [x] 1.3 Crear schemas Pydantic de autenticación y social
    - Crear `backend/schemas/auth.py` con `UserRegister` (email con regex, username min 3 max 100, password min 8), `UserLogin`, `UserResponse`, `TokenResponse`, `RefreshRequest`, `TokenPairResponse`
    - Crear `backend/schemas/social.py` con `FriendRequestCreate`, `FriendRequestResponse`, `FriendResponse`, `FeedEntry`, `FeedResponse`
    - _Requisitos: 1.1, 1.4, 1.6, 2.1, 6.1, 9.2_

  - [x] 1.4 Crear migración Alembic 002_social_login
    - Crear `backend/migrations/versions/002_social_login.py` con: tabla `users`, usuario legacy, columna `user_id` en `media_items` con default al legacy user, FK NOT NULL, tablas `friend_requests` y `friendships`
    - Usar patrón async con `sys.path.insert` en env.py
    - _Requisitos: 12.1, 12.2, 12.3_

  - [x] 1.5 Actualizar configuración con settings JWT
    - Modificar `backend/config.py`: añadir `JWT_SECRET_KEY`, `JWT_ALGORITHM` (HS256), `ACCESS_TOKEN_EXPIRE_MINUTES` (30), `REFRESH_TOKEN_EXPIRE_DAYS` (7)
    - Añadir `passlib[bcrypt]` y `python-jose[cryptography]` a `backend/requirements.txt`
    - _Requisitos: 2.3, 2.4_

- [x] 2. Servicio de autenticación y dependency de usuario
  - [x] 2.1 Implementar AuthService
    - Crear `backend/services/auth_service.py` con métodos: `register(session, data)` → crea usuario con hash bcrypt, devuelve tokens; `login(session, data)` → verifica credenciales, devuelve tokens; `refresh(session, refresh_token)` → valida y rota tokens
    - Funciones helper: `_hash_password`, `_verify_password` (passlib bcrypt), `_create_access_token`, `_create_refresh_token` (python-jose)
    - Manejar errores: 409 email/username duplicado, 401 credenciales inválidas (mensaje genérico), 401 refresh token inválido
    - Usar `from __future__ import annotations`
    - _Requisitos: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 3.1, 3.2_

  - [x] 2.2 Implementar dependency get_current_user
    - Crear `backend/dependencies.py` con `get_current_user(token)`: decodifica JWT del header Authorization Bearer, busca usuario por `sub` claim, devuelve User o lanza 401
    - _Requisitos: 4.1, 4.2, 4.3_

  - [x] 2.3 Implementar router de autenticación
    - Crear `backend/routers/auth.py` con endpoints: `POST /api/auth/register` (201), `POST /api/auth/login` (200), `POST /api/auth/refresh` (200)
    - Registrar router en `backend/main.py` ANTES del mount de static files
    - _Requisitos: 1.1, 2.1, 3.1_

  - [x] 2.4 Tests de propiedad para autenticación (P1-P7)
    - [x] 2.4.1 Propiedad 1: Round-trip de registro y login
      - **Propiedad 1: Round-trip de registro y login**
      - Para cualquier email/username/password válidos, registrar y luego login devuelve tokens válidos
      - Usar `_fresh_session()` con SQLite in-memory, `unique=True` en `st.lists()` para emails/usernames
      - **Valida: Requisitos 1.1, 2.1**
    - [x] 2.4.2 Propiedad 2: Rechazo de registro duplicado
      - **Propiedad 2: Rechazo de registro duplicado**
      - Registrar con email o username existente → error 409, sin cambio en conteo de usuarios
      - **Valida: Requisitos 1.2, 1.3**
    - [x] 2.4.3 Propiedad 3: Validación de contraseña corta
      - **Propiedad 3: Validación de contraseña corta**
      - Contraseña de 0-7 caracteres → rechazo, sin usuario creado
      - **Valida: Requisito 1.4**
    - [x] 2.4.4 Propiedad 4: Hashing de contraseña con bcrypt
      - **Propiedad 4: Hashing de contraseña con bcrypt**
      - Tras registro, password_hash ≠ password y bcrypt.verify(password, hash) == True
      - **Valida: Requisito 1.5**
    - [x] 2.4.5 Propiedad 5: Rechazo de credenciales inválidas
      - **Propiedad 5: Rechazo de credenciales inválidas**
      - Email no registrado o password incorrecto → 401 con mensaje genérico
      - **Valida: Requisito 2.2**
    - [x] 2.4.6 Propiedad 6: Expiración correcta de tokens
      - **Propiedad 6: Expiración correcta de tokens**
      - Access token exp ≈ 30 min, refresh token exp ≈ 7 días desde emisión
      - **Valida: Requisitos 2.3, 2.4**
    - [x] 2.4.7 Propiedad 7: Identidad del token
      - **Propiedad 7: Identidad del token**
      - El claim `sub` del access token corresponde al ID del usuario registrado
      - **Valida: Requisito 4.3**

  - [x] 2.5 Tests de propiedad para protección y refresh (P8-P10)
    - [x] 2.5.1 Propiedad 8: Endpoints protegidos rechazan sin auth
      - **Propiedad 8: Endpoints protegidos rechazan peticiones sin autenticación**
      - Petición sin Authorization o con token inválido/expirado → 401
      - Usar httpx.AsyncClient + ASGITransport con app.dependency_overrides
      - **Valida: Requisitos 4.1, 4.2**
    - [x] 2.5.2 Propiedad 9: Flujo de refresh token
      - **Propiedad 9: Flujo de refresh token**
      - Refresh token válido → nuevo par de tokens válidos
      - **Valida: Requisito 3.1**
    - [x] 2.5.3 Propiedad 10: Rechazo de refresh token inválido
      - **Propiedad 10: Rechazo de refresh token inválido**
      - String no-JWT o JWT expirado → 401
      - **Valida: Requisito 3.2**

  - [x] 2.6 Tests unitarios del router de autenticación
    - Crear `tests/test_auth_router.py` con httpx.AsyncClient + ASGITransport
    - Tests: registro exitoso (201), registro duplicado (409), login exitoso, login fallido (401), refresh exitoso, refresh inválido (401)
    - _Requisitos: 1.1, 1.2, 1.3, 2.1, 2.2, 3.1, 3.2_

- [x] 3. Checkpoint — Verificar autenticación
  - Asegurar que todos los tests pasan, preguntar al usuario si surgen dudas.

- [x] 4. Multi-tenancy: adaptar servicios existentes
  - [x] 4.1 Modificar MediaService para filtrar por user_id
    - Modificar `backend/services/media_service.py`: todos los métodos reciben `user_id: int`, create asigna user_id, get/update/delete verifican ownership (403 si no coincide), list filtra por user_id
    - _Requisitos: 5.1, 5.2, 5.3, 5.4_

  - [x] 4.2 Modificar StatsService y ExportService para filtrar por user_id
    - Modificar `backend/services/stats_service.py`: `get_stats(session, user_id)` filtra por user_id
    - Modificar `backend/services/export_service.py`: `export_catalog(session, user_id)` y `import_catalog(session, user_id, data)` filtran por user_id
    - _Requisitos: 5.5, 5.6_

  - [x] 4.3 Inyectar get_current_user en routers existentes
    - Modificar `backend/routers/media.py`: añadir `Depends(get_current_user)` a todos los endpoints, pasar `user.id` a los métodos del servicio
    - Modificar `backend/routers/stats.py`: inyectar usuario y pasar user_id
    - Modificar `backend/routers/export_import.py`: inyectar usuario y pasar user_id
    - _Requisitos: 4.1, 4.3, 5.1, 5.5, 5.6_

  - [x] 4.4 Tests de propiedad para multi-tenancy (P11-P14)
    - [x] 4.4.1 Propiedad 11: Asignación de user_id al crear item
      - **Propiedad 11: Propiedad de items — asignación de user_id**
      - Al crear un item, user_id del item == ID del usuario autenticado
      - **Valida: Requisito 5.1**
    - [x] 4.4.2 Propiedad 12: Aislamiento de listado por usuario
      - **Propiedad 12: Aislamiento de listado por usuario**
      - Dos usuarios distintos, cada uno ve solo sus propios items
      - **Valida: Requisito 5.2**
    - [x] 4.4.3 Propiedad 13: Rechazo de acceso cruzado
      - **Propiedad 13: Rechazo de acceso cruzado entre usuarios**
      - Usuario B no puede acceder/modificar/eliminar items de usuario A → 403
      - **Valida: Requisito 5.3**
    - [x] 4.4.4 Propiedad 14: Aislamiento de estadísticas y exportación
      - **Propiedad 14: Aislamiento de estadísticas y exportación**
      - Stats y export de cada usuario reflejan solo sus propios items
      - **Valida: Requisitos 5.5, 5.6**

- [x] 5. Checkpoint — Verificar multi-tenancy
  - Asegurar que todos los tests pasan, preguntar al usuario si surgen dudas.

- [x] 6. Sistema de amistades
  - [x] 6.1 Implementar FriendService
    - Crear `backend/services/friend_service.py` con métodos: `send_request(session, from_user_id, username)`, `accept_request(session, user_id, request_id)`, `reject_request(session, user_id, request_id)`, `list_pending(session, user_id)`, `list_friends(session, user_id)`, `remove_friend(session, user_id, friend_id)`, `search_users(session, user_id, query)`
    - Amistad bidireccional: al aceptar, insertar dos filas en friendships (A→B y B→A)
    - Validaciones: auto-solicitud (400), duplicada/ya amigos (409), solicitud ajena (403), no encontrado (404)
    - Usar `from __future__ import annotations`
    - _Requisitos: 6.1, 6.2, 6.3, 6.4, 6.5, 7.1, 7.2, 7.3, 7.4, 8.1, 8.2, 8.3_

  - [x] 6.2 Implementar router de amistades
    - Crear `backend/routers/friends.py` con endpoints: `POST /api/friends/requests`, `GET /api/friends/requests/pending`, `POST /api/friends/requests/{request_id}/accept`, `POST /api/friends/requests/{request_id}/reject`, `GET /api/friends`, `DELETE /api/friends/{friend_id}`, `GET /api/friends/search`
    - Todos los endpoints protegidos con `Depends(get_current_user)`
    - Registrar router en `backend/main.py` ANTES del mount de static files
    - _Requisitos: 6.1, 6.5, 7.1, 7.2, 7.3, 8.1, 8.3_

  - [x] 6.3 Tests de propiedad para amistades (P15-P23)
    - [x] 6.3.1 Propiedad 15: Creación de solicitud de amistad
      - **Propiedad 15: Creación de solicitud de amistad**
      - Dos usuarios sin relación → solicitud con status "pending", from/to correctos
      - **Valida: Requisito 6.1**
    - [x] 6.3.2 Propiedad 16: Validación de solicitudes
      - **Propiedad 16: Validación de solicitudes de amistad**
      - Auto-solicitud → 400, ya amigos → 409, solicitud pendiente duplicada → 409
      - **Valida: Requisitos 6.2, 6.3, 6.4**
    - [x] 6.3.3 Propiedad 17: Búsqueda de usuarios por nombre
      - **Propiedad 17: Búsqueda de usuarios por nombre**
      - Resultados contienen solo usuarios con substring match (case-insensitive), excluyendo al buscador
      - **Valida: Requisito 6.5**
    - [x] 6.3.4 Propiedad 18: Aceptar solicitud crea amistad bidireccional
      - **Propiedad 18: Aceptar solicitud crea amistad bidireccional**
      - Aceptar → ambos en lista de amigos del otro, solicitud eliminada
      - **Valida: Requisito 7.1**
    - [x] 6.3.5 Propiedad 19: Rechazar solicitud no crea amistad
      - **Propiedad 19: Rechazar solicitud no crea amistad**
      - Rechazar → solicitud eliminada, ninguno en lista de amigos del otro
      - **Valida: Requisito 7.2**
    - [x] 6.3.6 Propiedad 20: Listado de solicitudes pendientes
      - **Propiedad 20: Listado de solicitudes pendientes**
      - N solicitudes recibidas → exactamente N en listado con username del remitente
      - **Valida: Requisito 7.3**
    - [x] 6.3.7 Propiedad 21: Autorización de acciones sobre solicitudes
      - **Propiedad 21: Autorización de acciones sobre solicitudes**
      - Usuario C no puede aceptar/rechazar solicitud de A→B → 403
      - **Valida: Requisito 7.4**
    - [x] 6.3.8 Propiedad 22: Eliminación de amistad bidireccional
      - **Propiedad 22: Eliminación de amistad es bidireccional**
      - Eliminar amistad → ninguno aparece en lista del otro
      - **Valida: Requisito 8.1**
    - [x] 6.3.9 Propiedad 23: Listado de amigos
      - **Propiedad 23: Listado de amigos**
      - N amigos confirmados → exactamente N entradas con id y username
      - **Valida: Requisito 8.3**

  - [x] 6.4 Tests unitarios del router de amistades
    - Crear `tests/test_friends_router.py` con httpx.AsyncClient + ASGITransport
    - Tests: enviar solicitud, aceptar, rechazar, listar pendientes, listar amigos, eliminar amistad, buscar usuarios, errores (400, 403, 404, 409)
    - _Requisitos: 6.1, 6.2, 6.3, 6.4, 6.5, 7.1, 7.2, 7.3, 7.4, 8.1, 8.3_

- [x] 7. Checkpoint — Verificar amistades
  - Asegurar que todos los tests pasan, preguntar al usuario si surgen dudas.

- [x] 8. Feed social
  - [x] 8.1 Implementar FeedService
    - Crear `backend/services/feed_service.py` con métodos: `get_feed(session, user_id, page, size)` → consulta media_items de amigos con actividad en últimos 30 días, ordenado por fecha desc, paginado (max 20); `get_friend_collection(session, user_id, friend_id, filters, page, size)` → verifica amistad (403 si no), devuelve items del amigo con filtros
    - Acciones del feed: "added" (created_at), "completed" (completed_at), "rated" (updated_at con rating no null)
    - Usar `from __future__ import annotations`
    - _Requisitos: 9.1, 9.2, 9.3, 9.5, 10.1, 10.2_

  - [x] 8.2 Implementar router de feed
    - Crear `backend/routers/feed.py` con endpoints: `GET /api/feed` (paginado), `GET /api/feed/friends/{friend_id}/collection` (con filtros media_type, status, search, tag, page, size)
    - Protegidos con `Depends(get_current_user)`
    - Registrar router en `backend/main.py` ANTES del mount de static files
    - _Requisitos: 9.1, 9.3, 10.1_

  - [x] 8.3 Tests de propiedad para feed (P24-P27)
    - [x] 8.3.1 Propiedad 24: Feed muestra actividad de amigos ordenada
      - **Propiedad 24: Feed social muestra actividad de amigos ordenada cronológicamente**
      - Solo items de amigos, con username/título/tipo/acción/fecha, orden desc, max 20 por página
      - **Valida: Requisitos 9.1, 9.2, 9.3**
    - [x] 8.3.2 Propiedad 25: Feed limitado a 30 días
      - **Propiedad 25: Feed limitado a 30 días**
      - Ninguna entrada con fecha > 30 días atrás
      - **Valida: Requisito 9.5**
    - [x] 8.3.3 Propiedad 26: Acceso a colección de amigo
      - **Propiedad 26: Acceso a colección de amigo**
      - Amigos pueden ver colección del otro con filtros, resultados solo del amigo
      - **Valida: Requisito 10.1**
    - [x] 8.3.4 Propiedad 27: Rechazo de acceso a colección de no-amigo
      - **Propiedad 27: Rechazo de acceso a colección de no-amigo**
      - No-amigos → 403
      - **Valida: Requisito 10.2**

  - [x] 8.4 Tests unitarios del router de feed
    - Crear `tests/test_feed_router.py` con httpx.AsyncClient + ASGITransport
    - Tests: feed con amigos, feed vacío, paginación, colección de amigo con filtros, acceso a no-amigo (403)
    - _Requisitos: 9.1, 9.3, 9.4, 9.5, 10.1, 10.2_

- [x] 9. Checkpoint — Verificar feed social
  - Asegurar que todos los tests pasan, preguntar al usuario si surgen dudas.

- [x] 10. Frontend: autenticación y guards de navegación
  - [x] 10.1 Crear cliente HTTP de autenticación
    - Crear `frontend/src/api/auth.js` con funciones: `register(email, username, password)`, `login(email, password)`, `refresh(refreshToken)` — llamadas a `/api/auth/*`
    - _Requisitos: 1.1, 2.1, 3.1_

  - [x] 10.2 Crear cliente HTTP social
    - Crear `frontend/src/api/social.js` con funciones: `sendFriendRequest(username)`, `getPendingRequests()`, `acceptRequest(id)`, `rejectRequest(id)`, `listFriends()`, `removeFriend(id)`, `searchUsers(query)`, `getFeed(page)`, `getFriendCollection(friendId, params)` — llamadas a `/api/friends/*` y `/api/feed/*`
    - _Requisitos: 6.1, 7.3, 8.3, 9.1, 10.1_

  - [x] 10.3 Implementar composable useAuth
    - Crear `frontend/src/composables/useAuth.js` con: estado reactivo (user, accessToken, refreshToken, isAuthenticated), métodos (login, register, logout, refreshToken), persistencia en localStorage, interceptor para añadir header Authorization a peticiones, refresh automático en error 401
    - _Requisitos: 11.1, 11.2, 11.3, 11.4, 11.5_

  - [x] 10.4 Añadir header Authorization al cliente HTTP existente
    - Modificar `frontend/src/api/media.js`: la función `request()` debe incluir `Authorization: Bearer <token>` de localStorage en todas las peticiones
    - _Requisitos: 4.1, 11.3_

  - [x] 10.5 Configurar navigation guards y nuevas rutas
    - Modificar `frontend/src/router/index.js`: añadir rutas para login, register, feed, friends, friend-collection; añadir `beforeEach` guard que redirige a login si no autenticado (rutas protegidas) y a catálogo si autenticado (rutas de auth)
    - Rutas públicas: `/login`, `/register`
    - Rutas protegidas: `/`, `/media/*`, `/stats`, `/import-export`, `/feed`, `/friends`, `/friends/:id/collection`
    - _Requisitos: 11.1, 11.2_

  - [x] 10.6 Tests frontend del composable useAuth
    - Crear `frontend/src/__tests__/composables/useAuth.test.js` con vitest
    - Tests: login guarda tokens en localStorage, logout limpia estado, isAuthenticated reactivo, refresh automático
    - _Requisitos: 11.3, 11.4, 11.5_

  - [x] 10.7 Tests frontend de navigation guards
    - Crear `frontend/src/__tests__/router/guards.test.js` con vitest
    - Tests: redirige a login sin auth, redirige a catálogo con auth en /login, permite acceso con auth
    - _Requisitos: 11.1, 11.2_

- [x] 11. Frontend: vistas de autenticación y social
  - [x] 11.1 Implementar LoginView y RegisterView
    - Crear `frontend/src/views/LoginView.vue` con formulario de email + contraseña, enlace a registro, manejo de errores
    - Crear `frontend/src/views/RegisterView.vue` con formulario de email + username + contraseña, validación de contraseña ≥8 chars, enlace a login
    - Usar `<script setup>`, `<style scoped>`, accesibilidad (aria-labels, role="alert" para errores)
    - _Requisitos: 1.1, 1.6, 2.1_

  - [x] 11.2 Implementar FeedView
    - Crear `frontend/src/views/FeedView.vue` con lista paginada de actividad de amigos, cada entrada muestra username/título/tipo/acción/fecha, mensaje de feed vacío sugiriendo buscar amigos
    - _Requisitos: 9.1, 9.2, 9.3, 9.4_

  - [x] 11.3 Implementar FriendsView
    - Crear `frontend/src/views/FriendsView.vue` con: lista de amigos actuales, solicitudes pendientes recibidas (aceptar/rechazar), buscador de usuarios para enviar solicitudes, botón eliminar amistad
    - _Requisitos: 6.1, 6.5, 7.1, 7.2, 7.3, 8.1, 8.3_

  - [x] 11.4 Implementar FriendCollectionView
    - Crear `frontend/src/views/FriendCollectionView.vue` con colección del amigo en modo solo lectura, mismos filtros que CatalogView (tipo, estado, búsqueda, tag), paginación
    - _Requisitos: 10.1, 10.2, 10.3_

  - [x] 11.5 Modificar App.vue con navegación social y logout
    - Modificar `frontend/src/App.vue`: añadir enlaces de navegación a Feed y Amigos en sidebar, botón de logout, mostrar username del usuario autenticado
    - _Requisitos: 8.3, 9.1, 11.5_

- [x] 12. Checkpoint final — Verificar integración completa
  - Asegurar que todos los tests pasan, preguntar al usuario si surgen dudas.

## Notas

- Las tareas marcadas con `*` son opcionales y pueden omitirse para un MVP más rápido
- Cada tarea referencia requisitos específicos para trazabilidad
- Los checkpoints aseguran validación incremental
- Los tests de propiedad validan las 27 propiedades de correctitud del diseño usando Hypothesis
- Los tests de propiedad usan `sync def test_*` con `asyncio.run()` internamente (patrón del proyecto)
- Los tests de router usan `httpx.AsyncClient` + `ASGITransport` con `app.dependency_overrides`
- Usar `from __future__ import annotations` en archivos Python con type hints genéricos
- Registrar routers ANTES del mount de static files en main.py
