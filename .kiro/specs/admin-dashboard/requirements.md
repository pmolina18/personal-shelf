# Documento de Requisitos — Panel de Administración

## Introducción

Esta funcionalidad transforma el sistema de control de acceso de PersonalShelf y añade un panel de administración exclusivo para usuarios admin. Actualmente, el fichero `allowed_users` actúa como puerta de registro (solo los emails listados pueden registrarse). El cambio renombra este fichero a `allowed_admins` y lo redefine: el registro pasa a ser abierto para cualquier persona, y el fichero determina en tiempo de ejecución quién es administrador. Los administradores acceden a un dashboard con estadísticas globales de la aplicación: usuarios, contenido, actividad social y tendencias.

## Glosario

- **Sistema**: La aplicación PersonalShelf (backend FastAPI + frontend Vue 3).
- **Fichero_Allowed_Admins**: Fichero de texto plano en la raíz del proyecto (`allowed_admins`), con un email por línea. Los comentarios empiezan con `#`. Determina qué usuarios son administradores.
- **Servicio_Admin**: Servicio backend que lee el Fichero_Allowed_Admins y determina si un email corresponde a un administrador.
- **Usuario**: Persona registrada en el sistema con email, username y contraseña.
- **Admin**: Usuario cuyo email aparece en el Fichero_Allowed_Admins.
- **Panel_Admin**: Sección del frontend exclusiva para administradores que muestra estadísticas globales de la aplicación.
- **Servicio_Stats_Admin**: Servicio backend que calcula métricas agregadas a nivel de toda la aplicación (no por usuario individual).
- **Dependencia_Require_Admin**: Dependencia FastAPI que verifica que el usuario autenticado es administrador antes de permitir acceso a rutas protegidas.
- **Respuesta_Auth**: Objeto JSON devuelto por los endpoints de login y registro, que incluye tokens y datos del usuario.
- **Servicio_GitHub**: Servicio existente que crea Pull Requests en GitHub para solicitudes de acceso.

## Requisitos

### Requisito 1: Renombrar allowed_users a allowed_admins

**Historia de Usuario:** Como propietario de la aplicación, quiero que el fichero `allowed_users` se renombre a `allowed_admins` y cambie su semántica de "quién puede registrarse" a "quién es administrador", para que el registro sea abierto y el rol admin se determine por el fichero.

#### Criterios de Aceptación

1. THE Sistema SHALL utilizar un fichero llamado `allowed_admins` en la raíz del proyecto en lugar de `allowed_users`.
2. THE Sistema SHALL leer la variable de configuración `ALLOWED_ADMINS_PATH` para localizar el Fichero_Allowed_Admins.
3. WHEN el Fichero_Allowed_Admins contiene un email, THE Servicio_Admin SHALL identificar a ese Usuario como Admin (comparación case-insensitive, ignorando espacios y líneas de comentario).
4. WHEN el Fichero_Allowed_Admins no existe en disco, THE Servicio_Admin SHALL tratar a todos los usuarios como no-admin y registrar un error en el log.

### Requisito 2: Registro abierto (eliminar restricción de allowlist)

**Historia de Usuario:** Como visitante nuevo, quiero poder registrarme en PersonalShelf sin necesidad de estar en una lista de permitidos, para que cualquier persona pueda crear una cuenta.

#### Criterios de Aceptación

1. WHEN un visitante envía datos válidos de registro (email, username, contraseña), THE Sistema SHALL crear la cuenta sin verificar el Fichero_Allowed_Admins.
2. WHEN un email ya está registrado, THE Sistema SHALL devolver un error 409 con el mensaje "Email already registered".
3. WHEN un username ya está en uso, THE Sistema SHALL devolver un error 409 con el mensaje "Username already taken".
4. THE Sistema SHALL mantener el endpoint `/api/auth/request-access` funcional, actualizando las referencias internas para apuntar al fichero `allowed_admins` en lugar de `allowed_users`.

### Requisito 3: Campo is_admin en la respuesta de autenticación

**Historia de Usuario:** Como desarrollador frontend, quiero que la respuesta de login y registro incluya un campo `is_admin` booleano, para que el frontend pueda mostrar u ocultar la sección de administración sin llamadas API adicionales.

#### Criterios de Aceptación

1. WHEN un Usuario inicia sesión, THE Respuesta_Auth SHALL incluir un campo `is_admin` de tipo booleano dentro del objeto `user`.
2. WHEN un Usuario se registra, THE Respuesta_Auth SHALL incluir un campo `is_admin` de tipo booleano dentro del objeto `user`.
3. WHEN el email del Usuario aparece en el Fichero_Allowed_Admins, THE Sistema SHALL devolver `is_admin: true`.
4. WHEN el email del Usuario no aparece en el Fichero_Allowed_Admins, THE Sistema SHALL devolver `is_admin: false`.

### Requisito 4: Dependencia require_admin para protección de rutas backend

**Historia de Usuario:** Como propietario de la aplicación, quiero que las rutas de administración estén protegidas en el backend, para que solo los administradores puedan acceder a los datos globales.

#### Criterios de Aceptación

1. THE Dependencia_Require_Admin SHALL verificar que el usuario autenticado es Admin consultando el Servicio_Admin con el email del usuario.
2. WHEN un Usuario no-admin intenta acceder a una ruta protegida con Dependencia_Require_Admin, THE Sistema SHALL devolver un error 403 con el mensaje "Admin access required".
3. WHEN un Usuario admin accede a una ruta protegida con Dependencia_Require_Admin, THE Sistema SHALL permitir el acceso y continuar con la ejecución del endpoint.
4. THE Dependencia_Require_Admin SHALL depender de `get_current_user` para obtener el usuario autenticado antes de verificar el rol admin.

### Requisito 5: API de estadísticas globales de administración

**Historia de Usuario:** Como administrador, quiero acceder a un endpoint que devuelva estadísticas globales de la aplicación, para poder monitorizar la salud y actividad de PersonalShelf.

#### Criterios de Aceptación

1. THE Sistema SHALL exponer un endpoint `GET /api/admin/stats` protegido con Dependencia_Require_Admin.
2. WHEN un Admin solicita las estadísticas, THE Servicio_Stats_Admin SHALL devolver las siguientes métricas de usuarios:
   - Total de usuarios registrados.
   - Número de usuarios nuevos registrados en los últimos 7 días.
   - Número de usuarios que han añadido al menos un MediaItem en los últimos 7 días (usuarios activos).
3. WHEN un Admin solicita las estadísticas, THE Servicio_Stats_Admin SHALL devolver las siguientes métricas de contenido:
   - Total de MediaItems en toda la aplicación.
   - Número de MediaItems creados en los últimos 7 días.
   - Distribución de MediaItems por media_type (movie, book, series) con conteo de cada tipo.
   - Distribución de MediaItems por status (pending, in_progress, completed) con conteo de cada estado.
   - Rating promedio global de todos los MediaItems que tienen rating asignado.
4. WHEN un Admin solicita las estadísticas, THE Servicio_Stats_Admin SHALL devolver las siguientes métricas sociales:
   - Total de amistades activas (pares en la tabla friendships).
   - Total de solicitudes de amistad pendientes (FriendRequest con status "pending").
   - Total de tags únicos creados en la aplicación.
5. WHEN un Admin solicita las estadísticas, THE Servicio_Stats_Admin SHALL devolver un ranking de los 5 usuarios más activos en los últimos 7 días, ordenados por número de MediaItems creados, incluyendo username y conteo.
6. WHEN un Admin solicita las estadísticas, THE Servicio_Stats_Admin SHALL devolver un ranking de los 5 tags más utilizados en la aplicación, ordenados por número de MediaItems asociados, incluyendo nombre del tag y conteo.
7. WHEN un Admin solicita las estadísticas, THE Servicio_Stats_Admin SHALL devolver las últimas 10 acciones recientes en la aplicación (MediaItems creados o actualizados), incluyendo título, media_type, username del propietario y timestamp.

### Requisito 6: Protección de la sección admin en el frontend

**Historia de Usuario:** Como propietario de la aplicación, quiero que la sección de administración solo sea visible y accesible para usuarios admin en el frontend, para que los usuarios normales no vean opciones que no les corresponden.

#### Criterios de Aceptación

1. WHEN el usuario autenticado tiene `is_admin: true`, THE Sistema SHALL mostrar un enlace "Admin" en la barra lateral de navegación.
2. WHEN el usuario autenticado tiene `is_admin: false`, THE Sistema SHALL ocultar el enlace "Admin" de la barra lateral de navegación.
3. WHEN un usuario no-admin navega directamente a la ruta `/admin`, THE Sistema SHALL redirigir al usuario a la ruta `/catalog`.
4. THE Sistema SHALL almacenar el campo `is_admin` del usuario en el estado de autenticación del composable `useAuth`.
5. THE Sistema SHALL definir la ruta `/admin` con un meta campo `requiresAdmin: true` en el router.
6. WHEN el router detecta una navegación a una ruta con `requiresAdmin: true` y el usuario no es admin, THE Sistema SHALL redirigir a `/catalog`.

### Requisito 7: Vista del Panel de Administración en el frontend

**Historia de Usuario:** Como administrador, quiero ver un dashboard visual con estadísticas globales de la aplicación, para tener una visión rápida del estado y actividad de PersonalShelf.

#### Criterios de Aceptación

1. THE Panel_Admin SHALL mostrar una fila de tarjetas KPI con: total de usuarios, usuarios nuevos esta semana, total de MediaItems, MediaItems nuevos esta semana, y usuarios activos esta semana.
2. THE Panel_Admin SHALL mostrar un gráfico de barras horizontales con la distribución de MediaItems por tipo (movie, book, series).
3. THE Panel_Admin SHALL mostrar un gráfico de barras horizontales con la distribución de MediaItems por estado (pending, in_progress, completed).
4. THE Panel_Admin SHALL mostrar el rating promedio global con representación visual (barra de progreso sobre 10).
5. THE Panel_Admin SHALL mostrar una sección de métricas sociales con: total de amistades, solicitudes pendientes y tags únicos.
6. THE Panel_Admin SHALL mostrar una tabla con el ranking de los 5 usuarios más activos esta semana (username y número de items añadidos).
7. THE Panel_Admin SHALL mostrar una tabla con los 5 tags más populares (nombre y número de items asociados).
8. THE Panel_Admin SHALL mostrar un feed de actividad reciente con las últimas 10 acciones (título, tipo, usuario y fecha).
9. WHILE los datos se están cargando, THE Panel_Admin SHALL mostrar un indicador de carga con `role="status"`.
10. IF la llamada a la API falla, THEN THE Panel_Admin SHALL mostrar un mensaje de error con `role="alert"`.

### Requisito 8: Actualización del Servicio GitHub para allowed_admins

**Historia de Usuario:** Como propietario de la aplicación, quiero que el flujo de solicitud de acceso vía GitHub PR apunte al fichero `allowed_admins` en lugar de `allowed_users`, para que las solicitudes de acceso admin funcionen correctamente con el nuevo esquema.

#### Criterios de Aceptación

1. WHEN un usuario solicita acceso, THE Servicio_GitHub SHALL crear un PR que modifique el fichero `allowed_admins` en lugar de `allowed_users`.
2. WHEN el Servicio_GitHub construye el mensaje del commit, THE Servicio_GitHub SHALL referenciar `allowed_admins` en el texto del commit.
3. WHEN el Servicio_GitHub construye el cuerpo del PR, THE Servicio_GitHub SHALL describir que el email se añade a la lista de administradores.
