# Tareas — Login con username o email (IDEA-13)

## Tarea 1: Backend — Schema + Service

- [x] 1.1 Actualizar `UserLogin` en `backend/schemas/auth.py`: renombrar `email` → `identifier`
- [x] 1.2 Actualizar `AuthService.login()` en `backend/services/auth_service.py`: detectar `@` y buscar por email o username
- [x] 1.3 Actualizar docstrings del router en `backend/routers/auth.py`

## Tarea 2: Frontend — API + Vista

- [x] 2.1 Actualizar `login()` en `frontend/src/api/auth.js`: enviar `identifier` en vez de `email`
- [x] 2.2 Actualizar `login()` en `frontend/src/composables/useAuth.js`: renombrar parámetro
- [x] 2.3 Actualizar `LoginView.vue`: label, placeholder, tipo de input, variable reactiva
