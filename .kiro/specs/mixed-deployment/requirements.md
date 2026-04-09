# Documento de Requisitos — Mixed Deployment

## Introducción

Personal Shelf es una aplicación web personal para catalogar películas, libros y series. Actualmente funciona exclusivamente en entorno local de desarrollo. Esta feature prepara el proyecto para un despliegue mixto en producción usando servicios gratuitos:

- **Frontend** (Vue 3 SPA): desplegado como sitio estático en Vercel (CDN, sin cold starts, free tier).
- **Backend** (FastAPI + Uvicorn): desplegado como web service en Render (free tier).
- **Base de datos** (PostgreSQL): alojada en Neon.dev (free tier permanente, 0.5 GB, sin expiración).

El desafío principal es que frontend y backend estarán en dominios distintos (cross-origin), el filesystem de Render es efímero (las imágenes locales se pierden en cada redeploy), y la configuración debe soportar tanto desarrollo local como producción sin conflictos.

## Glosario

- **Sistema_Build_Frontend**: Subsistema de Vite responsable de compilar la SPA de Vue 3 y generar los assets estáticos en `frontend/dist/`.
- **Cliente_API**: Módulo `frontend/src/api/media.js` que encapsula todas las llamadas HTTP al backend usando fetch.
- **Sistema_Backend**: Aplicación FastAPI desplegada en Render que sirve la API REST y gestiona la lógica de negocio.
- **Sistema_CORS**: Middleware de FastAPI que controla qué orígenes pueden realizar peticiones cross-origin al backend.
- **Sistema_Config**: Módulo `backend/config.py` que centraliza la configuración de la aplicación mediante variables de entorno.
- **Sistema_Migraciones**: Alembic configurado en modo async que gestiona el esquema de la base de datos PostgreSQL.
- **Sistema_Imágenes**: Subsistema que gestiona el almacenamiento y servicio de imágenes de portada de media items.
- **Entorno_Producción**: Conjunto de servicios en la nube (Vercel + Render + Neon.dev) donde se ejecuta la aplicación en producción.
- **Entorno_Desarrollo**: Entorno local con Vite dev server (:5173), Uvicorn (:8000) y PostgreSQL local (:5432).
- **Variable_Entorno**: Valor de configuración inyectado en tiempo de ejecución (backend) o en tiempo de build (frontend) que permite diferenciar entre entornos.
- **Health_Check**: Endpoint HTTP que Render consulta periódicamente para verificar que el backend está operativo.
- **SSL_Requerido**: Conexión cifrada obligatoria para la base de datos en Neon.dev (parámetro `sslmode=require`).

## Requisitos

### Requisito 1: Configuración dinámica de la URL base del API en el frontend

**User Story:** Como desarrollador, quiero que el frontend apunte automáticamente al backend correcto según el entorno, para que funcione tanto en desarrollo local como en producción.

#### Criterios de Aceptación

1. WHILE el frontend se ejecuta en Entorno_Desarrollo, THE Cliente_API SHALL enviar las peticiones a `/api` (URL relativa, resuelta por el proxy de Vite).
2. WHILE el frontend se ejecuta en Entorno_Producción, THE Cliente_API SHALL enviar las peticiones a la URL absoluta del Sistema_Backend en Render (por ejemplo `https://<app>.onrender.com/api`).
3. THE Sistema_Build_Frontend SHALL leer la URL base del backend desde la variable de entorno `VITE_API_BASE_URL` en tiempo de build.
4. WHEN la variable `VITE_API_BASE_URL` no está definida, THE Cliente_API SHALL usar `/api` como valor por defecto para mantener compatibilidad con el Entorno_Desarrollo.
5. THE Cliente_API SHALL construir todas las URLs de petición concatenando la URL base configurada con la ruta del endpoint, sin duplicar barras.

### Requisito 2: Configuración dinámica de la URL base de imágenes en el frontend

**User Story:** Como desarrollador, quiero que las URLs de imágenes apunten al origen correcto según el entorno, para que las portadas se muestren tanto en desarrollo como en producción.

#### Criterios de Aceptación

1. WHILE el frontend se ejecuta en Entorno_Desarrollo, THE Cliente_API SHALL construir las URLs de imágenes usando `/images` (URL relativa, resuelta por el proxy de Vite).
2. WHILE el frontend se ejecuta en Entorno_Producción, THE Cliente_API SHALL construir las URLs de imágenes usando la URL absoluta del Sistema_Backend en Render (por ejemplo `https://<app>.onrender.com/images`).
3. THE Sistema_Build_Frontend SHALL leer la URL base de imágenes desde la variable de entorno `VITE_IMAGES_BASE_URL` en tiempo de build.
4. WHEN la variable `VITE_IMAGES_BASE_URL` no está definida, THE Cliente_API SHALL usar `/images` como valor por defecto.

### Requisito 3: Configuración de CORS para producción

**User Story:** Como desarrollador, quiero que el backend permita peticiones desde el dominio del frontend en producción, para que la comunicación cross-origin funcione correctamente.

#### Criterios de Aceptación

1. THE Sistema_CORS SHALL leer la lista de orígenes permitidos desde la variable de entorno `ALLOWED_ORIGINS`.
2. WHEN la variable `ALLOWED_ORIGINS` está definida, THE Sistema_CORS SHALL permitir peticiones únicamente desde los orígenes listados (separados por coma).
3. WHEN la variable `ALLOWED_ORIGINS` no está definida, THE Sistema_CORS SHALL permitir todos los orígenes (`*`) para mantener compatibilidad con el Entorno_Desarrollo.
4. THE Sistema_CORS SHALL permitir las cabeceras `Authorization` y `Content-Type` en las peticiones cross-origin.
5. THE Sistema_CORS SHALL permitir los métodos HTTP GET, POST, PUT, PATCH y DELETE en las peticiones cross-origin.

### Requisito 4: Configuración de la base de datos para Neon.dev

**User Story:** Como desarrollador, quiero que el backend se conecte a la base de datos de Neon.dev en producción con SSL obligatorio, manteniendo la conexión local para desarrollo.

#### Criterios de Aceptación

1. THE Sistema_Config SHALL leer la URL de conexión a la base de datos desde la variable de entorno `DATABASE_URL`.
2. WHEN la variable `DATABASE_URL` no está definida, THE Sistema_Config SHALL usar la URL de conexión local por defecto (`postgresql+asyncpg://postgres:postgres@localhost:5432/media_tracker`).
3. WHEN la variable `DATABASE_URL` contiene un host de Neon.dev, THE Sistema_Config SHALL configurar la conexión con SSL habilitado (`ssl=require`).
4. THE Sistema_Config SHALL soportar el formato de URL de Neon.dev (`postgresql+asyncpg://<user>:<password>@<host>.neon.tech/<database>?ssl=require`).

### Requisito 5: Ejecución de migraciones contra Neon.dev

**User Story:** Como desarrollador, quiero poder ejecutar las migraciones de Alembic contra la base de datos de Neon.dev, para mantener el esquema actualizado en producción.

#### Criterios de Aceptación

1. THE Sistema_Migraciones SHALL leer la URL de conexión desde la variable de entorno `DATABASE_URL` en lugar de usar el valor hardcodeado en `alembic.ini`.
2. WHEN se ejecuta `alembic upgrade head` con la variable `DATABASE_URL` apuntando a Neon.dev, THE Sistema_Migraciones SHALL aplicar todas las migraciones pendientes contra la base de datos remota.
3. THE Sistema_Migraciones SHALL soportar conexiones con SSL requerido al ejecutar migraciones contra Neon.dev.

### Requisito 6: Gestión de variables de entorno por entorno

**User Story:** Como desarrollador, quiero tener una separación clara de configuración entre desarrollo y producción, para evitar errores de configuración.

#### Criterios de Aceptación

1. THE Sistema_Config SHALL documentar todas las variables de entorno necesarias para producción en un archivo `.env.example` en la raíz del proyecto.
2. THE Sistema_Config SHALL incluir las siguientes variables en `.env.example`: `DATABASE_URL`, `ALLOWED_ORIGINS`, `JWT_SECRET_KEY`, `TMDB_API_KEY`, `VITE_API_BASE_URL` y `VITE_IMAGES_BASE_URL`.
3. THE Sistema_Build_Frontend SHALL incluir un archivo `.env.example` en `frontend/` con las variables `VITE_API_BASE_URL` y `VITE_IMAGES_BASE_URL`.
4. THE Sistema_Config SHALL cargar la variable `JWT_SECRET_KEY` desde el entorno en producción, sin usar el valor por defecto de desarrollo.


### Requisito 7: Estrategia de almacenamiento de imágenes para filesystem efímero

**User Story:** Como desarrollador, quiero que las imágenes de portada sobrevivan a los redeploys de Render, o al menos que la aplicación funcione correctamente sin ellas.

#### Criterios de Aceptación

1. THE Sistema_Imágenes SHALL detectar cuando una imagen referenciada en `image_path` no existe en el filesystem y devolver una respuesta apropiada en lugar de un error 500.
2. WHEN el Sistema_Backend se despliega en Render, THE Sistema_Imágenes SHALL documentar que el directorio `backend/images/` es efímero y que las imágenes se pierden en cada redeploy.
3. THE Sistema_Imágenes SHALL servir una imagen placeholder o devolver un código 404 controlado cuando la imagen solicitada no existe en el filesystem.
4. IF la variable de entorno `TMDB_API_KEY` está configurada en producción, THEN THE Sistema_Imágenes SHALL re-descargar las imágenes de TMDB bajo demanda cuando se acceda a un media item cuya imagen no existe en el filesystem.

### Requisito 8: Health check endpoint para Render

**User Story:** Como desarrollador, quiero que Render pueda verificar que el backend está operativo, para que el servicio se reinicie automáticamente si deja de responder.

#### Criterios de Aceptación

1. THE Sistema_Backend SHALL exponer un endpoint `GET /api/health` que devuelva un código HTTP 200 con un cuerpo JSON `{"status": "ok"}`.
2. THE Health_Check SHALL responder sin requerir autenticación (sin Token_Acceso).
3. THE Health_Check SHALL verificar que la conexión a la base de datos está activa ejecutando una query simple (`SELECT 1`).
4. IF la conexión a la base de datos falla durante el health check, THEN THE Sistema_Backend SHALL devolver un código HTTP 503 con un cuerpo JSON `{"status": "unhealthy", "detail": "database connection failed"}`.

### Requisito 9: Configuración de despliegue del backend en Render

**User Story:** Como desarrollador, quiero que Render sepa cómo construir y arrancar el backend, para que el despliegue sea automático.

#### Criterios de Aceptación

1. THE Sistema_Backend SHALL incluir un archivo `render.yaml` en la raíz del proyecto que defina el servicio web con el tipo `web`, el runtime `python`, el comando de build (`pip install -r backend/requirements.txt`) y el comando de arranque.
2. THE Sistema_Backend SHALL arrancar en producción con el comando `uvicorn backend.main:app --host 0.0.0.0 --port $PORT` donde `$PORT` es la variable de entorno proporcionada por Render.
3. THE Sistema_Backend SHALL definir en `render.yaml` las variables de entorno necesarias (`DATABASE_URL`, `ALLOWED_ORIGINS`, `JWT_SECRET_KEY`) como referencias a variables de entorno de Render (no valores hardcodeados).
4. THE Sistema_Backend SHALL configurar el health check path como `/api/health` en `render.yaml`.

### Requisito 10: Configuración de despliegue del frontend en Vercel

**User Story:** Como desarrollador, quiero que el frontend se despliegue automáticamente como sitio estático en Vercel, para aprovechar el CDN y el free tier.

#### Criterios de Aceptación

1. THE Sistema_Build_Frontend SHALL incluir un archivo de configuración de despliegue `vercel.json` en el directorio `frontend/`.
2. THE Sistema_Build_Frontend SHALL configurar el comando de build como `npm run build` y el directorio de salida como `dist`.
3. THE Sistema_Build_Frontend SHALL configurar una regla de rewrite que redirija todas las rutas a `index.html` para soportar el enrutamiento del lado del cliente de Vue Router (modo history).
4. THE Sistema_Build_Frontend SHALL definir la variable de entorno `VITE_API_BASE_URL` en la configuración de Vercel apuntando a la URL del Sistema_Backend en Render.
5. THE Sistema_Build_Frontend SHALL definir la variable de entorno `VITE_IMAGES_BASE_URL` en la configuración de Vercel apuntando a la URL de imágenes del Sistema_Backend en Render.

### Requisito 11: Compatibilidad dual desarrollo/producción

**User Story:** Como desarrollador, quiero que el flujo de desarrollo local siga funcionando exactamente igual después de los cambios de deployment, para no romper mi workflow.

#### Criterios de Aceptación

1. WHILE el frontend se ejecuta en Entorno_Desarrollo, THE Sistema_Build_Frontend SHALL mantener el proxy de Vite para `/api` y `/images` hacia `localhost:8000` sin cambios.
2. WHILE el backend se ejecuta en Entorno_Desarrollo sin variables de entorno de producción, THE Sistema_Config SHALL usar todos los valores por defecto (base de datos local, CORS permisivo, JWT secret de desarrollo).
3. THE Sistema_Backend SHALL funcionar correctamente tanto con PostgreSQL local como con Neon.dev sin cambios en el código fuente, solo mediante variables de entorno.
4. THE Sistema_Migraciones SHALL funcionar correctamente tanto contra PostgreSQL local como contra Neon.dev, determinando la URL de conexión exclusivamente por la variable de entorno `DATABASE_URL`.
