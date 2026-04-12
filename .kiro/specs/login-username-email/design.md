# Diseño — Login con username o email (IDEA-13)

## Resumen

Permitir que el usuario inicie sesión con su nombre de usuario o con su email. El backend detecta automáticamente si el valor es un email (contiene `@`) o un username, y busca al usuario correspondiente.

## Cambios

### Backend

1. **`backend/schemas/auth.py`** — Renombrar campo `email` → `identifier` en `UserLogin`. Sin validación de formato email (acepta ambos).
2. **`backend/services/auth_service.py`** — En `login()`, si `identifier` contiene `@` buscar por `User.email`, si no buscar por `User.username`.
3. **`backend/routers/auth.py`** — Sin cambios (ya usa `UserLogin` genéricamente).

### Frontend

4. **`frontend/src/api/auth.js`** — Renombrar parámetro `email` → `identifier` en `login()`. Enviar `{ identifier, password }`.
5. **`frontend/src/composables/useAuth.js`** — Renombrar parámetro `email` → `identifier` en `login()`.
6. **`frontend/src/views/LoginView.vue`** — Cambiar label a "Email or username", placeholder a "you@example.com or username", input type a `text`.

## Detección email vs username

```python
if "@" in data.identifier:
    query = select(User).where(User.email == data.identifier)
else:
    query = select(User).where(User.username == data.identifier)
```

Simple, determinista, sin ambigüedad (los usernames no pueden contener `@` por convención).
