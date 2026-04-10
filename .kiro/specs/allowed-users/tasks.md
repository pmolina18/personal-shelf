# Plan de Implementación: Allowed Users

## Resumen

Implementar el control de acceso al registro mediante un fichero `allowed_users`, con solicitud de acceso vía Pull Request en GitHub. Se crean dos servicios nuevos (`AllowedUsersService`, `GitHubService`), un endpoint de solicitud de acceso, modificaciones al flujo de registro existente, y cambios en el frontend para manejar el rechazo 403 y ofrecer la opción de solicitar acceso.

## Tareas

- [x] 1. Configuración y schemas base
  - [x] 1.1 Añadir variables de configuración en `backend/config.py`
    - Añadir `ALLOWED_USERS_PATH`, `GITHUB_TOKEN`, `GITHUB_REPO`, `GITHUB_DEFAULT_BRANCH`
    - _Requisitos: 6.1, 6.2, 6.3_
  - [x] 1.2 Crear schemas `AccessRequest` y `AccessRequestResponse` en `backend/schemas/auth.py`
    - `AccessRequest` con campo `email` validado con regex
    - `AccessRequestResponse` con campos `message` y `pr_url: str | None`
    - _Requisitos: 4.1, 4.4_

- [x] 2. Implementar AllowedUsersService
  - [x] 2.1 Crear `backend/services/allowed_users_service.py`
    - Implementar `__init__`, `is_allowed`, `parse`, `serialize`, `parse_preserving`, `add_email`
    - Lectura del fichero desde `ALLOWED_USERS_PATH`, comparación case-insensitive
    - Ignorar líneas vacías y comentarios (`#`) en `parse`, preservarlos en `parse_preserving`
    - _Requisitos: 1.1, 1.2, 1.3, 1.4, 7.1, 7.2, 7.3, 7.4_
  - [ ]* 2.2 Test de propiedad: corrección del parseo
    - **Propiedad 1: Corrección del parseo**
    - **Valida: Requisitos 1.2, 7.1**
  - [ ]* 2.3 Test de propiedad: comparación case-insensitive
    - **Propiedad 2: Comparación case-insensitive de emails**
    - **Valida: Requisito 1.4**
  - [ ]* 2.4 Test de propiedad: round-trip parseo-serialización-parseo
    - **Propiedad 4: Round-trip parseo-serialización-parseo**
    - **Valida: Requisito 7.3**
  - [ ]* 2.5 Test de propiedad: preservación de comentarios y líneas vacías al añadir email
    - **Propiedad 5: Preservación de comentarios y líneas vacías al añadir email**
    - **Valida: Requisito 7.4**

- [x] 3. Checkpoint — Verificar AllowedUsersService
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Implementar GitHubService
  - [x] 4.1 Crear `backend/services/github_service.py`
    - Implementar clase async `GitHubService` con httpx
    - Métodos: `is_configured`, `create_access_request_pr`, `_check_existing_pr`, `_get_file_content`, `_create_or_update_file`, `_create_branch`, `_create_pull_request`
    - Verificación de PR duplicado, creación de rama con nombre sanitizado, creación del PR
    - Warning en log si `GITHUB_TOKEN` o `GITHUB_REPO` no están configurados
    - _Requisitos: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 6.1, 6.2, 6.3, 6.4_
  - [ ]* 4.2 Test de propiedad: derivación de metadatos del PR desde email
    - **Propiedad 6: Derivación de metadatos del PR desde email**
    - **Valida: Requisitos 3.2, 3.3**

- [x] 5. Integrar validación en el flujo de registro
  - [x] 5.1 Modificar `AuthService.register()` en `backend/services/auth_service.py`
    - Añadir validación contra `AllowedUsersService.is_allowed()` como primer paso, antes de comprobar duplicados
    - Lanzar `HTTPException(403)` con mensaje descriptivo si el email no está permitido
    - _Requisitos: 2.1, 2.2, 2.3, 2.4_
  - [ ]* 5.2 Test de propiedad: registro condicionado por lista de permitidos
    - **Propiedad 3: Registro condicionado por lista de permitidos**
    - **Valida: Requisitos 2.1, 2.2, 2.3**

- [x] 6. Implementar endpoint de solicitud de acceso
  - [x] 6.1 Añadir `POST /api/auth/request-access` en `backend/routers/auth.py`
    - Verificar que GitHub está configurado (503 si no)
    - Verificar que el email no está ya en la lista (409 si sí)
    - Delegar creación del PR a `GitHubService`
    - Responder 201 con mensaje de confirmación y URL del PR
    - Manejar errores de GitHub API (502)
    - _Requisitos: 4.1, 4.2, 4.3, 4.4, 3.4, 3.5, 6.4_
  - [ ]* 6.2 Test de propiedad: request-access rechaza emails ya permitidos
    - **Propiedad 7: Request-access rechaza emails ya permitidos**
    - **Valida: Requisito 4.2**
  - [ ]* 6.3 Test de propiedad: validación de formato de email
    - **Propiedad 8: Validación de formato de email**
    - **Valida: Requisito 4.4**

- [x] 7. Checkpoint — Verificar backend completo
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Crear fichero `allowed_users` en la raíz del repositorio
  - Crear fichero `allowed_users` con cabecera de comentarios y al menos un email de ejemplo
  - _Requisitos: 1.1, 1.2_

- [x] 9. Implementar cambios en el frontend
  - [x] 9.1 Añadir función `requestAccess(email)` en `frontend/src/api/auth.js`
    - POST a `/auth/request-access` con `{ email }`
    - _Requisitos: 5.3_
  - [x] 9.2 Modificar `frontend/src/views/RegisterView.vue`
    - Detectar respuesta 403 y activar estado `accessDenied`
    - Mostrar mensaje de error con `role="alert"`
    - Mostrar botón "Solicitar acceso" cuando `accessDenied` es true
    - Implementar flujo de solicitud: loading, éxito, error
    - Deshabilitar botón y mostrar indicador de carga mientras la solicitud está en curso
    - Mostrar mensaje de confirmación tras envío exitoso
    - _Requisitos: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_
  - [ ]* 9.3 Tests unitarios para RegisterView (flujo de acceso denegado)
    - Verificar que se muestra el botón "Solicitar acceso" tras 403
    - Verificar mensaje de confirmación tras solicitud exitosa
    - Verificar manejo de errores en solicitud fallida
    - _Requisitos: 5.1, 5.2, 5.4, 5.5, 5.6_

- [x] 10. Checkpoint final — Verificar integración completa
  - Ensure all tests pass, ask the user if questions arise.

## Notas

- Las tareas marcadas con `*` son opcionales y pueden omitirse para un MVP más rápido
- Cada tarea referencia requisitos específicos para trazabilidad
- Los tests de propiedades usan Hypothesis con `@settings(max_examples=100, deadline=None)` y el patrón `sync def` + `asyncio.run()` del proyecto
- Los tests de propiedades van en `tests/test_property_allowed_users.py`
- Los tests de frontend van en `frontend/src/__tests__/views/RegisterView.test.js`
- httpx ya es dependencia del proyecto, se usa para las llamadas a GitHub API
