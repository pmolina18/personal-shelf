# Plan de Implementación: Panel de Administración

## Visión General

Transformar el sistema de control de acceso de PersonalShelf: renombrar `allowed_users` → `allowed_admins`, abrir el registro a cualquier persona, añadir campo `is_admin` en autenticación, proteger rutas admin con dependencia `require_admin`, crear endpoint de estadísticas globales y vista de dashboard admin en el frontend.

## Tareas

- [x] 1. Renombrar allowed_users a allowed_admins y actualizar config
  - [x] 1.1 Renombrar fichero y actualizar configuración
    - Renombrar el fichero `allowed_users` a `allowed_admins` en la raíz del proyecto
    - En `backend/config.py`: reemplazar `ALLOWED_USERS_PATH` por `ALLOWED_ADMINS_PATH` apuntando a `allowed_admins`
    - _Requisitos: 1.1, 1.2_

  - [x] 1.2 Crear `AllowedAdminsService` (renombrar desde `AllowedUsersService`)
    - Crear `backend/services/allowed_admins_service.py` con la clase `AllowedAdminsService`
    - Mismos métodos que `AllowedUsersService`: `is_admin(email)`, `parse()`, `serialize()`, `parse_preserving()`, `add_email()`
    - Usar `ALLOWED_ADMINS_PATH` de config
    - Renombrar `is_allowed` a `is_admin` (retorna `bool`, comparación case-insensitive)
    - Fichero no encontrado → retorna `False` y registra error en log
    - _Requisitos: 1.3, 1.4_

  - [ ]* 1.3 Test de propiedad: corrección del parsing de admins
    - **Propiedad 1: Corrección del parsing de admins**
    - Para cualquier contenido de fichero con emails, comentarios y líneas vacías, `is_admin(email)` retorna `True` sii el email aparece en una línea no vacía y no comentada (case-insensitive, sin espacios)
    - **Valida: Requisitos 1.3, 3.3, 3.4**

- [x] 2. Registro abierto y campo is_admin en autenticación
  - [x] 2.1 Modificar `AuthService` para registro abierto y añadir `is_admin`
    - En `backend/services/auth_service.py`:
      - Eliminar la verificación `is_allowed()` del método `register()` (cualquier persona puede registrarse)
      - Reemplazar import de `AllowedUsersService` por `AllowedAdminsService`
      - En `register()` y `login()`: consultar `AllowedAdminsService.is_admin(user.email)` y pasar el resultado a `UserResponse`
    - _Requisitos: 2.1, 3.1, 3.2_

  - [x] 2.2 Añadir campo `is_admin` al schema `UserResponse`
    - En `backend/schemas/auth.py`: añadir `is_admin: bool = False` a `UserResponse`
    - _Requisitos: 3.1, 3.2_

  - [ ]* 2.3 Test de propiedad: respuesta de autenticación incluye is_admin correcto
    - **Propiedad 2: Respuesta de autenticación incluye is_admin correcto**
    - Para cualquier usuario registrado, la respuesta de login/registro incluye `is_admin` cuyo valor coincide con `AllowedAdminsService.is_admin(user.email)`
    - **Valida: Requisitos 3.1, 3.2**

- [x] 3. Dependencia require_admin y router admin
  - [x] 3.1 Crear dependencia `require_admin`
    - En `backend/dependencies.py`: añadir `async def require_admin(user = Depends(get_current_user)) -> User`
    - Instanciar `AllowedAdminsService`, llamar `is_admin(user.email)`
    - Si `False` → `HTTPException(403, "Admin access required")`
    - Si `True` → retornar `User`
    - _Requisitos: 4.1, 4.2, 4.3, 4.4_

  - [ ]* 3.2 Test de propiedad: require_admin permite admins y rechaza no-admins
    - **Propiedad 3: require_admin permite admins y rechaza no-admins**
    - Para cualquier usuario autenticado, `require_admin` permite acceso si `is_admin(email)` es `True` y lanza HTTP 403 si es `False`
    - **Valida: Requisitos 4.1, 4.2, 4.3**

- [x] 4. Schemas y servicio de estadísticas admin
  - [x] 4.1 Crear schemas de admin stats
    - Crear `backend/schemas/admin.py` con: `TypeDistribution`, `StatusDistribution`, `TopUser`, `TopTag`, `RecentActivity`, `UserMetrics`, `ContentMetrics`, `SocialMetrics`, `AdminStatsResponse`
    - Usar `from __future__ import annotations`
    - _Requisitos: 5.2, 5.3, 5.4, 5.5, 5.6, 5.7_

  - [x] 4.2 Crear `AdminStatsService`
    - Crear `backend/services/admin_stats_service.py`
    - Método `async def get_admin_stats(session: AsyncSession) -> AdminStatsResponse`
    - Queries globales (sin filtro de `user_id`): métricas de usuarios, contenido, social, rankings, actividad reciente
    - `new_this_week` y `active_this_week`: usuarios/items con `created_at` en los últimos 7 días
    - `top_users`: 5 usuarios con más MediaItems creados en últimos 7 días
    - `top_tags`: 5 tags con más MediaItems asociados
    - `recent_activity`: 10 últimos MediaItems por `updated_at` descendente
    - _Requisitos: 5.2, 5.3, 5.4, 5.5, 5.6, 5.7_

  - [ ]* 4.3 Test de propiedad: métricas de usuarios correctas
    - **Propiedad 4: Métricas de usuarios correctas**
    - Para cualquier conjunto de usuarios con fechas variadas, `total`, `new_this_week` y `active_this_week` son correctos
    - **Valida: Requisito 5.2**

  - [ ]* 4.4 Test de propiedad: métricas de contenido correctas
    - **Propiedad 5: Métricas de contenido correctas**
    - Para cualquier conjunto de MediaItems, `total`, `new_this_week`, `by_type`, `by_status` y `avg_rating` son correctos
    - **Valida: Requisito 5.3**

  - [ ]* 4.5 Test de propiedad: métricas sociales correctas
    - **Propiedad 6: Métricas sociales correctas**
    - Para cualquier conjunto de amistades, solicitudes y tags, `total_friendships`, `pending_requests` y `unique_tags` son correctos
    - **Valida: Requisito 5.4**

  - [ ]* 4.6 Test de propiedad: ranking de usuarios más activos
    - **Propiedad 7: Ranking de usuarios más activos ordenado correctamente**
    - Máximo 5 entradas, ordenadas de mayor a menor por conteo, username y conteo correctos
    - **Valida: Requisito 5.5**

  - [ ]* 4.7 Test de propiedad: ranking de tags más utilizados
    - **Propiedad 8: Ranking de tags más utilizados ordenado correctamente**
    - Máximo 5 entradas, ordenadas de mayor a menor por número de MediaItems asociados
    - **Valida: Requisito 5.6**

  - [ ]* 4.8 Test de propiedad: actividad reciente ordenada
    - **Propiedad 9: Actividad reciente ordenada por timestamp descendente**
    - Máximo 10 entradas, ordenadas de más reciente a más antigua por `updated_at`
    - **Valida: Requisito 5.7**

- [x] 5. Checkpoint — Verificar tests backend
  - Asegurar que todos los tests pasan, preguntar al usuario si surgen dudas.

- [x] 6. Router admin y registro en main.py
  - [x] 6.1 Crear router admin
    - Crear `backend/routers/admin.py` con prefijo `/api/admin`
    - Endpoint `GET /stats` protegido con `Depends(require_admin)`
    - Delegar lógica a `AdminStatsService.get_admin_stats(session)`
    - _Requisitos: 5.1_

  - [x] 6.2 Registrar router admin en main.py
    - En `backend/main.py`: importar y registrar `admin_router` antes de los mounts estáticos
    - _Requisitos: 5.1_

  - [x] 6.3 Actualizar imports en auth router
    - En `backend/routers/auth.py`: reemplazar import de `AllowedUsersService` por `AllowedAdminsService`
    - Actualizar la instancia `_allowed_users_service` → `_allowed_admins_service`
    - _Requisitos: 1.1_

  - [x] 6.4 Actualizar `GitHubService` para apuntar a `allowed_admins`
    - En `backend/services/github_service.py`:
      - Cambiar `file_path = "allowed_users"` → `"allowed_admins"` en `create_access_request_pr()`
      - Actualizar mensaje de commit para referenciar `allowed_admins`
      - Actualizar cuerpo del PR para describir lista de administradores
      - Reemplazar import de `AllowedUsersService` por `AllowedAdminsService`
    - _Requisitos: 2.4, 8.1, 8.2, 8.3_

- [x] 7. Frontend — useAuth, router y sidebar admin
  - [x] 7.1 Modificar `useAuth.js` para incluir `is_admin`
    - Exponer `isAdmin` como `computed(() => user.value?.is_admin ?? false)`
    - `persistTokens()` ya almacena el objeto `user` completo (incluye `is_admin` del backend)
    - _Requisitos: 3.1, 3.2, 6.4_

  - [x] 7.2 Añadir ruta `/admin` y guard en el router
    - En `frontend/src/router/index.js`:
      - Añadir lazy import de `AdminView`
      - Añadir ruta `{ path: '/admin', name: 'admin', component: AdminView, meta: { requiresAdmin: true } }`
      - En `beforeEach`: si `to.meta.requiresAdmin` y usuario no es admin → redirigir a `/catalog`
    - _Requisitos: 6.3, 6.5, 6.6_

  - [x] 7.3 Añadir enlace "Admin" en sidebar de `App.vue`
    - Mostrar enlace solo si `isAdmin` es `true` (importar `isAdmin` de `useAuth`)
    - Posición: después del divider, junto a los enlaces de sección autenticada
    - Icono SVG apropiado (escudo o engranaje)
    - _Requisitos: 6.1, 6.2_

- [x] 8. Frontend — API client y vista AdminView
  - [x] 8.1 Crear `api/admin.js`
    - Crear `frontend/src/api/admin.js`
    - Función `getAdminStats()` → `GET /api/admin/stats` con Bearer token en header Authorization
    - _Requisitos: 5.1_

  - [x] 8.2 Crear `AdminView.vue`
    - Crear `frontend/src/views/AdminView.vue` con `<script setup>`
    - Llamar a `getAdminStats()` en `onMounted`
    - Mostrar KPIs: total usuarios, nuevos esta semana, total MediaItems, nuevos esta semana, usuarios activos
    - Gráficos de barras horizontales: distribución por tipo y por estado
    - Rating promedio global con barra de progreso sobre 10
    - Métricas sociales: amistades, solicitudes pendientes, tags únicos
    - Tabla ranking top 5 usuarios más activos
    - Tabla ranking top 5 tags más populares
    - Feed de actividad reciente (últimas 10 acciones)
    - Estado loading con `role="status"`, error con `role="alert"`
    - Estilos scoped siguiendo design tokens del proyecto
    - _Requisitos: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9, 7.10_

- [x] 9. Checkpoint — Verificar integración completa
  - Asegurar que todos los tests pasan, preguntar al usuario si surgen dudas.

- [x] 10. Limpieza y eliminación de fichero antiguo
  - [x] 10.1 Eliminar `AllowedUsersService` antiguo
    - Eliminar `backend/services/allowed_users_service.py` (ya reemplazado por `allowed_admins_service.py`)
    - Verificar que ningún import referencia al fichero antiguo
    - _Requisitos: 1.1_

- [x] 11. Checkpoint final — Verificar que todo funciona
  - Asegurar que todos los tests pasan, preguntar al usuario si surgen dudas.

## Notas

- Las tareas marcadas con `*` son opcionales y pueden omitirse para un MVP más rápido.
- Cada tarea referencia requisitos específicos para trazabilidad.
- Los checkpoints aseguran validación incremental.
- Los tests de propiedades validan propiedades universales de corrección definidas en el diseño.
- Los tests unitarios validan ejemplos específicos y casos borde.
- Patrón de tests de propiedades: usar `_fresh_session()` con SQLite in-memory, `@settings(max_examples=100, deadline=None)`, funciones sync `def test_*` con `asyncio.run()` interno.
