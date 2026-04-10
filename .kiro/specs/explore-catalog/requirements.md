# Documento de Requisitos — Explore Catalog

## Introducción

La funcionalidad "Explore" añade una nueva vista de catálogo global a Personal Shelf. Permite a los usuarios autenticados descubrir contenido multimedia que otros usuarios han añadido a la plataforma, sin exponer datos privados de ningún usuario. Los items se agrupan por combinación de título y tipo de media para evitar duplicados. La vista ofrece filtrado por tipo de media, ordenación alfabética y ordenación por señales sociales (cuántos amigos del usuario tienen el item o se lo han recomendado). Se apoya en la infraestructura existente de `MediaItem`, `Recommendation` y `friendships`, sin requerir nuevos modelos de base de datos.

## Glosario

- **Explore_Service**: Servicio backend que ejecuta las queries globales de catálogo, deduplicación, conteo de señales sociales, filtrado, ordenación y paginación.
- **Explore_Endpoint**: Endpoint HTTP `GET /api/explore` que expone el catálogo global con parámetros de filtro, orden y paginación.
- **Explore_View**: Vista frontend Vue 3 que muestra el catálogo global con controles de filtro y ordenación.
- **Explore_Card**: Componente frontend que representa un item del catálogo global, incluyendo señales sociales.
- **Catálogo_Global**: Conjunto de items multimedia agregados de todos los usuarios, deduplicados por la combinación (título normalizado, tipo de media).
- **Señales_Sociales**: Datos derivados de las relaciones de amistad y recomendaciones: cantidad de amigos que poseen un item y cantidad de amigos que lo han recomendado al usuario actual.
- **Ordenación_Por_Amigos**: Criterio de ordenación que usa la suma de señales sociales (amigos que lo tienen + amigos que lo recomendaron) como valor de ranking.
- **Item_Deduplicado**: Representación única de un item multimedia en el catálogo global, resultado de agrupar por (título case-insensitive, media_type).

## Requisitos

### Requisito 1: Endpoint del catálogo global

**Historia de Usuario:** Como usuario autenticado, quiero consultar un catálogo global de items multimedia de toda la plataforma, para descubrir contenido que otros usuarios han añadido.

#### Criterios de Aceptación

1. WHEN un usuario autenticado envía una petición GET a `/api/explore`, THE Explore_Endpoint SHALL devolver una respuesta paginada con items del Catálogo_Global.
2. THE Explore_Endpoint SHALL aceptar los parámetros de query `page` (entero >= 1, default 1) y `size` (entero entre 1 y 100, default 20) para controlar la paginación.
3. THE Explore_Endpoint SHALL devolver un objeto JSON con los campos `items` (lista de Item_Deduplicado), `total` (entero), `page` (entero), `size` (entero) y `pages` (entero).
4. IF un usuario no autenticado envía una petición GET a `/api/explore`, THEN THE Explore_Endpoint SHALL devolver un código de estado 401.

### Requisito 2: Deduplicación de items

**Historia de Usuario:** Como usuario, quiero ver cada título multimedia una sola vez en el catálogo global, para no encontrar duplicados cuando varios usuarios tienen el mismo item.

#### Criterios de Aceptación

1. THE Explore_Service SHALL agrupar los items del Catálogo_Global por la combinación de título (comparación case-insensitive) y media_type.
2. WHEN existen múltiples items con el mismo título normalizado y media_type, THE Explore_Service SHALL seleccionar un único representante por grupo, priorizando el item con imagen disponible (image_path no nulo).
3. THE Explore_Service SHALL incluir en cada Item_Deduplicado los campos: título, media_type, año, creador, image_url y señales sociales.

### Requisito 3: Filtrado por tipo de media

**Historia de Usuario:** Como usuario, quiero filtrar el catálogo global por tipo de media (película, libro, serie), para encontrar contenido del tipo que me interesa.

#### Criterios de Aceptación

1. THE Explore_Endpoint SHALL aceptar un parámetro de query `media_type` con valores válidos `movie`, `book` o `series`.
2. WHEN el parámetro `media_type` está presente, THE Explore_Service SHALL devolver únicamente items cuyo media_type coincida con el valor proporcionado.
3. WHEN el parámetro `media_type` no está presente, THE Explore_Service SHALL devolver items de todos los tipos de media.
4. IF el parámetro `media_type` contiene un valor no válido, THEN THE Explore_Endpoint SHALL devolver un código de estado 422 con un mensaje descriptivo.

### Requisito 4: Búsqueda por título

**Historia de Usuario:** Como usuario, quiero buscar items en el catálogo global por título, para encontrar contenido específico que me interesa.

#### Criterios de Aceptación

1. THE Explore_Endpoint SHALL aceptar un parámetro de query `search` de tipo string.
2. WHEN el parámetro `search` está presente, THE Explore_Service SHALL devolver únicamente items cuyo título contenga el texto proporcionado (comparación case-insensitive, coincidencia parcial).
3. WHEN el parámetro `search` no está presente, THE Explore_Service SHALL devolver items sin restricción de título.

### Requisito 5: Ordenación alfabética

**Historia de Usuario:** Como usuario, quiero ordenar el catálogo global alfabéticamente (A→Z o Z→A), para navegar el contenido de forma organizada.

#### Criterios de Aceptación

1. THE Explore_Endpoint SHALL aceptar un parámetro de query `sort` con valores válidos `title_asc`, `title_desc` y `friends`.
2. WHEN el parámetro `sort` tiene el valor `title_asc`, THE Explore_Service SHALL ordenar los items alfabéticamente por título de forma ascendente (A→Z).
3. WHEN el parámetro `sort` tiene el valor `title_desc`, THE Explore_Service SHALL ordenar los items alfabéticamente por título de forma descendente (Z→A).
4. WHEN el parámetro `sort` no está presente, THE Explore_Service SHALL usar `title_asc` como ordenación por defecto.

### Requisito 6: Ordenación por recomendaciones de amigos

**Historia de Usuario:** Como usuario, quiero ordenar el catálogo global por relevancia social (cuántos amigos lo tienen o me lo han recomendado), para descubrir contenido popular entre mis amigos.

#### Criterios de Aceptación

1. WHEN el parámetro `sort` tiene el valor `friends`, THE Explore_Service SHALL ordenar los items por la suma de señales sociales de forma descendente (mayor cantidad primero).
2. THE Explore_Service SHALL calcular las Señales_Sociales de cada Item_Deduplicado como la suma de: (a) cantidad de amigos del usuario actual que poseen un item con el mismo título y media_type, y (b) cantidad de amigos del usuario actual que le han recomendado un item con el mismo título y media_type.
3. WHEN dos items tienen la misma suma de señales sociales, THE Explore_Service SHALL usar el título ascendente como criterio de desempate.
4. WHEN el usuario no tiene amigos, THE Explore_Service SHALL asignar un valor de 0 a las señales sociales de todos los items y ordenar alfabéticamente por título.

### Requisito 7: Señales sociales en cada item

**Historia de Usuario:** Como usuario, quiero ver cuántos amigos tienen un item y cuántos me lo han recomendado, para tomar decisiones informadas sobre qué contenido explorar.

#### Criterios de Aceptación

1. THE Explore_Service SHALL incluir en cada Item_Deduplicado un campo `friends_have` (entero) que represente la cantidad de amigos del usuario actual que poseen un item con el mismo título y media_type.
2. THE Explore_Service SHALL incluir en cada Item_Deduplicado un campo `friends_recommended` (entero) que represente la cantidad de amigos del usuario actual que le han enviado una recomendación de un item con el mismo título y media_type.
3. WHEN el usuario no tiene amigos, THE Explore_Service SHALL devolver 0 en ambos campos de señales sociales para todos los items.

### Requisito 8: Vista frontend de Explore

**Historia de Usuario:** Como usuario, quiero acceder a una vista "Explore" desde la navegación principal, para descubrir contenido nuevo de forma visual.

#### Criterios de Aceptación

1. THE Explore_View SHALL estar accesible en la ruta `/explore` del frontend.
2. THE Explore_View SHALL mostrar una cuadrícula de Explore_Card con los items del Catálogo_Global.
3. THE Explore_View SHALL incluir un control de filtro por tipo de media (Todos, Película, Libro, Serie).
4. THE Explore_View SHALL incluir un control de ordenación con las opciones: Alfabético A→Z, Alfabético Z→A y Por amigos.
5. THE Explore_View SHALL incluir un campo de búsqueda por título.
6. THE Explore_View SHALL incluir controles de paginación consistentes con el componente Pagination existente.
7. WHILE los datos se están cargando, THE Explore_View SHALL mostrar un indicador de carga con `role="status"`.
8. IF la petición al Explore_Endpoint falla, THEN THE Explore_View SHALL mostrar un mensaje de error con `role="alert"`.
9. WHEN no existen items que coincidan con los filtros aplicados, THE Explore_View SHALL mostrar un mensaje indicando que no se encontraron resultados.

### Requisito 9: Tarjeta de item en Explore

**Historia de Usuario:** Como usuario, quiero ver información relevante de cada item en el catálogo global, incluyendo señales sociales, para evaluar el contenido.

#### Criterios de Aceptación

1. THE Explore_Card SHALL mostrar el título, tipo de media, año (cuando esté disponible), creador (cuando esté disponible) e imagen del item.
2. WHEN el campo `friends_have` del item es mayor que 0, THE Explore_Card SHALL mostrar el texto "N amigos lo tienen" donde N es el valor de `friends_have`.
3. WHEN el campo `friends_recommended` del item es mayor que 0, THE Explore_Card SHALL mostrar el texto "N amigos te lo recomendaron" donde N es el valor de `friends_recommended`.
4. WHEN ambos campos de señales sociales son 0, THE Explore_Card SHALL omitir la sección de señales sociales.
5. THE Explore_Card SHALL mostrar una imagen placeholder apropiada al tipo de media cuando el item no tenga imagen disponible.

### Requisito 10: Enlace de navegación en el sidebar

**Historia de Usuario:** Como usuario autenticado, quiero acceder a la vista Explore desde el menú lateral, para navegar fácilmente al catálogo global.

#### Criterios de Aceptación

1. WHILE el usuario está autenticado, THE Explore_View SHALL aparecer como enlace en la navegación del sidebar, en la sección social (junto a Feed, Friends y Recommendations).
2. THE Explore_View SHALL mostrar un icono representativo y la etiqueta "Explore" en el sidebar.
3. WHEN el sidebar está colapsado, THE Explore_View SHALL mostrar únicamente el icono con un atributo `title` con el valor "Explore".
