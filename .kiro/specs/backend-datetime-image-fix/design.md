# Corrección de Datetimes e Imágenes en Backend — Diseño de Bugfix

## Resumen

Este documento formaliza la corrección de dos bugs interrelacionados en el backend del Media Tracker:

1. **Crash por timezone en datetimes**: `media_service.py` usa `datetime.now(timezone.utc)` que produce datetimes con timezone (tz-aware), pero las columnas de PostgreSQL son `TIMESTAMP WITHOUT TIME ZONE`. asyncpg rechaza la incompatibilidad y lanza `DBAPIError`. La corrección reemplaza todas las llamadas por `datetime.utcnow()` (naive UTC), consistente con el resto del codebase que usa `server_default=func.now()`.

2. **Flujo de imágenes roto**: Las imágenes placeholder por defecto (`default_movie.png`, `default_book.png`, `default_series.png`) no existen físicamente en `backend/images/`, causando 404. Además, aunque el router ya invoca `ImageService.fetch_image()` después de crear un item, el flujo necesita que los placeholders existan en disco para que el fallback funcione. La corrección crea los archivos placeholder y asegura que `image_path` siempre quede persistido.

## Glosario

- **Bug_Condition (C)**: Condición que dispara el bug — (1) cualquier operación de update que asigne `datetime.now(timezone.utc)` a una columna timestamp, (2) referencia a archivos de imagen por defecto inexistentes
- **Property (P)**: Comportamiento deseado — (1) los datetimes asignados son naive (sin tzinfo) y el commit se completa sin error, (2) los archivos de imagen por defecto existen y son servidos con HTTP 200
- **Preservation**: Comportamiento existente que no debe cambiar — creación de items con `server_default`, consultas GET, eliminación, servicio de imágenes ya almacenadas
- **`MediaService`**: Clase en `backend/services/media_service.py` que contiene toda la lógica de negocio CRUD para media items
- **`ImageService`**: Clase en `backend/services/image_service.py` que busca, descarga y almacena imágenes de medios
- **`_to_response()`**: Función helper que convierte un `MediaItem` ORM a `MediaResponse`, construyendo `image_url` desde `image_path`
- **Datetime naive**: Objeto `datetime` sin información de timezone (`tzinfo is None`)
- **Datetime tz-aware**: Objeto `datetime` con timezone asignado (`tzinfo is not None`)

## Detalles de los Bugs

### Bug Condition

Los bugs se manifiestan en dos escenarios independientes:

**Bug 1 — Timezone**: Cualquier operación que ejecute `datetime.now(timezone.utc)` y haga commit a PostgreSQL falla porque asyncpg no puede insertar un datetime tz-aware en una columna `TIMESTAMP WITHOUT TIME ZONE`. Esto afecta a 5 métodos de `MediaService`: `update()`, `update_status()`, `update_rating()`, `update_tags()`, y las transiciones de estado que asignan `started_at`/`completed_at`.

**Bug 2 — Imágenes**: Cuando `ImageService.fetch_image()` no encuentra imagen externa (o falla la descarga), devuelve un filename de imagen por defecto (e.g., `default_movie.png`). Este archivo no existe en `backend/images/`, resultando en HTTP 404 al servir la imagen.

**Especificación Formal:**
```
FUNCTION isBugCondition_Timezone(input)
  INPUT: input de tipo ServiceMethodCall (método, media_id, datos)
  OUTPUT: boolean

  RETURN input.method IN ['update', 'update_status', 'update_rating', 'update_tags']
         AND el método asigna datetime.now(timezone.utc) a alguna columna
         AND la columna es TIMESTAMP WITHOUT TIME ZONE
END FUNCTION

FUNCTION isBugCondition_Image(input)
  INPUT: input de tipo ImageRequest (media_type)
  OUTPUT: boolean

  RETURN input.media_type IN ['movie', 'book', 'series']
         AND fetch_image() retorna un filename de imagen por defecto
         AND el archivo correspondiente NO existe en backend/images/
END FUNCTION
```

### Ejemplos

- **Ejemplo 1**: Cambiar status a "completed" → `update_status()` asigna `datetime.now(timezone.utc)` a `completed_at` y `updated_at` → asyncpg lanza `DBAPIError: can't subtract offset-naive and offset-aware datetimes`
- **Ejemplo 2**: Cambiar status a "in_progress" (con `started_at` None) → mismo error al asignar `started_at` y `updated_at`
- **Ejemplo 3**: Actualizar rating a 8 → `update_rating()` asigna `datetime.now(timezone.utc)` a `updated_at` → mismo `DBAPIError`
- **Ejemplo 4**: Crear media item "Inception" tipo "movie" sin API key de TMDB → `fetch_image()` retorna `default_movie.png` → frontend solicita `/images/default_movie.png` → HTTP 404
- **Ejemplo 5**: Crear media item "Dune" tipo "book" → `fetch_image()` falla en Open Library → retorna `default_book.png` → HTTP 404

## Comportamiento Esperado

### Requisitos de Preservación

**Comportamientos Sin Cambios:**
- La creación de media items debe seguir asignando `created_at` y `updated_at` mediante `server_default=func.now()` del lado del servidor
- Las consultas GET de media items deben seguir devolviendo timestamps correctamente en JSON
- La eliminación de media items debe seguir funcionando sin errores de timestamps
- La subida manual de imágenes debe seguir guardando en `backend/images/` y almacenando la referencia en `image_path`
- La descarga exitosa de imágenes externas (TMDB/Open Library) debe seguir funcionando
- Las imágenes previamente almacenadas deben seguir siendo servidas con HTTP 200
- Los media items existentes con `image_path` asignado deben seguir devolviendo `image_url` correcta

**Alcance:**
Todas las operaciones que NO involucren asignación manual de datetimes en el código Python ni referencia a imágenes por defecto inexistentes deben quedar completamente inalteradas. Esto incluye:
- Creación de items (timestamps vía `server_default`)
- Consultas y listados (GET)
- Eliminación de items (DELETE)
- Servicio de imágenes ya existentes en disco

## Causa Raíz Hipotética

Basado en el análisis del código fuente, las causas raíz son:

1. **Incompatibilidad de timezone en `media_service.py`**: El archivo importa `from datetime import datetime, timezone` y usa `datetime.now(timezone.utc)` en 5 ubicaciones dentro de los métodos `update()`, `update_status()`, `update_rating()`, y `update_tags()`. Esto produce objetos `datetime` con `tzinfo=UTC`, pero las columnas del modelo `MediaItem` (`updated_at`, `started_at`, `completed_at`) están mapeadas como `TIMESTAMP WITHOUT TIME ZONE` (el tipo por defecto de SQLAlchemy cuando no se especifica `timezone=True`). asyncpg rechaza estrictamente esta incompatibilidad.

2. **Archivos placeholder inexistentes**: `ImageService` define `_DEFAULT_IMAGES` con filenames (`default_movie.png`, `default_book.png`, `default_series.png`) pero estos archivos nunca fueron creados en `backend/images/`. El directorio existe (creado por `config.py` con `mkdir`) pero está vacío.

3. **Flujo de imagen en creación funciona parcialmente**: El router `media.py` ya invoca `fetch_image()` después de crear el item y persiste `image_path`. Sin embargo, cuando la búsqueda externa falla (sin API key, timeout, sin resultados), el fallback devuelve un filename de imagen por defecto que no existe en disco, resultando en un `image_path` válido en DB pero un archivo 404 en el servidor.

## Propiedades de Correctitud

Property 1: Bug Condition — Datetimes Naive en Operaciones de Update

_Para cualquier_ media item existente y cualquier operación de update (status, rating, tags, update parcial), la función corregida SHALL asignar datetimes naive (sin tzinfo) a `updated_at`, `started_at`, y `completed_at`, y el commit a la base de datos SHALL completarse sin `DBAPIError`.

**Valida: Requisitos 2.1, 2.2, 2.3, 2.4, 2.5**

Property 2: Bug Condition — Imágenes Placeholder Existen en Disco

_Para cualquier_ tipo de media (`movie`, `book`, `series`), el archivo de imagen por defecto correspondiente SHALL existir físicamente en `backend/images/` y SHALL ser servido con HTTP 200 cuando sea solicitado vía `/images/<filename>`.

**Valida: Requisitos 2.6, 2.9**

Property 3: Bug Condition — image_path Persistido en Creación

_Para cualquier_ media item creado, el sistema SHALL invocar `ImageService.fetch_image()` y SHALL almacenar el filename resultante en `image_path` en la base de datos, de modo que `image_url` en la respuesta de la API no sea null.

**Valida: Requisitos 2.7, 2.8, 2.10**

Property 4: Preservation — Timestamps de Creación via server_default

_Para cualquier_ media item creado, los campos `created_at` y `updated_at` SHALL seguir siendo asignados por `server_default=func.now()` del lado del servidor, sin intervención del código Python, preservando el comportamiento original de creación.

**Valida: Requisitos 3.1, 3.2, 3.3**

Property 5: Preservation — Servicio de Imágenes Existentes

_Para cualquier_ imagen previamente almacenada en `backend/images/`, el endpoint `/images/<filename>` SHALL seguir sirviendo el archivo con HTTP 200, y los media items existentes con `image_path` asignado SHALL seguir devolviendo `image_url` correcta en la respuesta de la API.

**Valida: Requisitos 3.4, 3.5, 3.6, 3.7**

## Implementación del Fix

### Cambios Requeridos

Asumiendo que nuestro análisis de causa raíz es correcto:

**Archivo**: `backend/services/media_service.py`

**Cambios Específicos**:
1. **Reemplazar import de timezone**: Cambiar `from datetime import datetime, timezone` a `from datetime import datetime` (eliminar `timezone` del import)
2. **Reemplazar `datetime.now(timezone.utc)` por `datetime.utcnow()`**: En 5 ubicaciones:
   - `update()` línea ~178: `item.updated_at = datetime.utcnow()`
   - `update_status()` línea ~218: `now = datetime.utcnow()`
   - `update_rating()` línea ~245: `item.updated_at = datetime.utcnow()`
   - `update_tags()` línea ~272: `item.updated_at = datetime.utcnow()`

**Archivo**: `backend/images/`

**Cambios Específicos**:
3. **Crear imágenes placeholder**: Generar programáticamente (o incluir como assets estáticos) tres archivos PNG mínimos:
   - `default_movie.png` — rectángulo con texto/icono de película
   - `default_book.png` — rectángulo con texto/icono de libro
   - `default_series.png` — rectángulo con texto/icono de serie
   - Estos pueden ser PNGs simples de 300x450px con color de fondo y texto centrado

**Archivo**: `backend/services/image_service.py` (verificación)

**Cambios Específicos**:
4. **Verificar que `get_default_image()` retorna filenames correctos**: Confirmar que `_DEFAULT_IMAGES` mapea correctamente a los archivos creados en el paso 3. No se requieren cambios si los nombres coinciden.

**Archivo**: `backend/routers/media.py` (verificación)

**Cambios Específicos**:
5. **Verificar flujo de imagen en creación**: El router ya invoca `fetch_image()` y persiste `image_path`. Con los placeholders existiendo en disco, el flujo completo debería funcionar. Verificar que no hay race conditions entre el commit del service y el commit del router.

## Estrategia de Testing

### Enfoque de Validación

La estrategia de testing sigue un enfoque de dos fases: primero, generar contraejemplos que demuestren los bugs en el código sin corregir, luego verificar que la corrección funciona y preserva el comportamiento existente.

### Exploración de Bug Condition (Checking Exploratorio)

**Objetivo**: Generar contraejemplos que demuestren los bugs ANTES de implementar la corrección. Confirmar o refutar el análisis de causa raíz. Si refutamos, necesitaremos re-hipotetizar.

**Plan de Test**: Escribir tests que ejecuten las operaciones de update en `MediaService` con una base de datos real (o mock de session) y verifiquen que `datetime.now(timezone.utc)` causa el error. Para imágenes, verificar que los archivos por defecto no existen en disco.

**Casos de Test**:
1. **Test de Update Status a Completed**: Llamar `update_status(session, id, "completed")` — fallará con `DBAPIError` en código sin corregir
2. **Test de Update Status a In Progress**: Llamar `update_status(session, id, "in_progress")` con `started_at=None` — fallará con `DBAPIError`
3. **Test de Update Rating**: Llamar `update_rating(session, id, 8)` — fallará con `DBAPIError`
4. **Test de Update Tags**: Llamar `update_tags(session, id, ["sci-fi"])` — fallará con `DBAPIError`
5. **Test de Placeholder Inexistente**: Verificar que `backend/images/default_movie.png` no existe — confirmará el bug de imagen

**Contraejemplos Esperados**:
- `DBAPIError` con mensaje sobre offset-naive vs offset-aware datetimes
- `FileNotFoundError` o HTTP 404 al acceder a imágenes por defecto
- Causas posibles: `datetime.now(timezone.utc)` produce tz-aware, columnas son `TIMESTAMP WITHOUT TIME ZONE`

### Fix Checking

**Objetivo**: Verificar que para todas las entradas donde la bug condition se cumple, la función corregida produce el comportamiento esperado.

**Pseudocódigo:**
```
FOR ALL input WHERE isBugCondition_Timezone(input) DO
  result := mediaService_fixed.method(input)
  ASSERT result.updated_at.tzinfo IS None
  ASSERT no DBAPIError raised
  ASSERT result contiene datos correctos
END FOR

FOR ALL input WHERE isBugCondition_Image(input) DO
  filename := imageService.get_default_image(input.media_type)
  filepath := IMAGE_STORAGE_PATH / filename
  ASSERT filepath.exists()
  ASSERT filepath.stat().st_size > 0
END FOR
```

### Preservation Checking

**Objetivo**: Verificar que para todas las entradas donde la bug condition NO se cumple, la función corregida produce el mismo resultado que la función original.

**Pseudocódigo:**
```
FOR ALL input WHERE NOT isBugCondition_Timezone(input) DO
  ASSERT mediaService_original(input) = mediaService_fixed(input)
END FOR

FOR ALL input WHERE NOT isBugCondition_Image(input) DO
  ASSERT imageService_original(input) = imageService_fixed(input)
END FOR
```

**Enfoque de Testing**: Se recomienda property-based testing para preservation checking porque:
- Genera muchos casos de test automáticamente a través del dominio de entrada
- Detecta edge cases que los unit tests manuales podrían omitir
- Proporciona garantías fuertes de que el comportamiento no cambia para entradas no afectadas por el bug

**Plan de Test**: Observar el comportamiento en código SIN CORREGIR primero para operaciones de creación, consulta y eliminación, luego escribir property-based tests capturando ese comportamiento.

**Casos de Test**:
1. **Preservación de Creación**: Verificar que crear items sigue asignando `created_at`/`updated_at` vía `server_default` sin intervención Python
2. **Preservación de GET**: Verificar que consultar items existentes devuelve timestamps correctos en la respuesta
3. **Preservación de DELETE**: Verificar que eliminar items funciona sin errores de timestamps
4. **Preservación de Imágenes Existentes**: Verificar que imágenes ya almacenadas siguen siendo servidas correctamente

### Unit Tests

- Verificar que `datetime.utcnow()` produce datetimes naive (sin tzinfo)
- Verificar que cada método de update asigna datetimes naive a las columnas correspondientes
- Verificar que los 3 archivos de imagen por defecto existen en `backend/images/`
- Verificar que `_to_response()` construye `image_url` correctamente desde `image_path`
- Verificar edge cases: update con datos vacíos, rating fuera de rango, tags vacíos

### Property-Based Tests

- Generar status aleatorios válidos y verificar que `update_status` completa sin error y produce datetimes naive
- Generar ratings aleatorios (1-10) y verificar que `update_rating` completa sin error
- Generar listas de tags aleatorias y verificar que `update_tags` completa sin error
- Generar media_types aleatorios y verificar que `get_default_image` retorna un filename que existe en disco
- Verificar preservación: para operaciones de creación, los timestamps son asignados por el servidor

### Integration Tests

- Test de flujo completo: crear item → verificar `image_path` no es null → verificar imagen servida con HTTP 200
- Test de flujo de status: crear item → cambiar a "in_progress" → cambiar a "completed" → verificar todos los timestamps son naive y correctos
- Test de fallback de imagen: crear item sin API key de TMDB → verificar que `image_path` apunta a imagen por defecto → verificar HTTP 200
- Test de actualización con re-fetch de imagen: actualizar título → verificar que se re-busca imagen
