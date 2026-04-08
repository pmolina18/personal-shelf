# Documento de Requisitos de Corrección de Bugs

## Introducción

Este documento describe dos bugs encontrados en los logs del backend API del proyecto Personal Shelf (media tracker):

1. **Crash por incompatibilidad de timezone en datetimes**: Al cambiar el estado de un media item a "completed" (o cualquier actualización que asigne `updated_at`, `started_at` o `completed_at`), el backend genera datetimes con timezone (`datetime.now(timezone.utc)`) pero las columnas de PostgreSQL están definidas como `TIMESTAMP WITHOUT TIME ZONE`. Esto provoca que asyncpg rechace el valor y lance un `DBAPIError`.

2. **Flujo de imágenes roto**: Las imágenes por defecto (`default_movie.png`, `default_book.png`, `default_series.png`) referenciadas por `ImageService` no existen físicamente en `backend/images/`, causando errores 404. Además, el flujo completo de asignación de imágenes durante la creación de media items (búsqueda automática en TMDB/Open Library → descarga → almacenamiento en DB) necesita garantizar que `image_path` siempre quede persistido correctamente, ya sea con una imagen descargada o con la imagen por defecto correspondiente.

## Análisis de Bugs

### Bug 1: Crash por timezone en datetimes

#### Comportamiento Actual (Defecto)

1.1 WHEN se actualiza el estado de un media item a "completed" THEN el sistema lanza `sqlalchemy.exc.DBAPIError` con el mensaje "can't subtract offset-naive and offset-aware datetimes" porque `datetime.now(timezone.utc)` genera un datetime con tzinfo que asyncpg no puede insertar en una columna `TIMESTAMP WITHOUT TIME ZONE`

1.2 WHEN se actualiza el estado de un media item a "in_progress" (y `started_at` es None) THEN el sistema lanza el mismo `DBAPIError` al intentar asignar un datetime timezone-aware a `started_at` y `updated_at`

1.3 WHEN se actualiza el rating de un media item THEN el sistema lanza `DBAPIError` al asignar `datetime.now(timezone.utc)` a `updated_at`

1.4 WHEN se actualizan los tags de un media item THEN el sistema lanza `DBAPIError` al asignar `datetime.now(timezone.utc)` a `updated_at`

1.5 WHEN se hace un update parcial de un media item (título, notas, etc.) THEN el sistema lanza `DBAPIError` al asignar `datetime.now(timezone.utc)` a `updated_at`

#### Comportamiento Esperado (Correcto)

2.1 WHEN se actualiza el estado de un media item a "completed" THEN el sistema SHALL asignar datetimes naive (sin timezone) a `updated_at` y `completed_at`, y el commit a la base de datos SHALL completarse sin error

2.2 WHEN se actualiza el estado de un media item a "in_progress" (y `started_at` es None) THEN el sistema SHALL asignar datetimes naive a `started_at` y `updated_at`, y el commit SHALL completarse sin error

2.3 WHEN se actualiza el rating de un media item THEN el sistema SHALL asignar un datetime naive a `updated_at`, y el commit SHALL completarse sin error

2.4 WHEN se actualizan los tags de un media item THEN el sistema SHALL asignar un datetime naive a `updated_at`, y el commit SHALL completarse sin error

2.5 WHEN se hace un update parcial de un media item THEN el sistema SHALL asignar un datetime naive a `updated_at`, y el commit SHALL completarse sin error

#### Comportamiento Sin Cambios (Prevención de Regresión)

3.1 WHEN se crea un nuevo media item THEN el sistema SHALL CONTINUE TO asignar `created_at` y `updated_at` mediante `server_default=func.now()` del lado del servidor sin intervención del código Python

3.2 WHEN se consulta un media item existente (GET) THEN el sistema SHALL CONTINUE TO devolver los timestamps correctamente en la respuesta JSON

3.3 WHEN se elimina un media item THEN el sistema SHALL CONTINUE TO eliminar el item sin errores relacionados con timestamps

### Bug 2: Flujo de imágenes roto — placeholders 404 y asignación incompleta

#### Comportamiento Actual (Defecto)

1.6 WHEN las imágenes por defecto (`default_movie.png`, `default_book.png`, `default_series.png`) son referenciadas por `ImageService` THEN el sistema devuelve un 404 porque estos archivos no existen físicamente en `backend/images/`

1.7 WHEN se crea un media item sin imagen subida por el usuario y la búsqueda externa (TMDB/Open Library) falla o no encuentra resultados THEN el sistema asigna un `image_path` que apunta a un archivo por defecto inexistente, resultando en un 404 al cargar la imagen en el frontend

1.8 WHEN se crea un media item sin imagen subida por el usuario y la búsqueda externa tiene éxito THEN el sistema descarga la imagen y la almacena en `backend/images/`, pero el `image_path` resultante puede no persistirse correctamente en la base de datos si ocurre un error entre la descarga y el commit

1.9 WHEN el frontend recibe `image_url: null` (porque `image_path` es null en la DB) THEN el frontend recurre a placeholders externos de `placehold.co`, lo cual indica que el backend no completó el flujo de asignación de imagen durante la creación del media item

#### Comportamiento Esperado (Correcto)

2.6 WHEN se despliega el backend THEN los archivos de imagen por defecto (`default_movie.png`, `default_book.png`, `default_series.png`) SHALL existir físicamente en `backend/images/` para que cualquier referencia a ellos sea servida con HTTP 200

2.7 WHEN se crea un media item sin imagen subida por el usuario THEN el sistema SHALL invocar automáticamente `ImageService.fetch_image()` con el título y tipo del media, y SHALL almacenar el filename resultante (imagen descargada o imagen por defecto) en la columna `image_path` de la base de datos

2.8 WHEN `ImageService.fetch_image()` busca en TMDB/Open Library y encuentra una imagen THEN el sistema SHALL descargar la imagen, guardarla en `backend/images/`, y devolver el filename para que sea almacenado en `image_path`

2.9 WHEN `ImageService.fetch_image()` no encuentra imagen externa o la descarga falla THEN el sistema SHALL devolver el filename de la imagen por defecto correspondiente al tipo de media (`default_movie.png`, `default_book.png`, o `default_series.png`), que SHALL existir físicamente y ser servida con HTTP 200

2.10 WHEN un media item tiene `image_path` almacenado en la DB THEN la respuesta de la API SHALL incluir `image_url` con el valor `/images/<image_path>`, y el frontend SHALL mostrar esa imagen

2.11 WHEN un media item tiene `image_url` como null en la respuesta de la API (caso extremo) THEN el frontend SHALL CONTINUE mostrando los placeholders de `placehold.co` como último recurso — este comportamiento existente es aceptable

#### Comportamiento Sin Cambios (Prevención de Regresión)

3.4 WHEN el usuario sube una imagen manualmente para un media item THEN el sistema SHALL CONTINUE TO guardar la imagen en `backend/images/` y almacenar la referencia en `image_path` en la DB

3.5 WHEN `ImageService` encuentra y descarga exitosamente una imagen externa de TMDB o Open Library THEN el sistema SHALL CONTINUE TO almacenar la imagen descargada en `backend/images/` y devolver su filename

3.6 WHEN se solicita una imagen previamente almacenada vía `/images/<filename>` THEN el sistema SHALL CONTINUE TO servir el archivo correctamente con HTTP 200

3.7 WHEN se consulta o lista media items existentes que ya tienen `image_path` asignado THEN el sistema SHALL CONTINUE TO devolver `image_url` con la ruta correcta sin modificar las imágenes existentes
