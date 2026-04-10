# Documento de Requisitos — Recomendaciones entre Amigos

## Introducción

Personal Shelf ya cuenta con un sistema de amistades bidireccional (tabla `friendships`, `FriendService`, solicitudes de amistad) y un catálogo de media items por usuario. Esta feature añade la capacidad de **recomendar items de media a amigos**: un usuario puede seleccionar una película, libro o serie de su catálogo (o del catálogo de un amigo) y enviársela como recomendación a uno o varios amigos, con un mensaje opcional.

El sistema incluye:
- **Modelo de recomendaciones**: tabla `recommendations` con sender, receiver, media item, mensaje opcional y estado de lectura.
- **Servicio y endpoints REST**: para enviar, listar, contar no leídas y marcar como leídas.
- **Notificaciones en el frontend**: badge con contador de recomendaciones no leídas en el sidebar, modal para enviar recomendaciones, y vista dedicada para ver las recomendaciones recibidas.
- **Validaciones de negocio**: solo se puede recomendar a amigos confirmados, no a uno mismo, y no se permite duplicar la misma recomendación.

## Glosario

- **Recomendación**: Registro que representa el acto de un Usuario (sender) sugiriendo un Media_Item a otro Usuario (receiver), con un mensaje opcional.
- **Sender**: Usuario que envía la recomendación.
- **Receiver**: Usuario que recibe la recomendación.
- **Sistema_Recomendaciones**: Subsistema backend responsable de crear, listar, contar y gestionar el estado de lectura de las recomendaciones.
- **Badge_Notificación**: Indicador visual en el sidebar del frontend que muestra el número de recomendaciones no leídas del usuario autenticado.
- **RecommendModal**: Componente modal del frontend que permite seleccionar amigo(s) y escribir un mensaje para enviar una recomendación.
- **Amistad_Confirmada**: Relación bidireccional existente en la tabla `friendships` entre dos usuarios.
- **Unread_Count**: Número de recomendaciones recibidas por un usuario que tienen `is_read=false`.

## Requisitos

### Requisito 1: Modelo de datos de recomendaciones

**User Story:** Como desarrollador, quiero una tabla `recommendations` en la base de datos que almacene las recomendaciones entre usuarios, para poder persistir y consultar esta información de forma eficiente.

#### Criterios de Aceptación

1. THE Sistema_Recomendaciones SHALL crear un modelo `Recommendation` mapeado a la tabla `recommendations` con las siguientes columnas: `id` (INTEGER PK autoincrement), `sender_id` (INTEGER FK → `users.id`, NOT NULL), `receiver_id` (INTEGER FK → `users.id`, NOT NULL), `media_item_id` (INTEGER FK → `media_items.id`, NOT NULL), `message` (TEXT, nullable, máximo 500 caracteres), `is_read` (BOOLEAN, NOT NULL, default `false`), `created_at` (TIMESTAMP, `server_default=func.now()`).
2. THE Sistema_Recomendaciones SHALL crear un índice compuesto en `(receiver_id, is_read)` para optimizar las queries del Badge_Notificación y el listado de recomendaciones no leídas.
3. THE Sistema_Recomendaciones SHALL definir relaciones SQLAlchemy con `lazy="selectin"` hacia `User` (sender y receiver) y hacia `MediaItem` para carga eficiente.
4. THE Sistema_Recomendaciones SHALL añadir un constraint UNIQUE en `(sender_id, receiver_id, media_item_id)` para prevenir recomendaciones duplicadas a nivel de base de datos.
5. THE Sistema_Recomendaciones SHALL usar `ondelete="CASCADE"` en las FKs de `sender_id`, `receiver_id` y `media_item_id` para que la eliminación de un usuario o media item elimine las recomendaciones asociadas.

**Archivos a crear/modificar:**
- Crear: `backend/models/recommendation.py`
- Modificar: `backend/models/__init__.py` (si existe, para re-exportar)

### Requisito 2: Migración Alembic para la tabla de recomendaciones

**User Story:** Como desarrollador, quiero una migración de Alembic que cree la tabla `recommendations`, para que el esquema de la base de datos se actualice de forma controlada.

#### Criterios de Aceptación

1. WHEN se ejecuta `alembic revision --autogenerate -m "add recommendations table"`, THE Sistema_Recomendaciones SHALL generar una migración que cree la tabla `recommendations` con todas las columnas, FKs, índice compuesto y constraint UNIQUE definidos en el Requisito 1.
2. WHEN se ejecuta `alembic upgrade head`, THE Sistema_Recomendaciones SHALL aplicar la migración sin errores tanto en PostgreSQL local como en Neon.dev.
3. WHEN se ejecuta `alembic downgrade -1`, THE Sistema_Recomendaciones SHALL revertir la migración eliminando la tabla `recommendations`.

**Archivos a crear:**
- `backend/migrations/versions/XXX_add_recommendations_table.py`

### Requisito 3: Schemas Pydantic para recomendaciones

**User Story:** Como desarrollador, quiero schemas Pydantic que validen las peticiones y serialicen las respuestas del sistema de recomendaciones, para mantener la consistencia de datos en la API.

#### Criterios de Aceptación

1. THE Sistema_Recomendaciones SHALL definir un schema `RecommendationCreate` con los campos: `receiver_id` (int, requerido), `media_item_id` (int, requerido), `message` (str, opcional, `max_length=500`).
2. THE Sistema_Recomendaciones SHALL definir un schema `RecommendationResponse` con `ConfigDict(from_attributes=True)` que incluya: `id`, `sender` (objeto con `id` y `username`), `receiver` (objeto con `id` y `username`), `media_item` (objeto con `id`, `title`, `media_type`, `image_url`), `message`, `is_read`, `created_at`.
3. THE Sistema_Recomendaciones SHALL definir un schema `UnreadCountResponse` con un campo `count` (int).
4. THE Sistema_Recomendaciones SHALL validar que `message` no exceda 500 caracteres usando `Field(max_length=500)`.

**Archivos a crear:**
- `backend/schemas/recommendation.py`

### Requisito 4: Servicio de recomendaciones

**User Story:** Como usuario, quiero poder enviar recomendaciones de media items a mis amigos, para compartir contenido que me ha gustado.

#### Criterios de Aceptación

1. WHEN un Usuario envía una recomendación a otro Usuario, THE Sistema_Recomendaciones SHALL verificar que existe una Amistad_Confirmada entre ambos en la tabla `friendships`. IF no son amigos, SHALL rechazar con error 403 ("Solo puedes recomendar a amigos confirmados").
2. WHEN un Usuario intenta recomendarse a sí mismo, THE Sistema_Recomendaciones SHALL rechazar con error 400 ("No puedes recomendarte a ti mismo").
3. WHEN un Usuario intenta enviar una recomendación duplicada (mismo sender, receiver y media_item), THE Sistema_Recomendaciones SHALL rechazar con error 409 ("Ya recomendaste este item a este usuario").
4. WHEN un Usuario envía una recomendación válida, THE Sistema_Recomendaciones SHALL crear un registro en la tabla `recommendations` con `is_read=false` y devolver la recomendación creada como `RecommendationResponse`.
5. WHEN un Usuario consulta sus recomendaciones recibidas, THE Sistema_Recomendaciones SHALL devolver una lista paginada de recomendaciones donde `receiver_id` es el usuario autenticado, ordenadas por `created_at` descendente, incluyendo datos del sender y del media item.
6. WHEN un Usuario consulta sus recomendaciones recibidas con filtro `unread_only=true`, THE Sistema_Recomendaciones SHALL devolver solo las recomendaciones con `is_read=false`.
7. WHEN un Usuario consulta el Unread_Count, THE Sistema_Recomendaciones SHALL devolver el número exacto de recomendaciones con `receiver_id=usuario` e `is_read=false`.
8. WHEN un Usuario marca una recomendación como leída, THE Sistema_Recomendaciones SHALL actualizar `is_read=true` en esa recomendación. IF la recomendación no pertenece al usuario o no existe, SHALL rechazar con error 404.
9. WHEN un Usuario ejecuta "marcar todas como leídas", THE Sistema_Recomendaciones SHALL actualizar `is_read=true` en todas las recomendaciones donde `receiver_id=usuario` e `is_read=false`.

**Archivos a crear:**
- `backend/services/recommendation_service.py`

### Requisito 5: Router de recomendaciones

**User Story:** Como desarrollador, quiero endpoints REST para todas las operaciones de recomendaciones, para que el frontend pueda interactuar con el sistema.

#### Criterios de Aceptación

1. THE Sistema_Recomendaciones SHALL exponer `POST /api/recommendations` que reciba un `RecommendationCreate` y devuelva un `RecommendationResponse` con código 201. El sender se obtiene del usuario autenticado vía `get_current_user`.
2. THE Sistema_Recomendaciones SHALL exponer `GET /api/recommendations` que devuelva las recomendaciones recibidas por el usuario autenticado, paginadas con parámetros `page` (default 1) y `size` (default 20), y filtrable con `unread_only` (boolean, default false).
3. THE Sistema_Recomendaciones SHALL exponer `GET /api/recommendations/unread-count` que devuelva un `UnreadCountResponse` con el número de recomendaciones no leídas del usuario autenticado.
4. THE Sistema_Recomendaciones SHALL exponer `PATCH /api/recommendations/{id}/read` que marque como leída una recomendación específica del usuario autenticado y devuelva la recomendación actualizada.
5. THE Sistema_Recomendaciones SHALL exponer `POST /api/recommendations/mark-all-read` que marque todas las recomendaciones no leídas del usuario autenticado como leídas y devuelva `{"message": "All recommendations marked as read"}`.
6. ALL los endpoints de recomendaciones SHALL requerir autenticación vía `Depends(get_current_user)`.
7. THE Sistema_Recomendaciones SHALL registrar el router en `backend/main.py` con `app.include_router(recommendations_router)` ANTES del mount de archivos estáticos.

**Archivos a crear/modificar:**
- Crear: `backend/routers/recommendations.py`
- Modificar: `backend/main.py` (registrar el nuevo router)


### Requisito 6: Validaciones de negocio

**User Story:** Como usuario, quiero que el sistema prevenga recomendaciones inválidas, para mantener la integridad de los datos y una buena experiencia de uso.

#### Criterios de Aceptación

1. WHEN un Usuario intenta recomendar un media item que no existe en la base de datos, THE Sistema_Recomendaciones SHALL rechazar con error 404 ("Media item no encontrado").
2. WHEN un Usuario intenta recomendar a un receiver que no existe en la base de datos, THE Sistema_Recomendaciones SHALL rechazar con error 404 ("Usuario no encontrado").
3. WHEN un Usuario intenta marcar como leída una recomendación que pertenece a otro usuario (receiver_id ≠ usuario autenticado), THE Sistema_Recomendaciones SHALL rechazar con error 404 para no revelar la existencia de la recomendación.
4. THE Sistema_Recomendaciones SHALL validar que el campo `message` no exceda 500 caracteres a nivel de schema Pydantic (validación automática por FastAPI, error 422).

**Archivos afectados:**
- `backend/services/recommendation_service.py`
- `backend/schemas/recommendation.py`

### Requisito 7: API client de recomendaciones en el frontend

**User Story:** Como desarrollador frontend, quiero un módulo de API que encapsule todas las llamadas HTTP al backend de recomendaciones, para mantener la separación de responsabilidades.

#### Criterios de Aceptación

1. THE Cliente_API SHALL exponer una función `sendRecommendation(receiverId, mediaItemId, message?)` que envíe un `POST /api/recommendations`.
2. THE Cliente_API SHALL exponer una función `listRecommendations(page?, unreadOnly?)` que envíe un `GET /api/recommendations` con los parámetros de query correspondientes.
3. THE Cliente_API SHALL exponer una función `getUnreadCount()` que envíe un `GET /api/recommendations/unread-count`.
4. THE Cliente_API SHALL exponer una función `markAsRead(id)` que envíe un `PATCH /api/recommendations/{id}/read`.
5. THE Cliente_API SHALL exponer una función `markAllAsRead()` que envíe un `POST /api/recommendations/mark-all-read`.
6. THE Cliente_API SHALL usar el mismo patrón de `request()` helper con token JWT de `localStorage` que usa `frontend/src/api/social.js`.

**Archivos a crear:**
- `frontend/src/api/recommendations.js`

### Requisito 8: Composable useRecommendations

**User Story:** Como desarrollador frontend, quiero un composable que gestione el estado reactivo de las recomendaciones, para compartir lógica entre componentes sin duplicar código.

#### Criterios de Aceptación

1. THE composable `useRecommendations` SHALL exponer refs reactivos: `recommendations` (lista), `unreadCount` (número), `loading` (boolean), `error` (string|null).
2. THE composable SHALL exponer métodos async: `fetchRecommendations(page?, unreadOnly?)`, `fetchUnreadCount()`, `send(receiverId, mediaItemId, message?)`, `markRead(id)`, `markAllRead()`.
3. WHEN `markRead(id)` se ejecuta exitosamente, THE composable SHALL decrementar `unreadCount` en 1 localmente (optimistic update).
4. WHEN `markAllRead()` se ejecuta exitosamente, THE composable SHALL poner `unreadCount` a 0 localmente.
5. THE composable SHALL devolver refs independientes por invocación (sin estado compartido a nivel de módulo), siguiendo el patrón de `useMedia.js`.

**Archivos a crear:**
- `frontend/src/composables/useRecommendations.js`

### Requisito 9: Botón "Recomendar" en la vista de detalle

**User Story:** Como usuario, quiero poder recomendar un media item a mis amigos desde la vista de detalle, para compartir contenido que me interesa.

#### Criterios de Aceptación

1. WHEN un Usuario autenticado está viendo el detalle de un media item, THE Client SHALL mostrar un botón "Recomendar a amigo" visible junto a las acciones existentes (editar, eliminar, etc.).
2. WHEN el Usuario hace click en "Recomendar a amigo", THE Client SHALL abrir el RecommendModal pasando el `media_item_id` y el `title` del item como props.
3. THE botón "Recomendar a amigo" SHALL tener un icono de compartir/enviar y ser accesible con `aria-label="Recomendar este item a un amigo"`.
4. THE botón SHALL estar visible tanto en items propios del usuario como en items de amigos (cuando se visualiza la colección de un amigo).

**Archivos a modificar:**
- `frontend/src/views/MediaDetailView.vue`

### Requisito 10: Modal de recomendación (RecommendModal)

**User Story:** Como usuario, quiero un modal donde pueda seleccionar a qué amigo(s) enviar la recomendación y escribir un mensaje opcional, para personalizar mi recomendación.

#### Criterios de Aceptación

1. WHEN el RecommendModal se abre, THE Client SHALL cargar la lista de amigos del usuario usando `listFriends()` del API social existente.
2. THE RecommendModal SHALL mostrar la lista de amigos con checkboxes para selección múltiple, mostrando el username de cada amigo.
3. THE RecommendModal SHALL incluir un campo de texto opcional para el mensaje (máximo 500 caracteres), con un contador de caracteres visible.
4. WHEN el Usuario hace click en "Enviar", THE Client SHALL enviar una recomendación por cada amigo seleccionado llamando a `sendRecommendation()` para cada uno.
5. WHEN todas las recomendaciones se envían exitosamente, THE RecommendModal SHALL cerrarse y mostrar un mensaje de éxito.
6. WHEN alguna recomendación falla (por ejemplo, duplicada), THE RecommendModal SHALL mostrar el error específico sin cerrar el modal, permitiendo al usuario corregir.
7. THE RecommendModal SHALL desactivar el botón "Enviar" si no hay amigos seleccionados.
8. THE RecommendModal SHALL usar `<Teleport to="body">` y seguir el patrón de overlay/modal del proyecto (fixed overlay, centered dialog, cierre con Escape y click fuera).
9. THE RecommendModal SHALL cumplir con accesibilidad: `role="dialog"`, `aria-modal="true"`, auto-focus al abrir, cierre con tecla Escape.

**Archivos a crear:**
- `frontend/src/components/RecommendModal.vue`

### Requisito 11: Badge de notificación en el sidebar

**User Story:** Como usuario, quiero ver un indicador visual en el sidebar con el número de recomendaciones no leídas, para saber cuándo tengo nuevas recomendaciones sin tener que entrar a la vista.

#### Criterios de Aceptación

1. WHEN un Usuario autenticado tiene recomendaciones no leídas, THE Client SHALL mostrar un badge circular con el Unread_Count junto al enlace "Recomendaciones" en el sidebar.
2. WHEN el Unread_Count es 0, THE Client SHALL ocultar el badge (no mostrar "0").
3. WHEN el Unread_Count supera 99, THE Client SHALL mostrar "99+" en el badge.
4. THE Client SHALL consultar el Unread_Count al montar el componente App.vue y actualizarlo periódicamente (cada 60 segundos) usando `setInterval`.
5. THE Client SHALL limpiar el intervalo de polling con `onUnmounted` para evitar memory leaks.
6. THE badge SHALL tener estilo visual consistente con el diseño del sidebar: fondo `var(--color-primary)`, texto blanco, border-radius circular, tamaño compacto (font-size 0.65rem).
7. THE Client SHALL añadir un nuevo enlace "Recomendaciones" en la sección social del sidebar (después de "Friends"), visible solo para usuarios autenticados.

**Archivos a modificar:**
- `frontend/src/App.vue`

### Requisito 12: Vista de recomendaciones recibidas

**User Story:** Como usuario, quiero una vista dedicada donde pueda ver todas las recomendaciones que he recibido de mis amigos, para explorar el contenido que me sugieren.

#### Criterios de Aceptación

1. THE Client SHALL mostrar una lista de recomendaciones recibidas con: nombre del sender, título del media item, tipo de media, imagen del item (si existe), mensaje del sender (si existe), fecha de la recomendación, y estado de lectura (leída/no leída).
2. WHEN una recomendación no está leída, THE Client SHALL mostrarla con un estilo visual diferenciado (fondo ligeramente destacado o indicador de "nueva").
3. THE Client SHALL incluir un botón "Marcar como leída" en cada recomendación no leída que llame a `markAsRead(id)`.
4. THE Client SHALL incluir un botón global "Marcar todas como leídas" que llame a `markAllAsRead()`, visible solo cuando hay recomendaciones no leídas.
5. WHEN el Usuario hace click en el título o imagen del media item recomendado, THE Client SHALL navegar a la vista de detalle de ese media item (`/media/{id}` si es propio, o la colección del amigo si es de otro usuario).
6. THE Client SHALL paginar las recomendaciones con el componente `Pagination` existente.
7. WHEN no hay recomendaciones, THE Client SHALL mostrar un mensaje vacío amigable ("Aún no tienes recomendaciones. ¡Tus amigos pueden recomendarte películas, libros y series!").

**Archivos a crear:**
- `frontend/src/views/RecommendationsView.vue`

### Requisito 13: Ruta de recomendaciones en el router

**User Story:** Como usuario, quiero acceder a la vista de recomendaciones desde una URL dedicada, para poder navegar directamente a ella.

#### Criterios de Aceptación

1. THE Client SHALL registrar la ruta `/recommendations` con el nombre `recommendations` y el componente `RecommendationsView` en el router de Vue.
2. THE ruta `/recommendations` SHALL ser una ruta protegida (requiere autenticación, misma lógica que las demás rutas protegidas del `beforeEach` guard).
3. THE Client SHALL usar lazy loading (`() => import(...)`) para el componente `RecommendationsView`, siguiendo el patrón existente del router.

**Archivos a modificar:**
- `frontend/src/router/index.js`

## Propiedades de Corrección (Hypothesis)

Las siguientes propiedades deben validarse con tests property-based usando Hypothesis, siguiendo el patrón del proyecto (sync `def test_*` con `asyncio.run()` interno, `_fresh_session()` para aislamiento, `@settings(max_examples=100)`).

### Propiedad 1: Solo se puede recomendar a amigos confirmados

`# Feature: friend-recommendations, Property 1: solo se puede recomendar a amigos confirmados`

GIVEN un sender y un receiver que NO tienen una Amistad_Confirmada en la tabla `friendships`,
WHEN el sender intenta enviar una recomendación al receiver,
THEN el Sistema_Recomendaciones SHALL rechazar con error 403.

### Propiedad 2: No se puede duplicar una recomendación

`# Feature: friend-recommendations, Property 2: no se puede duplicar una recomendación`

GIVEN un sender que ya envió una recomendación de un media_item específico a un receiver,
WHEN el sender intenta enviar la misma recomendación (mismo sender, receiver, media_item),
THEN el Sistema_Recomendaciones SHALL rechazar con error 409.

### Propiedad 3: Unread count es consistente con las recomendaciones no leídas

`# Feature: friend-recommendations, Property 3: unread count consistente`

GIVEN un receiver con N recomendaciones donde K tienen `is_read=false`,
WHEN el receiver consulta el Unread_Count,
THEN el resultado SHALL ser exactamente K.

### Propiedad 4: Marcar como leída reduce el unread count en exactamente 1

`# Feature: friend-recommendations, Property 4: mark as read reduce count en 1`

GIVEN un receiver con Unread_Count = C (donde C > 0),
WHEN el receiver marca una recomendación no leída como leída,
THEN el nuevo Unread_Count SHALL ser C - 1.

### Propiedad 5: Mark-all-read pone el unread count a 0

`# Feature: friend-recommendations, Property 5: mark all read pone count a 0`

GIVEN un receiver con cualquier número de recomendaciones no leídas,
WHEN el receiver ejecuta mark-all-read,
THEN el Unread_Count SHALL ser 0.

### Propiedad 6: No se puede recomendar a uno mismo

`# Feature: friend-recommendations, Property 6: no se puede recomendar a uno mismo`

GIVEN un usuario que intenta enviarse una recomendación a sí mismo (sender_id == receiver_id),
WHEN se ejecuta la operación de envío,
THEN el Sistema_Recomendaciones SHALL rechazar con error 400.

**Archivos a crear:**
- `tests/test_property_recommendations.py`

## Referencias a Archivos Existentes

| Archivo | Relación |
|---------|----------|
| `backend/models/user.py` | Contiene `User`, `FriendRequest`, tabla `friendships` — las FKs de `Recommendation` apuntan a `User` |
| `backend/models/media.py` | Contiene `MediaItem`, `Base` — FK de `Recommendation` apunta a `MediaItem`, `Base` se usa como clase base |
| `backend/services/friend_service.py` | `FriendService` — se reutiliza la lógica de verificación de amistad o se consulta `friendships` directamente |
| `backend/dependencies.py` | `get_current_user` — dependency de autenticación para los endpoints |
| `backend/db.py` | `get_session` — dependency de sesión de base de datos |
| `backend/main.py` | Registro del nuevo router |
| `backend/schemas/social.py` | Referencia de formato para schemas sociales |
| `backend/routers/friends.py` | Referencia de patrón para routers sociales |
| `frontend/src/api/social.js` | Referencia de patrón para el API client, contiene `listFriends()` que usa el RecommendModal |
| `frontend/src/composables/useMedia.js` | Referencia de patrón para composables |
| `frontend/src/App.vue` | Se modifica para añadir el badge y el enlace de recomendaciones en el sidebar |
| `frontend/src/views/MediaDetailView.vue` | Se modifica para añadir el botón "Recomendar a amigo" |
| `frontend/src/router/index.js` | Se modifica para añadir la ruta `/recommendations` |
| `frontend/src/components/MediaCard.vue` | Referencia de patrón para componentes de media |
| `tests/conftest.py` | Fixtures compartidos para tests |
