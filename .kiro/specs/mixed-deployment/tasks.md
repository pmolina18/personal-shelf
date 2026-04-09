# Plan de Implementación: Mixed Deployment

## Visión General

Preparar Personal Shelf para despliegue mixto en producción: Vercel (frontend), Render (backend) y Neon.dev (PostgreSQL). Los cambios son principalmente de configuración: URL base dinámica en el frontend, CORS configurable, SSL para Neon.dev, health check, manejo de imágenes en filesystem efímero, y archivos de despliegue (render.yaml, vercel.json). Todo debe mantener compatibilidad total con el entorno de desarrollo local.

## Tareas

- [x] 1. Configuración del backend para producción
  - [x] 1.1 Actualizar config.py con variables de entorno para producción
    - Añadir lectura de `ALLOWED_ORIGINS` desde `os.getenv` (string separado por comas, default `None`)
    - Añadir detección de SSL para Neon.dev: si `DATABASE_URL` contiene `.neon.tech`, asegurar que `ssl=require` está presente en los connect_args del engine
    - Verificar que `JWT_SECRET_KEY` ya se lee desde entorno (ya existe)
    - _Requisitos: 3.1, 4.1, 4.2, 4.3, 4.4, 6.4_

  - [x] 1.2 Actualizar db.py para soportar SSL con Neon.dev
    - Modificar la creación del engine en `backend/db.py` para pasar `connect_args={"ssl": "require"}` cuando la URL contenga `.neon.tech`
    - Mantener el comportamiento actual (sin SSL) para conexiones locales
    - _Requisitos: 4.3, 4.4, 11.3_

  - [x] 1.3 Configurar CORS dinámico en main.py
    - Modificar `backend/main.py`: leer `ALLOWED_ORIGINS` desde config, si está definida parsear como lista separada por comas, si no usar `["*"]`
    - Asegurar que se permiten las cabeceras `Authorization` y `Content-Type`
    - Asegurar que se permiten los métodos GET, POST, PUT, PATCH, DELETE
    - _Requisitos: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [x] 1.4 Implementar endpoint de health check
    - Crear `GET /api/health` en un nuevo router o directamente en `main.py`
    - Devolver `{"status": "ok"}` con HTTP 200 si la DB responde a `SELECT 1`
    - Devolver `{"status": "unhealthy", "detail": "database connection failed"}` con HTTP 503 si la conexión falla
    - No requerir autenticación
    - _Requisitos: 8.1, 8.2, 8.3, 8.4_

  - [x] 1.5 Escribir tests unitarios para health check y CORS
    - Test: GET /api/health devuelve 200 con DB activa
    - Test: GET /api/health devuelve 503 cuando la DB no responde
    - Test: CORS permite orígenes configurados cuando `ALLOWED_ORIGINS` está definida
    - Test: CORS permite todos los orígenes cuando `ALLOWED_ORIGINS` no está definida
    - _Requisitos: 3.2, 3.3, 8.1, 8.2, 8.3, 8.4_

- [x] 2. Manejo de imágenes en filesystem efímero
  - [x] 2.1 Hacer resiliente el servicio de imágenes
    - Modificar `backend/services/image_service.py` o el endpoint de imagen: cuando `image_path` referencia un archivo que no existe en disco, devolver 404 controlado en lugar de error 500
    - Si `TMDB_API_KEY` está configurada y la imagen no existe, intentar re-descargarla bajo demanda antes de devolver 404
    - _Requisitos: 7.1, 7.3, 7.4_

  - [x] 2.2 Escribir tests unitarios para imágenes faltantes
    - Test: imagen referenciada pero inexistente devuelve 404 (no 500)
    - Test: con TMDB_API_KEY configurada, intenta re-descarga bajo demanda
    - _Requisitos: 7.1, 7.3, 7.4_

- [x] 3. Checkpoint — Verificar cambios de backend
  - Asegurar que todos los tests pasan, preguntar al usuario si surgen dudas.

- [x] 4. Configuración dinámica del frontend
  - [x] 4.1 Actualizar el cliente API con URL base configurable
    - Modificar `frontend/src/api/media.js`: leer `BASE_URL` desde `import.meta.env.VITE_API_BASE_URL` con fallback a `/api`
    - Construir URLs concatenando base + ruta sin duplicar barras
    - _Requisitos: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [x] 4.2 Actualizar URLs de imágenes con base configurable
    - Modificar `frontend/src/api/media.js` o los componentes que construyen URLs de imagen: leer base desde `import.meta.env.VITE_IMAGES_BASE_URL` con fallback a `/images`
    - _Requisitos: 2.1, 2.2, 2.3, 2.4_

  - [x] 4.3 Escribir tests unitarios para construcción de URLs
    - Test: sin variables de entorno, usa `/api` y `/images` como base
    - Test: con variables definidas, usa las URLs absolutas configuradas
    - Test: no duplica barras al concatenar base + ruta
    - _Requisitos: 1.4, 1.5, 2.4_

- [x] 5. Migraciones compatibles con Neon.dev
  - [x] 5.1 Verificar que Alembic env.py lee DATABASE_URL del entorno
    - Confirmar que `backend/migrations/env.py` ya usa `DATABASE_URL` de `backend.config` (que lee del entorno)
    - Si es necesario, ajustar para que soporte conexiones SSL (Neon.dev requiere `sslmode=require`)
    - _Requisitos: 5.1, 5.2, 5.3, 11.4_

- [x] 6. Archivos de configuración de despliegue
  - [x] 6.1 Crear render.yaml para el backend
    - Crear `render.yaml` en la raíz del proyecto con: tipo `web`, runtime `python`, build command `pip install -r backend/requirements.txt`, start command `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
    - Definir variables de entorno como referencias (`DATABASE_URL`, `ALLOWED_ORIGINS`, `JWT_SECRET_KEY`, `TMDB_API_KEY`)
    - Configurar health check path como `/api/health`
    - _Requisitos: 9.1, 9.2, 9.3, 9.4_

  - [x] 6.2 Crear vercel.json para el frontend
    - Crear `frontend/vercel.json` con: build command `npm run build`, output directory `dist`
    - Añadir regla de rewrite `"source": "/(.*)", "destination": "/index.html"` para Vue Router en modo history
    - Documentar las variables `VITE_API_BASE_URL` y `VITE_IMAGES_BASE_URL` que deben configurarse en Vercel
    - _Requisitos: 10.1, 10.2, 10.3, 10.4, 10.5_

  - [x] 6.3 Crear archivos .env.example
    - Crear `.env.example` en la raíz con: `DATABASE_URL`, `ALLOWED_ORIGINS`, `JWT_SECRET_KEY`, `TMDB_API_KEY`, `VITE_API_BASE_URL`, `VITE_IMAGES_BASE_URL`
    - Crear `frontend/.env.example` con: `VITE_API_BASE_URL`, `VITE_IMAGES_BASE_URL`
    - _Requisitos: 6.1, 6.2, 6.3_

- [x] 7. Checkpoint — Verificar compatibilidad dual
  - Asegurar que todos los tests pasan tanto con configuración local (sin variables de entorno de producción) como con las nuevas variables.
  - Verificar que el proxy de Vite sigue funcionando para desarrollo local.
  - Preguntar al usuario si surgen dudas.
  - _Requisitos: 11.1, 11.2, 11.3, 11.4_

## Notas

- Las tareas marcadas con `*` son opcionales y pueden omitirse para un MVP más rápido
- Cada tarea referencia requisitos específicos para trazabilidad
- Los checkpoints aseguran validación incremental
- No hay tests de propiedad (Hypothesis) en este spec porque es configuración de despliegue, no lógica de negocio compleja
- Los tests unitarios opcionales validan la correctitud de la configuración dinámica
- Todos los cambios mantienen compatibilidad total con el entorno de desarrollo local
