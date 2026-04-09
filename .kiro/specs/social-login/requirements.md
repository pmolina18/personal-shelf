# Documento de Requisitos — Social Login

## Introducción

Personal Shelf es actualmente una aplicación mono-usuario para catalogar películas, libros y series. Esta feature transforma la aplicación en una plataforma multi-usuario con capacidades sociales: registro e inicio de sesión, propiedad de items por usuario (multi-tenancy), sistema de amistades y un feed social donde cada usuario puede ver las colecciones de sus amigos.

La propuesta técnica es:
- **Autenticación**: registro/login con email y contraseña, usando JWT (access + refresh tokens) almacenados en el frontend.
- **Multi-tenancy**: cada `MediaItem` pertenece a un `User` mediante una FK `user_id`. Las queries existentes se filtran automáticamente por el usuario autenticado.
- **Social**: modelo de amistad bidireccional con solicitudes (enviar, aceptar, rechazar). Feed social que muestra la actividad reciente de los amigos.
- **Privacidad**: la colección de un usuario solo es visible para sus amigos confirmados.

## Glosario

- **Sistema_Auth**: Subsistema de autenticación responsable del registro, login y gestión de tokens JWT.
- **Sistema_Usuarios**: Subsistema que gestiona los perfiles de usuario y la propiedad de media items.
- **Sistema_Amistades**: Subsistema que gestiona las relaciones de amistad entre usuarios (solicitudes, aceptación, rechazo, eliminación).
- **Sistema_Feed**: Subsistema que genera y presenta el feed social con la actividad de los amigos.
- **Usuario**: Persona registrada en la aplicación con email, nombre de usuario y contraseña.
- **Token_Acceso**: JWT de corta duración (30 minutos) usado para autenticar peticiones a la API.
- **Token_Refresco**: JWT de larga duración (7 días) usado para obtener nuevos Token_Acceso sin re-login.
- **Solicitud_Amistad**: Petición enviada de un Usuario a otro para establecer una relación de amistad bidireccional.
- **Amistad**: Relación bidireccional confirmada entre dos Usuarios que permite ver mutuamente sus colecciones.
- **Feed_Social**: Vista cronológica de la actividad reciente (items añadidos, completados, puntuados) de los amigos del Usuario autenticado.

## Requisitos

### Requisito 1: Registro de usuario

**User Story:** Como visitante, quiero crear una cuenta con email y contraseña, para poder tener mi propia colección de media items.

#### Criterios de Aceptación

1. WHEN un visitante envía un formulario de registro con email, nombre de usuario y contraseña válidos, THE Sistema_Auth SHALL crear una cuenta de Usuario y devolver un Token_Acceso y un Token_Refresco.
2. WHEN un visitante intenta registrarse con un email que ya existe en la base de datos, THE Sistema_Auth SHALL rechazar el registro con un error 409 indicando que el email ya está en uso.
3. WHEN un visitante intenta registrarse con un nombre de usuario que ya existe en la base de datos, THE Sistema_Auth SHALL rechazar el registro con un error 409 indicando que el nombre de usuario ya está en uso.
4. THE Sistema_Auth SHALL exigir que la contraseña tenga un mínimo de 8 caracteres.
5. THE Sistema_Auth SHALL almacenar la contraseña usando un hash bcrypt, sin almacenar la contraseña en texto plano.
6. WHEN un visitante envía un formulario de registro con campos vacíos o formato de email inválido, THE Sistema_Auth SHALL rechazar el registro con un error 422 indicando los campos inválidos.

### Requisito 2: Inicio de sesión

**User Story:** Como usuario registrado, quiero iniciar sesión con mi email y contraseña, para acceder a mi colección personal.

#### Criterios de Aceptación

1. WHEN un Usuario envía credenciales válidas (email y contraseña), THE Sistema_Auth SHALL devolver un Token_Acceso y un Token_Refresco.
2. WHEN un Usuario envía credenciales inválidas, THE Sistema_Auth SHALL rechazar el login con un error 401 sin revelar si el email o la contraseña son incorrectos.
3. THE Sistema_Auth SHALL generar Token_Acceso con una expiración de 30 minutos.
4. THE Sistema_Auth SHALL generar Token_Refresco con una expiración de 7 días.

### Requisito 3: Refresco de tokens

**User Story:** Como usuario autenticado, quiero que mi sesión se mantenga activa sin tener que re-introducir mis credenciales frecuentemente.

#### Criterios de Aceptación

1. WHEN un Usuario envía un Token_Refresco válido al endpoint de refresco, THE Sistema_Auth SHALL devolver un nuevo Token_Acceso y un nuevo Token_Refresco.
2. WHEN un Usuario envía un Token_Refresco expirado o inválido, THE Sistema_Auth SHALL rechazar la petición con un error 401.
3. WHEN un Token_Refresco se usa para obtener nuevos tokens, THE Sistema_Auth SHALL invalidar el Token_Refresco anterior para evitar reutilización.

### Requisito 4: Protección de rutas API

**User Story:** Como usuario autenticado, quiero que solo yo pueda acceder a mis datos, para que mi colección esté protegida.

#### Criterios de Aceptación

1. THE Sistema_Auth SHALL requerir un Token_Acceso válido en la cabecera Authorization (formato Bearer) para todos los endpoints de la API excepto registro, login y refresco de tokens.
2. WHEN una petición llega sin Token_Acceso o con un token expirado, THE Sistema_Auth SHALL rechazar la petición con un error 401.
3. WHEN una petición llega con un Token_Acceso válido, THE Sistema_Auth SHALL inyectar el Usuario autenticado en el contexto de la petición para uso de los servicios downstream.

### Requisito 5: Multi-tenancy de media items

**User Story:** Como usuario, quiero que mis media items sean míos y no se mezclen con los de otros usuarios.

#### Criterios de Aceptación

1. WHEN un Usuario crea un media item, THE Sistema_Usuarios SHALL asociar automáticamente el item al Usuario autenticado mediante un campo user_id.
2. WHEN un Usuario lista sus media items, THE Sistema_Usuarios SHALL devolver exclusivamente los items que pertenecen a ese Usuario.
3. WHEN un Usuario intenta acceder, modificar o eliminar un media item que pertenece a otro Usuario, THE Sistema_Usuarios SHALL rechazar la operación con un error 403.
4. THE Sistema_Usuarios SHALL aplicar el filtro de user_id en todas las operaciones de lectura, actualización y eliminación de media items.
5. THE Sistema_Usuarios SHALL aplicar el filtro de user_id en los endpoints de estadísticas, mostrando solo las estadísticas de los items del Usuario autenticado.
6. THE Sistema_Usuarios SHALL aplicar el filtro de user_id en los endpoints de exportación, exportando solo los items del Usuario autenticado.

### Requisito 6: Solicitudes de amistad

**User Story:** Como usuario, quiero enviar solicitudes de amistad a otros usuarios, para poder ver sus colecciones.

#### Criterios de Aceptación

1. WHEN un Usuario envía una solicitud de amistad a otro Usuario usando su nombre de usuario, THE Sistema_Amistades SHALL crear una Solicitud_Amistad con estado "pending".
2. WHEN un Usuario intenta enviar una solicitud de amistad a sí mismo, THE Sistema_Amistades SHALL rechazar la operación con un error 400.
3. WHEN un Usuario intenta enviar una solicitud de amistad a un Usuario con el que ya tiene una Amistad confirmada, THE Sistema_Amistades SHALL rechazar la operación con un error 409.
4. WHEN un Usuario intenta enviar una solicitud de amistad a un Usuario al que ya le envió una solicitud pendiente, THE Sistema_Amistades SHALL rechazar la operación con un error 409.
5. WHEN un Usuario busca otros usuarios por nombre de usuario, THE Sistema_Amistades SHALL devolver una lista de Usuarios cuyo nombre de usuario coincida parcialmente con el término de búsqueda (case-insensitive).

### Requisito 7: Gestión de solicitudes de amistad

**User Story:** Como usuario, quiero aceptar o rechazar solicitudes de amistad que recibo, para controlar quién puede ver mi colección.

#### Criterios de Aceptación

1. WHEN un Usuario acepta una Solicitud_Amistad, THE Sistema_Amistades SHALL crear una Amistad bidireccional entre ambos Usuarios y eliminar la solicitud.
2. WHEN un Usuario rechaza una Solicitud_Amistad, THE Sistema_Amistades SHALL eliminar la solicitud sin crear una Amistad.
3. WHEN un Usuario consulta sus solicitudes pendientes, THE Sistema_Amistades SHALL devolver la lista de Solicitudes_Amistad recibidas con estado "pending", incluyendo el nombre de usuario del remitente.
4. WHEN un Usuario intenta aceptar o rechazar una Solicitud_Amistad que no está dirigida a ese Usuario, THE Sistema_Amistades SHALL rechazar la operación con un error 403.

### Requisito 8: Eliminación de amistades

**User Story:** Como usuario, quiero poder eliminar a un amigo, para dejar de compartir mi colección con esa persona.

#### Criterios de Aceptación

1. WHEN un Usuario elimina una Amistad, THE Sistema_Amistades SHALL eliminar la relación bidireccional entre ambos Usuarios.
2. WHEN un Usuario elimina una Amistad, THE Sistema_Amistades SHALL dejar de mostrar los items de cada Usuario al otro en el Feed_Social.
3. WHEN un Usuario consulta su lista de amigos, THE Sistema_Amistades SHALL devolver la lista de Usuarios con los que tiene una Amistad confirmada, incluyendo nombre de usuario de cada amigo.

### Requisito 9: Feed social

**User Story:** Como usuario, quiero ver un feed con la actividad reciente de mis amigos, para descubrir qué están viendo, leyendo o completando.

#### Criterios de Aceptación

1. WHEN un Usuario accede al Feed_Social, THE Sistema_Feed SHALL mostrar los media items añadidos, completados o puntuados recientemente por los amigos del Usuario, ordenados cronológicamente (más recientes primero).
2. THE Sistema_Feed SHALL incluir en cada entrada del feed: el nombre de usuario del amigo, el título del media item, el tipo de media, la acción realizada (añadido, completado, puntuado) y la fecha de la acción.
3. THE Sistema_Feed SHALL paginar los resultados del feed con un máximo de 20 entradas por página.
4. WHEN un Usuario no tiene amigos, THE Sistema_Feed SHALL mostrar un mensaje indicando que el feed está vacío y sugiriendo buscar amigos.
5. THE Sistema_Feed SHALL mostrar solo la actividad de los últimos 30 días.

### Requisito 10: Visualización de la colección de un amigo

**User Story:** Como usuario, quiero poder ver la colección completa de un amigo, para explorar sus películas, libros y series.

#### Criterios de Aceptación

1. WHEN un Usuario accede al perfil de un amigo confirmado, THE Sistema_Feed SHALL mostrar la colección de media items de ese amigo con los mismos filtros disponibles que en el catálogo propio (tipo, estado, búsqueda, tag).
2. WHEN un Usuario intenta acceder a la colección de un Usuario que no es su amigo, THE Sistema_Feed SHALL rechazar la petición con un error 403.
3. THE Sistema_Feed SHALL mostrar la colección del amigo en modo solo lectura, sin permitir modificaciones.

### Requisito 11: Protección de rutas en el frontend

**User Story:** Como usuario, quiero que la aplicación me redirija al login si no estoy autenticado, para una experiencia fluida.

#### Criterios de Aceptación

1. WHEN un Usuario no autenticado intenta acceder a una ruta protegida, THE Sistema_Auth SHALL redirigir al Usuario a la página de login.
2. WHEN un Usuario autenticado accede a la página de login o registro, THE Sistema_Auth SHALL redirigir al Usuario a la página principal del catálogo.
3. THE Sistema_Auth SHALL almacenar el Token_Acceso y el Token_Refresco en localStorage del navegador.
4. WHEN el Token_Acceso expira durante una petición, THE Sistema_Auth SHALL intentar refrescar el token automáticamente usando el Token_Refresco antes de reintentar la petición original.
5. IF el refresco de token falla, THEN THE Sistema_Auth SHALL cerrar la sesión del Usuario y redirigir a la página de login.

### Requisito 12: Migración de datos existentes

**User Story:** Como desarrollador, quiero que los datos existentes se migren correctamente al nuevo esquema multi-usuario.

#### Criterios de Aceptación

1. WHEN se ejecuta la migración de Alembic, THE Sistema_Usuarios SHALL crear la tabla de usuarios, la tabla de amistades y la tabla de solicitudes de amistad.
2. WHEN se ejecuta la migración de Alembic, THE Sistema_Usuarios SHALL añadir la columna user_id a la tabla media_items con una FK hacia la tabla de usuarios.
3. THE Sistema_Usuarios SHALL asignar todos los media items existentes (sin user_id) a un usuario "legacy" creado automáticamente durante la migración.
