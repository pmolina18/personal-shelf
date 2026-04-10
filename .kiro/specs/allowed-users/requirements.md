# Documento de Requisitos — Allowed Users

## Introducción

Personal Shelf es una aplicación de seguimiento de medios desplegada en Render. Antes de abrir el registro al público general, el propietario quiere controlar quién puede registrarse mediante una lista de usuarios permitidos almacenada en un fichero del repositorio (`allowed_users`). Los usuarios que no estén en la lista podrán solicitar acceso, lo que generará automáticamente un Pull Request en GitHub contra dicho fichero. Cuando el propietario mergee el PR, el usuario quedará habilitado para registrarse en el siguiente despliegue.

## Glosario

- **Sistema_Auth**: El sistema de autenticación de Personal Shelf (AuthService, auth router, auth schemas).
- **Fichero_Allowed_Users**: Fichero de texto plano en la raíz del repositorio (`allowed_users`) que contiene una lista de emails permitidos, uno por línea.
- **Servicio_Allowed_Users**: Módulo backend encargado de leer y validar emails contra el Fichero_Allowed_Users.
- **Servicio_GitHub**: Módulo backend encargado de interactuar con la API de GitHub para crear Pull Requests.
- **Vista_Registro**: Componente frontend (`RegisterView.vue`) que gestiona el formulario de registro de nuevos usuarios.
- **Propietario**: Administrador del repositorio que aprueba o rechaza solicitudes de acceso mediante merge de PRs.
- **Solicitante**: Usuario no registrado que desea obtener acceso a la aplicación.

## Requisitos

### Requisito 1: Fichero de usuarios permitidos

**Historia de usuario:** Como Propietario, quiero mantener una lista de emails permitidos en un fichero del repositorio, para controlar quién puede registrarse en la aplicación.

#### Criterios de aceptación

1. THE Fichero_Allowed_Users SHALL almacenar una lista de direcciones de email, una por línea, en texto plano UTF-8.
2. THE Fichero_Allowed_Users SHALL ignorar líneas vacías y líneas que comiencen con el carácter `#` (comentarios).
3. THE Servicio_Allowed_Users SHALL leer el Fichero_Allowed_Users desde la ruta configurada al iniciar la validación.
4. THE Servicio_Allowed_Users SHALL realizar la comparación de emails de forma insensible a mayúsculas y minúsculas (case-insensitive).

### Requisito 2: Validación en el flujo de registro

**Historia de usuario:** Como Propietario, quiero que el sistema valide si un email está en la lista de permitidos antes de crear la cuenta, para impedir registros no autorizados.

#### Criterios de aceptación

1. WHEN un Solicitante envía una petición de registro, THE Sistema_Auth SHALL verificar que el email proporcionado existe en el Fichero_Allowed_Users antes de crear la cuenta de usuario.
2. WHEN el email del Solicitante existe en el Fichero_Allowed_Users, THE Sistema_Auth SHALL continuar con el flujo de registro existente (crear usuario, devolver tokens).
3. WHEN el email del Solicitante no existe en el Fichero_Allowed_Users, THE Sistema_Auth SHALL rechazar el registro con código HTTP 403 y el mensaje descriptivo "No estás en la lista de usuarios permitidos. Solicita acceso para ser añadido.".
4. THE Sistema_Auth SHALL ejecutar la validación contra el Fichero_Allowed_Users antes de comprobar duplicados de email o username en la base de datos.

### Requisito 3: Solicitud de acceso mediante Pull Request en GitHub

**Historia de usuario:** Como Solicitante, quiero poder solicitar acceso a la aplicación cuando mi email no está en la lista, para que el Propietario pueda aprobar mi solicitud mergeando un PR.

#### Criterios de aceptación

1. WHEN un Solicitante solicita acceso proporcionando su email, THE Servicio_GitHub SHALL crear un Pull Request en el repositorio de Personal Shelf que añada el email del Solicitante al final del Fichero_Allowed_Users.
2. THE Servicio_GitHub SHALL crear el PR en una rama con nombre único basado en el email del Solicitante (por ejemplo, `access-request/<email-sanitizado>`).
3. THE Servicio_GitHub SHALL asignar al PR un título descriptivo que incluya el email del Solicitante y una descripción que indique que es una solicitud de acceso automática.
4. WHEN el Servicio_GitHub crea el PR con éxito, THE Sistema_Auth SHALL responder con código HTTP 201 y un mensaje confirmando que la solicitud ha sido enviada.
5. IF la creación del PR falla por un error de la API de GitHub, THEN THE Sistema_Auth SHALL responder con código HTTP 502 y un mensaje indicando que la solicitud no pudo procesarse.
6. IF ya existe un PR abierto para el mismo email, THEN THE Servicio_GitHub SHALL informar al Solicitante de que ya tiene una solicitud pendiente en lugar de crear un PR duplicado.

### Requisito 4: Endpoint de solicitud de acceso

**Historia de usuario:** Como Solicitante, quiero un endpoint dedicado para solicitar acceso, para que el frontend pueda ofrecer esta opción cuando mi registro sea rechazado.

#### Criterios de aceptación

1. THE Sistema_Auth SHALL exponer un endpoint POST `/api/auth/request-access` que acepte un payload con el campo `email`.
2. WHEN el email proporcionado ya existe en el Fichero_Allowed_Users, THE Sistema_Auth SHALL responder con código HTTP 409 y un mensaje indicando que el email ya tiene acceso.
3. WHEN el email proporcionado es válido y no está en la lista, THE Sistema_Auth SHALL delegar la creación del PR al Servicio_GitHub.
4. THE Sistema_Auth SHALL validar que el campo `email` tiene formato de email válido antes de procesar la solicitud.

### Requisito 5: Interfaz de usuario para registro denegado y solicitud de acceso

**Historia de usuario:** Como Solicitante, quiero que la pantalla de registro me informe claramente cuando no tengo acceso y me ofrezca solicitar acceso, para no quedarme sin opciones.

#### Criterios de aceptación

1. WHEN el registro es rechazado con código HTTP 403, THE Vista_Registro SHALL mostrar el mensaje de error devuelto por el servidor en un elemento con `role="alert"`.
2. WHEN el registro es rechazado con código HTTP 403, THE Vista_Registro SHALL mostrar un botón "Solicitar acceso" que permita al Solicitante enviar una solicitud de acceso.
3. WHEN el Solicitante pulsa "Solicitar acceso", THE Vista_Registro SHALL enviar el email introducido al endpoint POST `/api/auth/request-access`.
4. WHEN la solicitud de acceso se envía con éxito, THE Vista_Registro SHALL mostrar un mensaje de confirmación indicando que la solicitud ha sido enviada y está pendiente de aprobación.
5. WHEN la solicitud de acceso falla, THE Vista_Registro SHALL mostrar el mensaje de error devuelto por el servidor.
6. WHILE la solicitud de acceso está en curso, THE Vista_Registro SHALL deshabilitar el botón "Solicitar acceso" y mostrar un indicador de carga.

### Requisito 6: Configuración de GitHub

**Historia de usuario:** Como Propietario, quiero configurar los datos de conexión a GitHub mediante variables de entorno, para mantener los secretos fuera del código fuente.

#### Criterios de aceptación

1. THE Servicio_GitHub SHALL leer el token de autenticación de GitHub desde la variable de entorno `GITHUB_TOKEN`.
2. THE Servicio_GitHub SHALL leer el nombre del repositorio (formato `owner/repo`) desde la variable de entorno `GITHUB_REPO`.
3. THE Servicio_GitHub SHALL leer el nombre de la rama principal (por defecto `main`) desde la variable de entorno `GITHUB_DEFAULT_BRANCH`.
4. IF la variable `GITHUB_TOKEN` o `GITHUB_REPO` no están configuradas, THEN THE Servicio_GitHub SHALL registrar un warning al iniciar la aplicación y el endpoint de solicitud de acceso SHALL responder con código HTTP 503 indicando que el servicio no está disponible.

### Requisito 7: Parseo y serialización del fichero de usuarios permitidos

**Historia de usuario:** Como desarrollador, quiero que el parseo y la serialización del fichero de usuarios permitidos sean consistentes, para evitar corrupción de datos al añadir emails mediante PRs.

#### Criterios de aceptación

1. THE Servicio_Allowed_Users SHALL parsear el Fichero_Allowed_Users extrayendo un email por línea, eliminando espacios en blanco al inicio y final de cada línea.
2. THE Servicio_Allowed_Users SHALL serializar la lista de emails de vuelta a texto plano con un email por línea, terminando el fichero con un salto de línea final.
3. FOR ALL listas válidas de emails, parsear y luego serializar y luego parsear de nuevo SHALL producir una lista equivalente a la original (propiedad round-trip).
4. THE Servicio_Allowed_Users SHALL preservar los comentarios (líneas que comienzan con `#`) y líneas vacías existentes al serializar el fichero con un nuevo email añadido.
