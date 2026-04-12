# Requisitos — Login con username o email (IDEA-13)

## Contexto

Actualmente el login solo acepta email. Los usuarios deberían poder iniciar sesión con su nombre de usuario o con su email indistintamente.

## Requisitos funcionales

1. El endpoint `POST /api/auth/login` debe aceptar un campo `identifier` que puede ser un email o un username.
2. Si `identifier` contiene `@`, el backend busca al usuario por email. Si no, busca por username.
3. El mensaje de error en caso de credenciales inválidas sigue siendo genérico ("Invalid credentials") sin revelar si el usuario existe o no.
4. El frontend muestra un campo de texto con label "Email or username" y placeholder "you@example.com or username".
5. El input del login cambia de `type="email"` a `type="text"` para aceptar usernames.

## Requisitos no funcionales

6. No se requiere migración de base de datos (el modelo `User` ya tiene `email` y `username` como campos únicos).
7. Los tests existentes de auth se actualizan para usar `identifier` en vez de `email`.
8. Se añade un test nuevo que valida el login con username.

## Fuera de alcance

- Validación de que los usernames no contengan `@` (convención existente, no se fuerza en este cambio).
- Cambios en el flujo de registro (sigue pidiendo email + username + password por separado).
