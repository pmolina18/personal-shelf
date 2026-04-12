# Documento de Requisitos — Status Timestamps

## Introducción

Personal Shelf registra el progreso de consumo de cada media item mediante tres estados: `pending`, `in_progress` y `completed`. Actualmente el modelo `MediaItem` ya dispone de los campos `started_at` y `completed_at`, que se gestionan parcialmente en `MediaService.update_status`. Sin embargo, falta el campo `pending_at` y la lógica de timestamps es inconsistente: `started_at` solo se setea si es `None` (no se sobreescribe al volver a `in_progress`), mientras que `completed_at` siempre se sobreescribe.

Esta feature unifica y completa la gestión de timestamps de estado:

1. Añade el campo `pending_at` al modelo y lo expone en la API.
2. Normaliza la lógica para que **siempre** se sobreescriba la fecha del estado destino al cambiar de estado (incluido `started_at`).
3. Setea `pending_at` automáticamente al crear un item (ya que nace con `status=pending`).
4. Muestra una mini-timeline visual en `MediaDetailView.vue` con los tres hitos temporales.

Los items existentes tendrán `pending_at` a `null` — solo se rellenan a partir de ahora.

## Glosario

- **MediaItem**: Modelo SQLAlchemy que representa un elemento del catálogo (película, libro o serie). Tabla `media_items`.
- **Status**: Estado de consumo de un MediaItem. Valores posibles: `pending`, `in_progress`, `completed` (enum `MediaStatus`).
- **Timestamp_Estado**: Campo `DateTime` nullable en MediaItem que registra la última vez que el item entró en un estado concreto. Son tres: `pending_at`, `started_at`, `completed_at`.
- **pending_at**: Timestamp que registra cuándo el item se puso (o volvió) al estado `pending`. **No existe todavía** — hay que añadirlo.
- **started_at**: Timestamp que registra cuándo el item pasó a `in_progress`. **Ya existe** en el modelo, pero su lógica es incompleta (solo se setea si es `None`).
- **completed_at**: Timestamp que registra cuándo el item se marcó como `completed`. **Ya existe** en el modelo y siempre se sobreescribe.
- **Servicio_Media**: Clase `MediaService` en `backend/services/media_service.py` que contiene toda la lógica de negocio de media items.
- **update_status**: Método de Servicio_Media que cambia el estado de un item y gestiona los Timestamps_Estado.
- **MediaResponse**: Schema Pydantic de respuesta que serializa un MediaItem para la API REST.
- **_to_response**: Función helper en `media_service.py` que convierte un `MediaItem` ORM a `MediaResponse`.
- **MediaDetailView**: Vista Vue (`MediaDetailView.vue`) que muestra el detalle completo de un media item.
- **Mini-Timeline**: Componente visual dentro de MediaDetailView que muestra los tres hitos temporales (`pending_at`, `started_at`, `completed_at`) como una línea de progreso horizontal con fechas.
- **Migración_Alembic**: Script de migración generado por Alembic que añade la columna `pending_at` a la tabla `media_items`.

## Requisitos

### Requisito 1: Añadir campo `pending_at` al modelo MediaItem

**Historia de Usuario:** Como desarrollador, quiero que el modelo MediaItem tenga un campo `pending_at` para registrar cuándo un item entró al estado `pending`, completando así el trío de timestamps de estado.

#### Criterios de Aceptación

1. THE MediaItem SHALL incluir un campo `pending_at` de tipo `DateTime`, nullable, sin valor por defecto a nivel de base de datos.
2. THE campo `pending_at` SHALL estar definido con `mapped_column(nullable=True)` siguiendo el mismo patrón que `started_at` y `completed_at`.
3. WHEN la Migración_Alembic se ejecute contra una base de datos existente, THE columna `pending_at` SHALL añadirse a la tabla `media_items` con valor `NULL` para todos los registros existentes.
4. THE Migración_Alembic SHALL ser reversible (incluir operación de downgrade que elimine la columna `pending_at`).

### Requisito 2: Setear `pending_at` automáticamente al crear un item

**Historia de Usuario:** Como usuario, quiero que al crear un nuevo media item se registre automáticamente la fecha de creación como `pending_at`, ya que todo item nuevo nace con estado `pending`.

#### Criterios de Aceptación

1. WHEN el Servicio_Media crea un nuevo MediaItem, THE Sistema SHALL asignar `pending_at` con la fecha y hora actual (`datetime.utcnow()`).
2. THE valor de `pending_at` asignado en la creación SHALL ser aproximadamente igual a `created_at` (diferencia menor a 1 segundo).
3. WHEN el item se crea, THE campos `started_at` y `completed_at` SHALL permanecer como `None`.

### Requisito 3: Sobreescribir siempre el timestamp del estado destino al cambiar de estado

**Historia de Usuario:** Como usuario, quiero que al cambiar el estado de un item se actualice siempre la fecha del estado destino con la fecha actual, incluso si ya tenía una fecha previa, para reflejar la última vez que entré en ese estado.

#### Criterios de Aceptación

1. WHEN el estado de un MediaItem cambia a `pending`, THE Servicio_Media SHALL asignar `pending_at` con `datetime.utcnow()`, sobreescribiendo cualquier valor previo.
2. WHEN el estado de un MediaItem cambia a `in_progress`, THE Servicio_Media SHALL asignar `started_at` con `datetime.utcnow()`, sobreescribiendo cualquier valor previo.
3. WHEN el estado de un MediaItem cambia a `completed`, THE Servicio_Media SHALL asignar `completed_at` con `datetime.utcnow()`, sobreescribiendo cualquier valor previo.
4. WHEN el estado de un MediaItem cambia, THE Servicio_Media SHALL modificar únicamente el Timestamp_Estado correspondiente al estado destino — los timestamps de los otros estados SHALL permanecer sin cambios.
5. WHEN el estado solicitado es igual al estado actual del item, THE Servicio_Media SHALL no modificar ningún Timestamp_Estado (no-op en cuanto a timestamps).

### Requisito 4: Exponer `pending_at` en el schema de respuesta de la API

**Historia de Usuario:** Como desarrollador frontend, quiero que la API devuelva el campo `pending_at` en las respuestas de media items, para poder mostrar la información de timestamps completa en la interfaz.

#### Criterios de Aceptación

1. THE MediaResponse SHALL incluir un campo `pending_at` de tipo `datetime | None`.
2. THE función `_to_response` SHALL mapear `item.pending_at` al campo `pending_at` de MediaResponse.
3. WHEN un MediaItem no tiene `pending_at` (items existentes previos a la migración), THE API SHALL devolver `pending_at: null` en la respuesta JSON.
4. THE campo `pending_at` SHALL aparecer en todos los endpoints que devuelven MediaResponse: `POST /api/media`, `GET /api/media`, `GET /api/media/{id}`, `PUT /api/media/{id}`, `PATCH /api/media/{id}/status`, `PATCH /api/media/{id}/rating`, `PUT /api/media/{id}/tags`.

### Requisito 5: Mini-timeline visual en MediaDetailView

**Historia de Usuario:** Como usuario, quiero ver una mini-timeline en el detalle de un media item que muestre cuándo pasó por cada estado (pending, in progress, completed), para tener una visión rápida del historial de consumo.

#### Criterios de Aceptación

1. THE MediaDetailView SHALL mostrar una sección "Timeline" dentro del área principal (`.detail-main`) cuando el item tiene al menos un Timestamp_Estado no nulo.
2. THE Mini-Timeline SHALL representar los tres hitos en orden horizontal: `Pending` → `In Progress` → `Completed`, conectados por una línea.
3. WHEN un Timestamp_Estado tiene valor, THE Mini-Timeline SHALL mostrar el hito correspondiente como activo (con color y fecha formateada debajo).
4. WHEN un Timestamp_Estado es `null`, THE Mini-Timeline SHALL mostrar el hito correspondiente como inactivo (gris, sin fecha).
5. THE Mini-Timeline SHALL formatear las fechas en formato legible corto (ejemplo: "12 mar 2026" o formato equivalente con `toLocaleDateString`).
6. THE Mini-Timeline SHALL ser accesible: usar `role="list"` para el contenedor y `role="listitem"` para cada hito, con `aria-label` descriptivo en cada hito (ejemplo: "Pending since 12 mar 2026").
7. THE Mini-Timeline SHALL ser responsive: en pantallas menores a 500px, los hitos SHALL apilarse verticalmente manteniendo la línea conectora.
8. THE Mini-Timeline SHALL usar los colores del sistema de diseño existente: `--color-status-pending-*` para el hito pending, `--color-status-in-progress-*` para in_progress, y `--color-status-completed-*` para completed.

### Requisito 6: Integración con el servicio MCP

**Historia de Usuario:** Como usuario de herramientas IA, quiero que las herramientas MCP que crean o cambian el estado de items también gestionen correctamente los timestamps de estado, para que el historial sea consistente independientemente de cómo se interactúe con la aplicación.

#### Criterios de Aceptación

1. WHEN la herramienta MCP `create_media` crea un item, THE Sistema SHALL asignar `pending_at` automáticamente (delegando en Servicio_Media).
2. WHEN la herramienta MCP `update_status` cambia el estado de un item, THE Sistema SHALL actualizar el Timestamp_Estado correspondiente (delegando en Servicio_Media).
3. THE respuesta de las herramientas MCP que devuelven datos de un MediaItem SHALL incluir los campos `pending_at`, `started_at` y `completed_at`.

## Propiedades de Correctitud (Hypothesis)

Las siguientes propiedades deben validarse con tests basados en propiedades usando Hypothesis:

### Propiedad 1: Creación siempre setea `pending_at`

Para cualquier combinación válida de título, tipo de media y campos opcionales, al crear un MediaItem el campo `pending_at` resultante no es `None` y su valor es menor o igual a la fecha actual. Los campos `started_at` y `completed_at` son `None`.

### Propiedad 2: Cambio de estado sobreescribe exactamente el timestamp destino

Para cualquier MediaItem existente y cualquier estado destino válido (`pending`, `in_progress`, `completed`), al ejecutar `update_status`:
- El Timestamp_Estado del estado destino tiene un valor no nulo posterior o igual al valor previo (si existía).
- Los Timestamps_Estado de los otros dos estados permanecen sin cambios respecto a sus valores previos.

### Propiedad 3: Idempotencia — cambiar al mismo estado no modifica timestamps

Para cualquier MediaItem existente cuyo estado actual es `S`, al ejecutar `update_status` con el mismo estado `S`, todos los Timestamps_Estado permanecen exactamente iguales a sus valores previos.

### Propiedad 4: Ciclo completo de estados produce tres timestamps no nulos

Para cualquier MediaItem nuevo, al ejecutar la secuencia `pending` → `in_progress` → `completed`, los tres Timestamps_Estado (`pending_at`, `started_at`, `completed_at`) son no nulos y cumplen `pending_at <= started_at <= completed_at`.

### Propiedad 5: `pending_at` en respuesta API coincide con el modelo

Para cualquier MediaItem creado o actualizado vía la API REST, el campo `pending_at` en la respuesta JSON coincide con el valor almacenado en la base de datos (verificado mediante consulta directa al modelo).
