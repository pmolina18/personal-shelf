# Documento de Requisitos — Tests Unitarios del Frontend

## Introducción

El frontend de "Personal Shelf" (Vue 3 + Vite) carece actualmente de tests unitarios. Este documento define los requisitos para implementar una suite completa de tests unitarios que cubra la capa API, los composables, los componentes y las vistas de la aplicación. Se utilizará Vitest como runner de tests y @vue/test-utils para el montaje de componentes Vue.

## Glosario

- **Suite_De_Tests**: Conjunto completo de archivos de test unitarios del frontend, ejecutados con Vitest.
- **Runner_De_Tests**: Vitest, el framework de testing integrado con Vite que ejecuta los tests.
- **Utilidades_De_Test_Vue**: Librería @vue/test-utils para montar y manipular componentes Vue en tests.
- **Capa_API**: Módulo `src/api/media.js` que encapsula todas las llamadas HTTP al backend mediante fetch nativo.
- **Composable_UseMedia**: Función `useMedia()` en `src/composables/useMedia.js` que gestiona estado reactivo, paginación, filtros y operaciones CRUD.
- **Componente**: Archivo `.vue` reutilizable en `src/components/` (ConfirmDialog, FilterBar, MediaCard, MediaForm, Pagination, RatingInput, TagInput).
- **Vista**: Archivo `.vue` en `src/views/` que representa una página completa (CatalogView, MediaDetailView, StatsView, ImportExportView).
- **Mock**: Sustituto de una dependencia real (fetch, API, router) utilizado para aislar la unidad bajo test.
- **Configuración_De_Tests**: Archivos de configuración necesarios para ejecutar Vitest (vitest.config, setup files, dependencias en package.json).

## Requisitos

### Requisito 1: Configuración del Entorno de Tests

**Historia de Usuario:** Como desarrollador, quiero tener un entorno de tests unitarios configurado y funcional, para poder ejecutar tests de forma rápida y fiable.

#### Criterios de Aceptación

1. THE Configuración_De_Tests SHALL incluir Vitest y @vue/test-utils como dependencias de desarrollo en `package.json`.
2. THE Configuración_De_Tests SHALL definir un script `test` en `package.json` que ejecute Vitest en modo de ejecución única.
3. THE Configuración_De_Tests SHALL incluir un archivo de configuración de Vitest con soporte para componentes Vue y resolución de alias.
4. THE Configuración_De_Tests SHALL incluir un archivo setup global que configure el entorno jsdom para tests de componentes.
5. WHEN un desarrollador ejecuta el comando `npm test`, THE Runner_De_Tests SHALL ejecutar todos los archivos de test y reportar resultados sin errores de configuración.

### Requisito 2: Tests de la Capa API

**Historia de Usuario:** Como desarrollador, quiero tests unitarios para el módulo API, para verificar que las llamadas HTTP se construyen correctamente y los errores se manejan de forma adecuada.

#### Criterios de Aceptación

1. WHEN la función `request()` recibe una respuesta exitosa, THE Suite_De_Tests SHALL verificar que el JSON se parsea y retorna correctamente.
2. WHEN la función `request()` recibe una respuesta con status 204, THE Suite_De_Tests SHALL verificar que retorna `null` sin intentar parsear el cuerpo.
3. WHEN la función `request()` recibe una respuesta con error (status no-ok), THE Suite_De_Tests SHALL verificar que lanza un Error con el mensaje `detail` del servidor.
4. WHEN se invoca `listMedia` con parámetros de filtro, THE Suite_De_Tests SHALL verificar que los parámetros no vacíos se incluyen como query string en la URL.
5. WHEN se invoca `listMedia` con parámetros vacíos o nulos, THE Suite_De_Tests SHALL verificar que dichos parámetros se omiten del query string.
6. WHEN se invoca `createMedia` con un cuerpo, THE Suite_De_Tests SHALL verificar que se envía una petición POST con el cuerpo serializado como JSON.
7. WHEN se invoca `updateMedia` con un ID y cuerpo, THE Suite_De_Tests SHALL verificar que se envía una petición PUT al endpoint correcto.
8. WHEN se invoca `deleteMedia` con un ID, THE Suite_De_Tests SHALL verificar que se envía una petición DELETE y retorna null.
9. WHEN se invoca `updateStatus`, `updateRating` o `updateTags`, THE Suite_De_Tests SHALL verificar que se envía una petición PATCH o PUT al sub-endpoint correspondiente con el payload correcto.
10. WHEN se invoca `exportCatalog` o `importCatalog`, THE Suite_De_Tests SHALL verificar que se utilizan los métodos HTTP y endpoints correctos.

### Requisito 3: Tests del Composable useMedia

**Historia de Usuario:** Como desarrollador, quiero tests unitarios para el composable `useMedia`, para asegurar que el estado reactivo, la paginación y las operaciones CRUD funcionan correctamente.

#### Criterios de Aceptación

1. WHEN se invoca `useMedia()` dos veces, THE Suite_De_Tests SHALL verificar que cada invocación retorna instancias de estado independientes (refs distintos).
2. WHEN se invoca `fetchMedia`, THE Suite_De_Tests SHALL verificar que `loading` cambia a `true` durante la petición y a `false` al completarse.
3. WHEN `fetchMedia` se completa exitosamente, THE Suite_De_Tests SHALL verificar que `items`, `total` y `pages` se actualizan con los datos de la respuesta.
4. WHEN `fetchMedia` falla, THE Suite_De_Tests SHALL verificar que `error` contiene el mensaje de error y `loading` es `false`.
5. WHEN se invoca `setFilters` con nuevos filtros, THE Suite_De_Tests SHALL verificar que `page` se reinicia a 1 y se invoca `fetchMedia` con los filtros actualizados.
6. WHEN se invoca `setPage` con un nuevo número de página, THE Suite_De_Tests SHALL verificar que `page` se actualiza y se invoca `fetchMedia`.
7. THE Suite_De_Tests SHALL verificar que `hasActiveFilters` retorna `true` cuando al menos un filtro tiene valor y `false` cuando todos son nulos.
8. WHEN se invoca `fetchItem` con un ID, THE Suite_De_Tests SHALL verificar que `currentItem` se actualiza con los datos del servidor y `itemLoading` refleja el estado de carga.
9. WHEN se invoca `update` exitosamente, THE Suite_De_Tests SHALL verificar que `currentItem` se actualiza y `successMsg` muestra un mensaje temporal.
10. WHEN se invoca `changeStatus`, `changeRating` o `changeTags` exitosamente, THE Suite_De_Tests SHALL verificar que `currentItem` se actualiza y se muestra un mensaje de éxito.
11. WHEN una operación de item falla, THE Suite_De_Tests SHALL verificar que `itemError` contiene el mensaje de error.
12. WHEN se invoca `create` con datos, THE Suite_De_Tests SHALL verificar que retorna el objeto creado por la API.
13. WHEN se invoca `remove` con un ID, THE Suite_De_Tests SHALL verificar que se invoca `deleteMedia` de la capa API.

### Requisito 4: Tests del Componente ConfirmDialog

**Historia de Usuario:** Como desarrollador, quiero tests para ConfirmDialog, para verificar que el diálogo modal se renderiza, gestiona el foco y emite eventos correctamente.

#### Criterios de Aceptación

1. WHEN la prop `open` es `false`, THE Suite_De_Tests SHALL verificar que el diálogo no se renderiza en el DOM.
2. WHEN la prop `open` es `true`, THE Suite_De_Tests SHALL verificar que el diálogo se renderiza con el título y mensaje proporcionados.
3. WHEN el usuario hace clic en el botón "Confirm", THE Suite_De_Tests SHALL verificar que se emite el evento `confirm`.
4. WHEN el usuario hace clic en el botón "Cancel", THE Suite_De_Tests SHALL verificar que se emite el evento `cancel`.
5. WHEN el usuario hace clic en el overlay (fuera del diálogo), THE Suite_De_Tests SHALL verificar que se emite el evento `cancel`.
6. THE Suite_De_Tests SHALL verificar que el diálogo tiene los atributos ARIA correctos (`role="dialog"`, `aria-modal="true"`, `aria-label`).

### Requisito 5: Tests del Componente FilterBar

**Historia de Usuario:** Como desarrollador, quiero tests para FilterBar, para verificar que los filtros emiten los valores correctos al interactuar con los campos.

#### Criterios de Aceptación

1. THE Suite_De_Tests SHALL verificar que FilterBar renderiza los cuatro campos de filtro (búsqueda, tipo, estado, tag).
2. WHEN el usuario escribe en el campo de búsqueda, THE Suite_De_Tests SHALL verificar que se emite `update:filters` con el valor de búsqueda en la propiedad `search`.
3. WHEN el usuario selecciona un tipo de medio, THE Suite_De_Tests SHALL verificar que se emite `update:filters` con el valor en la propiedad `media_type`.
4. WHEN el usuario selecciona un estado, THE Suite_De_Tests SHALL verificar que se emite `update:filters` con el valor en la propiedad `status`.
5. WHEN un campo de filtro está vacío, THE Suite_De_Tests SHALL verificar que la propiedad correspondiente en el payload emitido es `null`.

### Requisito 6: Tests del Componente MediaCard

**Historia de Usuario:** Como desarrollador, quiero tests para MediaCard, para verificar que muestra correctamente la información del medio y genera los enlaces adecuados.

#### Criterios de Aceptación

1. WHEN se proporciona un item, THE Suite_De_Tests SHALL verificar que MediaCard renderiza el título, las etiquetas de tipo y estado, y el enlace al detalle.
2. WHEN el item tiene un rating, THE Suite_De_Tests SHALL verificar que se muestra la puntuación con formato "★ N/10".
3. WHEN el item no tiene rating, THE Suite_De_Tests SHALL verificar que la sección de rating no se renderiza.
4. WHEN el item no tiene `image_url`, THE Suite_De_Tests SHALL verificar que se utiliza la imagen placeholder correspondiente al tipo de medio.
5. THE Suite_De_Tests SHALL verificar que el `router-link` apunta a `/media/{id}` con el ID del item.
6. THE Suite_De_Tests SHALL verificar que las etiquetas computadas (`typeLabel`, `statusLabel`) mapean correctamente los valores internos a etiquetas legibles.

### Requisito 7: Tests del Componente MediaForm

**Historia de Usuario:** Como desarrollador, quiero tests para MediaForm, para verificar la validación, la población de datos iniciales y la emisión del formulario.

#### Criterios de Aceptación

1. WHEN se renderiza sin `initialData`, THE Suite_De_Tests SHALL verificar que el formulario muestra campos vacíos y el botón dice "Create".
2. WHEN se proporciona `initialData`, THE Suite_De_Tests SHALL verificar que los campos se populan con los datos proporcionados y el botón dice "Save Changes".
3. WHEN el usuario envía el formulario sin título, THE Suite_De_Tests SHALL verificar que se muestra el error de validación "Title is required" y no se emite el evento `submit`.
4. WHEN el usuario envía el formulario con un título válido, THE Suite_De_Tests SHALL verificar que se emite el evento `submit` con los datos del formulario correctamente formateados.
5. WHEN la prop `initialData` cambia después del montaje, THE Suite_De_Tests SHALL verificar que los campos del formulario se actualizan con los nuevos datos.
6. THE Suite_De_Tests SHALL verificar que los valores opcionales vacíos (year, creator, notes) se emiten como `null` en el payload.

### Requisito 8: Tests del Componente Pagination

**Historia de Usuario:** Como desarrollador, quiero tests para Pagination, para verificar la navegación de páginas y el cálculo de la ventana de páginas visibles.

#### Criterios de Aceptación

1. WHEN `pages` es 1 o menor, THE Suite_De_Tests SHALL verificar que el componente no se renderiza.
2. WHEN `pages` es mayor que 1, THE Suite_De_Tests SHALL verificar que se muestra el total de items y los controles de paginación.
3. WHEN el usuario está en la primera página, THE Suite_De_Tests SHALL verificar que el botón "Prev" está deshabilitado.
4. WHEN el usuario está en la última página, THE Suite_De_Tests SHALL verificar que el botón "Next" está deshabilitado.
5. WHEN el usuario hace clic en un número de página, THE Suite_De_Tests SHALL verificar que se emite `update:page` con el número de página seleccionado.
6. THE Suite_De_Tests SHALL verificar que `visiblePages` calcula correctamente la ventana de ±2 páginas alrededor de la página actual.
7. THE Suite_De_Tests SHALL verificar que `visiblePages` no incluye páginas menores que 1 ni mayores que el total de páginas.

### Requisito 9: Tests del Componente RatingInput

**Historia de Usuario:** Como desarrollador, quiero tests para RatingInput, para verificar la selección de estrellas y el estado deshabilitado.

#### Criterios de Aceptación

1. THE Suite_De_Tests SHALL verificar que RatingInput renderiza 10 botones de estrella cuando no está deshabilitado.
2. WHEN la prop `disabled` es `true`, THE Suite_De_Tests SHALL verificar que se muestra el mensaje de estado deshabilitado en lugar de las estrellas.
3. WHEN el usuario hace clic en una estrella, THE Suite_De_Tests SHALL verificar que se emite `update:modelValue` con el número de estrella correspondiente (1-10).
4. WHEN `modelValue` tiene un valor, THE Suite_De_Tests SHALL verificar que las estrellas hasta ese valor tienen la clase `active` y se muestra el texto "N/10".

### Requisito 10: Tests del Componente TagInput

**Historia de Usuario:** Como desarrollador, quiero tests para TagInput, para verificar la adición, eliminación y validación de tags.

#### Criterios de Aceptación

1. WHEN se proporcionan tags en `modelValue`, THE Suite_De_Tests SHALL verificar que cada tag se renderiza como un chip con botón de eliminación.
2. WHEN el usuario escribe un tag y presiona Enter, THE Suite_De_Tests SHALL verificar que se emite `update:modelValue` con el array de tags actualizado incluyendo el nuevo tag.
3. WHEN el usuario intenta agregar un tag duplicado, THE Suite_De_Tests SHALL verificar que no se emite `update:modelValue` y el campo se limpia.
4. WHEN el número de tags alcanza el límite `max`, THE Suite_De_Tests SHALL verificar que se muestra el mensaje de límite y no se permite agregar más tags.
5. WHEN el usuario hace clic en el botón de eliminar de un tag, THE Suite_De_Tests SHALL verificar que se emite `update:modelValue` con el array sin el tag eliminado.
6. WHEN el campo de entrada está vacío, THE Suite_De_Tests SHALL verificar que el botón "Add" está deshabilitado.

### Requisito 11: Tests de la Vista CatalogView

**Historia de Usuario:** Como desarrollador, quiero tests para CatalogView, para verificar la integración con el composable, los estados de carga y los estados vacíos.

#### Criterios de Aceptación

1. WHEN la vista se monta, THE Suite_De_Tests SHALL verificar que se invoca `fetchMedia` del composable.
2. WHILE `loading` es `true`, THE Suite_De_Tests SHALL verificar que se muestra el indicador de carga.
3. WHEN `error` tiene un valor, THE Suite_De_Tests SHALL verificar que se muestra el mensaje de error.
4. WHEN `items` está vacío y no hay filtros activos, THE Suite_De_Tests SHALL verificar que se muestra el estado vacío con enlace para agregar el primer item.
5. WHEN `items` está vacío y hay filtros activos, THE Suite_De_Tests SHALL verificar que se muestra el mensaje "No items match your filters".
6. WHEN `items` tiene elementos, THE Suite_De_Tests SHALL verificar que se renderiza un MediaCard por cada item y el componente Pagination.

### Requisito 12: Tests de la Vista MediaDetailView

**Historia de Usuario:** Como desarrollador, quiero tests para MediaDetailView, para verificar los modos de creación y edición, las operaciones de estado y la confirmación de eliminación.

#### Criterios de Aceptación

1. WHEN la ruta es `media-create`, THE Suite_De_Tests SHALL verificar que se muestra el formulario en modo creación con el título "Add Media".
2. WHEN la ruta tiene un ID de medio, THE Suite_De_Tests SHALL verificar que se invoca `fetchItem` con el ID y se muestra el formulario con los datos cargados.
3. WHEN el usuario envía el formulario en modo creación, THE Suite_De_Tests SHALL verificar que se invoca `create` y se navega al detalle del item creado.
4. WHEN el usuario hace clic en "Delete item" y confirma, THE Suite_De_Tests SHALL verificar que se invoca `remove` y se navega al catálogo.
5. WHILE se carga el item, THE Suite_De_Tests SHALL verificar que se muestra el indicador de carga.
6. WHEN hay un error de carga, THE Suite_De_Tests SHALL verificar que se muestra el mensaje de error.

### Requisito 13: Tests de la Vista StatsView

**Historia de Usuario:** Como desarrollador, quiero tests para StatsView, para verificar la carga y presentación de estadísticas.

#### Criterios de Aceptación

1. WHEN la vista se monta, THE Suite_De_Tests SHALL verificar que se invoca `getStats` de la capa API.
2. WHEN las estadísticas se cargan exitosamente, THE Suite_De_Tests SHALL verificar que se muestran las secciones by_type, by_status y avg_rating_by_type.
3. THE Suite_De_Tests SHALL verificar que `totalItems` se calcula como la suma de los valores de `by_type`.
4. THE Suite_De_Tests SHALL verificar que `formatLabel` convierte claves como "in_progress" a "In Progress".
5. WHILE se cargan las estadísticas, THE Suite_De_Tests SHALL verificar que se muestra el indicador de carga.
6. WHEN la carga de estadísticas falla, THE Suite_De_Tests SHALL verificar que se muestra el mensaje de error.

### Requisito 14: Tests de la Vista ImportExportView

**Historia de Usuario:** Como desarrollador, quiero tests para ImportExportView, para verificar la exportación a archivo JSON y la importación desde archivo con manejo de errores.

#### Criterios de Aceptación

1. WHEN el usuario hace clic en "Export Catalog", THE Suite_De_Tests SHALL verificar que se invoca `exportCatalog` y se crea un enlace de descarga con el blob JSON.
2. WHEN la exportación falla, THE Suite_De_Tests SHALL verificar que se muestra el mensaje de error.
3. WHEN el usuario selecciona un archivo JSON válido y hace clic en "Import", THE Suite_De_Tests SHALL verificar que se lee el archivo con FileReader, se parsea el JSON y se invoca `importCatalog`.
4. WHEN la importación se completa exitosamente, THE Suite_De_Tests SHALL verificar que se muestra el número de items creados.
5. WHEN el archivo seleccionado no es JSON válido, THE Suite_De_Tests SHALL verificar que se muestra el error "Invalid JSON file".
6. WHILE no hay archivo seleccionado, THE Suite_De_Tests SHALL verificar que el botón "Import" está deshabilitado.
7. WHILE se ejecuta la exportación, THE Suite_De_Tests SHALL verificar que el botón "Export Catalog" está deshabilitado y muestra "Exporting…".

### Requisito 15: Tests del Router

**Historia de Usuario:** Como desarrollador, quiero tests para la configuración del router, para verificar que las rutas están definidas correctamente.

#### Criterios de Aceptación

1. THE Suite_De_Tests SHALL verificar que existen las cinco rutas definidas: `/`, `/media/new`, `/media/:id`, `/stats`, `/import-export`.
2. THE Suite_De_Tests SHALL verificar que cada ruta tiene el nombre correcto (`catalog`, `media-create`, `media-detail`, `stats`, `import-export`).
3. THE Suite_De_Tests SHALL verificar que los componentes de las rutas se cargan de forma lazy (son funciones que retornan imports dinámicos).
