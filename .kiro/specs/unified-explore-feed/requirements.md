# Documento de Requisitos — Feed Unificado en Explore

## Introducción

Actualmente la aplicación tiene dos vistas sociales separadas: **Feed** (actividad reciente de amigos) y **Explore** (catálogo global deduplicado con señales sociales). El usuario ha identificado que ambas vistas se pueden combinar en una sola vista "Explore" unificada. Los items que los amigos están consumiendo activamente (leyendo, viendo) aparecerán dentro del catálogo Explore con indicadores visuales que muestran qué amigo(s) específico(s) lo están haciendo, en lugar de solo mostrar conteos numéricos.

## Glosario

- **Explore_Unificado**: La vista combinada que reemplaza las vistas Feed y Explore actuales, mostrando el catálogo global con indicadores de actividad de amigos.
- **ExploreService**: Servicio backend que gestiona el catálogo global deduplicado con señales sociales, filtros, ordenación y paginación.
- **FeedService**: Servicio backend actual que consulta la actividad reciente de amigos (items con estado in_progress/completed en los últimos 30 días).
- **Señal_Social**: Información sobre la relación de amigos con un item del catálogo (cuántos lo tienen, cuántos lo recomendaron).
- **Indicador_Actividad**: Información visual que muestra qué amigo(s) específico(s) están consumiendo activamente un item (nombre de usuario y/o avatar).
- **Item_Activo**: Un MediaItem de un amigo cuyo estado es `in_progress` (actualmente leyendo, viendo o siguiendo).
- **Amigo_Activo**: Un amigo que tiene un item con estado `in_progress` que coincide con un item del catálogo Explore por `(LOWER(title), media_type)`.
- **ExploreItem**: Schema Pydantic que representa un item deduplicado en el catálogo global.
- **ExploreCard**: Componente Vue que renderiza un ExploreItem en la cuadrícula de Explore.
- **Sidebar**: Barra lateral de navegación principal de la aplicación definida en App.vue.

## Requisitos

### Requisito 1: Extender el endpoint Explore con datos de amigos activos

**User Story:** Como usuario autenticado, quiero que el endpoint de Explore incluya información sobre qué amigos están consumiendo activamente cada item, para poder ver esa información en la vista unificada.

#### Criterios de Aceptación

1. WHEN el usuario autenticado solicita el catálogo Explore, THE ExploreService SHALL incluir en cada ExploreItem una lista de Amigos_Activos que tienen un item coincidente por `(LOWER(title), media_type)` con estado `in_progress`.
2. THE ExploreService SHALL devolver para cada Amigo_Activo el `user_id` y el `username` del amigo.
3. WHEN un item del catálogo no tiene ningún Amigo_Activo, THE ExploreService SHALL devolver una lista vacía de Amigos_Activos para ese item.
4. WHEN el usuario no tiene amigos, THE ExploreService SHALL devolver una lista vacía de Amigos_Activos para todos los items.
5. THE ExploreService SHALL calcular los Amigos_Activos utilizando únicamente items de amigos confirmados del usuario (tabla `friendships`).

### Requisito 2: Schema ExploreItem extendido

**User Story:** Como desarrollador, quiero que el schema ExploreItem incluya la información de amigos activos, para que el frontend pueda renderizar los indicadores de actividad.

#### Criterios de Aceptación

1. THE ExploreItem SHALL incluir un campo `friends_reading` de tipo lista de objetos con `user_id` (entero) y `username` (cadena de texto).
2. THE ExploreItem SHALL mantener los campos existentes (`title`, `media_type`, `year`, `creator`, `image_url`, `tags`, `friends_have`, `friends_recommended`) sin modificaciones.
3. WHEN el campo `friends_reading` está vacío, THE ExploreItem SHALL serializar el campo como una lista vacía `[]`.

### Requisito 3: Indicador visual de amigos activos en ExploreCard

**User Story:** Como usuario, quiero ver qué amigos específicos están leyendo o viendo un item en el catálogo Explore, para descubrir contenido a través de la actividad de mis amigos.

#### Criterios de Aceptación

1. WHEN un ExploreItem tiene uno o más Amigos_Activos, THE ExploreCard SHALL mostrar una sección de indicadores de actividad con los nombres de usuario de los amigos.
2. WHEN un ExploreItem tiene un solo Amigo_Activo, THE ExploreCard SHALL mostrar el texto con el formato `"{username} lo está viendo/leyendo"` según el `media_type` del item.
3. WHEN un ExploreItem tiene dos Amigos_Activos, THE ExploreCard SHALL mostrar el texto con el formato `"{username1} y {username2} lo están viendo/leyendo"`.
4. WHEN un ExploreItem tiene tres o más Amigos_Activos, THE ExploreCard SHALL mostrar el texto con el formato `"{username1}, {username2} y N más lo están viendo/leyendo"`.
5. THE ExploreCard SHALL utilizar el verbo "leyendo" para items de tipo `book` y "viendo" para items de tipo `movie` o `series`.
6. WHEN un ExploreItem no tiene Amigos_Activos, THE ExploreCard SHALL ocultar la sección de indicadores de actividad.
7. THE ExploreCard SHALL mostrar la sección de indicadores de actividad visualmente diferenciada de las señales sociales existentes (`friends_have`, `friends_recommended`).

### Requisito 4: Ordenación por actividad de amigos

**User Story:** Como usuario, quiero poder ordenar el catálogo Explore por actividad de amigos, para ver primero los items que mis amigos están consumiendo activamente.

#### Criterios de Aceptación

1. WHEN el usuario selecciona la ordenación "Por actividad de amigos", THE ExploreService SHALL ordenar los items por el número de Amigos_Activos en orden descendente.
2. WHEN dos items tienen el mismo número de Amigos_Activos, THE ExploreService SHALL desempatar por la suma de `friends_have` + `friends_recommended` en orden descendente.
3. WHEN dos items empatan en ambos criterios, THE ExploreService SHALL desempatar por `LOWER(title)` en orden ascendente.
4. THE Explore_Unificado SHALL ofrecer la opción de ordenación "Por actividad" en el selector de ordenación, además de las opciones existentes (A→Z, Z→A, Por amigos).

### Requisito 5: Eliminar la vista Feed y su entrada en la navegación

**User Story:** Como usuario, quiero que la navegación sea más simple al tener una sola vista social unificada en lugar de dos vistas separadas.

#### Criterios de Aceptación

1. THE Sidebar SHALL eliminar el enlace de navegación "Feed" de la barra lateral.
2. THE Explore_Unificado SHALL mantener el enlace "Explore" en la Sidebar en su posición actual.
3. WHEN un usuario navega a la ruta `/feed`, THE Explore_Unificado SHALL redirigir automáticamente a la ruta `/explore`.
4. THE Sidebar SHALL mantener todos los demás enlaces de navegación sin cambios (Catalog, Statistics, Explore, Suggestions, Friends, Recommendations).

### Requisito 6: Mantener funcionalidad existente de Explore

**User Story:** Como usuario, quiero que todas las funcionalidades actuales de Explore sigan funcionando después de la unificación.

#### Criterios de Aceptación

1. THE Explore_Unificado SHALL mantener el filtro por tipo de media (`movie`, `book`, `series`).
2. THE Explore_Unificado SHALL mantener la búsqueda por título (case-insensitive, parcial).
3. THE Explore_Unificado SHALL mantener el filtro por tag.
4. THE Explore_Unificado SHALL mantener la paginación con los controles existentes.
5. THE Explore_Unificado SHALL mantener la funcionalidad de añadir items al catálogo personal ("Add to shelf").
6. THE Explore_Unificado SHALL mantener la deduplicación por `(LOWER(title), media_type)`.
7. THE Explore_Unificado SHALL mantener las señales sociales existentes (`friends_have`, `friends_recommended`).

### Requisito 7: Endpoint Feed preservado para compatibilidad

**User Story:** Como desarrollador, quiero que el endpoint `/api/feed` siga existiendo temporalmente para no romper posibles integraciones externas.

#### Criterios de Aceptación

1. THE FeedService SHALL seguir disponible en el endpoint `GET /api/feed` sin cambios en su comportamiento.
2. THE FeedService SHALL seguir devolviendo la actividad reciente de amigos con el formato `FeedResponse` existente.

### Requisito 8: Destacar items con actividad de amigos en la cuadrícula

**User Story:** Como usuario, quiero que los items que mis amigos están consumiendo activamente se destaquen visualmente en la cuadrícula de Explore.

#### Criterios de Aceptación

1. WHEN un ExploreItem tiene uno o más Amigos_Activos, THE ExploreCard SHALL aplicar un estilo visual diferenciado (borde o fondo sutil) que distinga el item de los que no tienen actividad de amigos.
2. THE ExploreCard SHALL utilizar un indicador visual (icono o emoji) junto a los nombres de los Amigos_Activos para reforzar que se trata de actividad en curso.
3. THE ExploreCard SHALL mantener la accesibilidad del indicador de actividad con un atributo `aria-label` descriptivo en la sección de Amigos_Activos.

### Requisito 9: Propiedades de correctitud

**User Story:** Como desarrollador, quiero validar la correctitud de la lógica de unificación mediante property-based testing.

#### Criterios de Aceptación

1. FOR ALL conjuntos de MediaItems y amistades generados, THE ExploreService SHALL devolver `friends_reading` que contenga únicamente amigos confirmados del usuario con items en estado `in_progress` que coincidan por `(LOWER(title), media_type)`.
2. FOR ALL ExploreItems devueltos, THE ExploreService SHALL garantizar que la longitud de `friends_reading` sea menor o igual al número total de amigos del usuario.
3. FOR ALL ExploreItems devueltos con ordenación "activity", THE ExploreService SHALL garantizar que el número de Amigos_Activos del item N sea mayor o igual al del item N+1.
4. FOR ALL ExploreItems devueltos, THE ExploreService SHALL garantizar que `friends_reading` no contenga el propio usuario.
5. FOR ALL ExploreItems devueltos, THE ExploreService SHALL garantizar que no existan duplicados de `user_id` dentro de la lista `friends_reading` de un mismo item.
