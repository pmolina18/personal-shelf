# Documento de Requisitos — Media Metadata Autofill

## Introducción

Esta funcionalidad permite que el backend de Personal Shelf rellene automáticamente los campos de metadatos (año, creador, descripción) al crear o actualizar un media item, consultando APIs externas: TMDB para películas y series, y Open Library para libros. Además, se expone un endpoint de búsqueda/sugerencias para que el frontend muestre candidatos antes de confirmar la creación, permitiendo al usuario revisar y editar los datos autocompletados.

## Glosario

- **MetadataService**: Servicio del backend responsable de buscar metadatos en APIs externas (TMDB, Open Library) y devolver resultados estructurados.
- **MetadataCandidate**: Objeto que representa un resultado de búsqueda de metadatos, incluyendo título, año, creador, descripción e imagen.
- **TMDB**: The Movie Database — API externa que provee metadatos de películas y series (título, fecha de estreno, sinopsis, director/creador).
- **Open_Library**: API pública de Open Library que provee metadatos de libros (título, año de primera publicación, autor, temas).
- **MediaItem**: Entidad principal del catálogo que representa una película, libro o serie.
- **ImageService**: Servicio existente que busca imágenes de portada en TMDB y Open Library.
- **MediaForm**: Componente Vue del frontend que gestiona la creación y edición de media items.

## Requisitos

### Requisito 1: Búsqueda de metadatos en TMDB

**User Story:** Como usuario, quiero que el sistema busque metadatos en TMDB cuando creo una película o serie, para no tener que introducir manualmente el año, director y sinopsis.

#### Criterios de Aceptación

1. WHEN el usuario proporciona un título y el media_type es "movie", THE MetadataService SHALL buscar en la API de TMDB usando el endpoint `/search/movie` y devolver una lista de MetadataCandidate con título, año (extraído de `release_date`), director (extraído de créditos) y descripción (campo `overview`).
2. WHEN el usuario proporciona un título y el media_type es "series", THE MetadataService SHALL buscar en la API de TMDB usando el endpoint `/search/tv` y devolver una lista de MetadataCandidate con título, año (extraído de `first_air_date`), creador (extraído de `created_by`) y descripción (campo `overview`).
3. WHILE la variable de entorno TMDB_API_KEY esté vacía o no configurada, THE MetadataService SHALL omitir la búsqueda en TMDB y devolver una lista vacía de candidatos sin generar un error.

### Requisito 2: Búsqueda de metadatos en Open Library

**User Story:** Como usuario, quiero que el sistema busque metadatos en Open Library cuando creo un libro, para obtener automáticamente el año de publicación y el autor.

#### Criterios de Aceptación

1. WHEN el usuario proporciona un título y el media_type es "book", THE MetadataService SHALL buscar en la API de Open Library usando el endpoint `/search.json` y devolver una lista de MetadataCandidate con título, año (campo `first_publish_year`), autor (primer elemento de `author_name`) y descripción (primer elemento de `subject`, si existe).
2. WHEN la API de Open Library no devuelve resultados para el título proporcionado, THE MetadataService SHALL devolver una lista vacía de candidatos.

### Requisito 3: Endpoint de búsqueda de sugerencias de metadatos

**User Story:** Como usuario, quiero poder buscar sugerencias de metadatos antes de crear un item, para elegir el resultado correcto entre varios candidatos.

#### Criterios de Aceptación

1. THE Backend SHALL exponer un endpoint `GET /api/media/metadata-search` que acepte los parámetros `title` (obligatorio, string) y `media_type` (obligatorio, uno de "movie", "book", "series").
2. WHEN se recibe una petición válida al endpoint de búsqueda, THE Backend SHALL invocar al MetadataService y devolver una lista de hasta 5 MetadataCandidate en formato JSON, cada uno con los campos: `title`, `year`, `creator`, `description` e `image_url`.
3. WHEN el parámetro `title` está vacío o ausente, THE Backend SHALL responder con código HTTP 400 y un mensaje de error descriptivo.
4. IF la API externa (TMDB u Open Library) no responde dentro de 10 segundos, THEN THE MetadataService SHALL cancelar la petición y devolver una lista vacía de candidatos sin propagar el error al usuario.

### Requisito 4: Autocompletado de metadatos al crear un media item

**User Story:** Como usuario, quiero que al crear un media item con solo título y tipo, el backend rellene automáticamente año, creador y descripción, para ahorrar tiempo de entrada manual.

#### Criterios de Aceptación

1. WHEN se crea un media item mediante `POST /api/media` y los campos `year`, `creator` y `notes` no están proporcionados por el usuario, THE Backend SHALL invocar al MetadataService para buscar metadatos y rellenar automáticamente los campos `year`, `creator` y `notes` (con la descripción/sinopsis) usando el primer resultado encontrado.
2. WHEN se crea un media item y el usuario proporciona valores explícitos para `year`, `creator` o `notes`, THE Backend SHALL preservar los valores del usuario y no sobreescribirlos con datos de la API externa.
3. WHEN el MetadataService no encuentra resultados para el título y tipo proporcionados, THE Backend SHALL crear el media item con los campos de metadatos vacíos (null), sin generar un error.

### Requisito 5: Re-obtención de metadatos al actualizar título o tipo

**User Story:** Como usuario, quiero que al cambiar el título o tipo de un media item existente, el sistema re-obtenga los metadatos, para mantener la información actualizada.

#### Criterios de Aceptación

1. WHEN se actualiza un media item mediante `PUT /api/media/{id}` y el campo `title` o `media_type` ha cambiado, THE Backend SHALL invocar al MetadataService para buscar nuevos metadatos y actualizar los campos `year`, `creator` y `notes` con el primer resultado encontrado, solo si dichos campos no fueron proporcionados explícitamente en la petición de actualización.
2. WHEN se actualiza un media item y ni `title` ni `media_type` han cambiado, THE Backend SHALL omitir la búsqueda de metadatos y procesar la actualización normalmente.

### Requisito 6: Esquema de respuesta de MetadataCandidate

**User Story:** Como desarrollador frontend, quiero un esquema de respuesta claro y consistente para los candidatos de metadatos, para poder mostrar las sugerencias en la interfaz.

#### Criterios de Aceptación

1. THE MetadataCandidate SHALL contener los campos: `title` (string, obligatorio), `year` (integer o null), `creator` (string o null), `description` (string o null) e `image_url` (string o null).
2. THE Backend SHALL serializar la lista de MetadataCandidate usando un schema Pydantic validado, garantizando consistencia en el formato de respuesta.

### Requisito 7: Visualización de sugerencias en el frontend

**User Story:** Como usuario, quiero ver las sugerencias de metadatos en el formulario de creación, para poder elegir el resultado correcto y editarlo antes de guardar.

#### Criterios de Aceptación

1. WHEN el usuario ha introducido un título y seleccionado un tipo en el MediaForm, THE Frontend SHALL invocar el endpoint `GET /api/media/metadata-search` tras un debounce de 500ms sin actividad de escritura.
2. WHEN el endpoint devuelve una lista de MetadataCandidate, THE Frontend SHALL mostrar los candidatos en una lista desplegable debajo del campo de título, mostrando título, año y creador de cada candidato.
3. WHEN el usuario selecciona un candidato de la lista, THE Frontend SHALL rellenar los campos `year`, `creator` y `notes` del formulario con los valores del candidato seleccionado.
4. WHILE los campos del formulario están rellenados con datos de un candidato, THE Frontend SHALL permitir al usuario editar libremente cualquier campo antes de enviar el formulario.
5. WHEN el endpoint devuelve una lista vacía o un error, THE Frontend SHALL ocultar la lista de sugerencias sin mostrar un mensaje de error al usuario.

### Requisito 8: Manejo de errores en APIs externas

**User Story:** Como usuario, quiero que el sistema funcione correctamente aunque las APIs externas fallen, para que la creación de items no se bloquee por problemas de red.

#### Criterios de Aceptación

1. IF la API de TMDB devuelve un código de error HTTP (4xx o 5xx), THEN THE MetadataService SHALL registrar el error en los logs del servidor y devolver una lista vacía de candidatos.
2. IF la API de Open Library devuelve un código de error HTTP (4xx o 5xx), THEN THE MetadataService SHALL registrar el error en los logs del servidor y devolver una lista vacía de candidatos.
3. IF ocurre un error de conexión o timeout al contactar una API externa, THEN THE MetadataService SHALL registrar el error en los logs del servidor y devolver una lista vacía de candidatos sin interrumpir el flujo de creación o actualización del media item.
