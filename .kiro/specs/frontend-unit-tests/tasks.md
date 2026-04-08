# Plan de Implementación: Tests Unitarios del Frontend

## Visión General

Implementar una suite completa de tests unitarios para el frontend Vue 3 de Personal Shelf usando Vitest, @vue/test-utils, jsdom y fast-check. Se crearán 14 archivos de test organizados en 5 directorios, cubriendo la capa API, composables, componentes, vistas y router. Los tests de propiedades validan invariantes universales con fast-check.

## Tareas

- [x] 1. Configurar el entorno de tests
  - Instalar dependencias de desarrollo: `vitest`, `@vue/test-utils`, `jsdom`, `fast-check`
  - Agregar script `"test": "vitest run"` en `frontend/package.json`
  - Crear `frontend/vitest.config.js` con entorno jsdom, globals true, setup file y alias `@` → `src/`
  - Crear `frontend/src/__tests__/setup.js` con `afterEach(() => vi.restoreAllMocks())`
  - Verificar que `npm test` ejecuta sin errores de configuración (puede fallar por 0 tests, eso es esperado)
  - _Requisitos: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 2. Tests de la capa API
  - [x] 2.1 Crear `frontend/src/__tests__/api/media.test.js`
    - Mockear `globalThis.fetch` con `vi.fn()` en `beforeEach`
    - Tests para `request()`: respuesta exitosa parsea JSON, status 204 retorna null, error lanza Error con `detail`
    - Tests para `listMedia`: parámetros no vacíos en query string, parámetros nulos/vacíos omitidos
    - Tests para `createMedia`: POST con body JSON al endpoint correcto
    - Tests para `updateMedia`: PUT con ID y body al endpoint correcto
    - Tests para `deleteMedia`: DELETE al endpoint correcto, retorna null
    - Tests para `updateStatus`, `updateRating`, `updateTags`: método HTTP y sub-endpoint correctos
    - Tests para `exportCatalog`, `importCatalog`: métodos y endpoints correctos
    - _Requisitos: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10_

  - [x] 2.2 Test de propiedad para construcción del query string
    - **Propiedad 1: Construcción correcta del query string en listMedia**
    - Usar `fast-check` con `fc.record()` generando mezclas de valores nulos, vacíos y no vacíos
    - Verificar que la URL contiene exactamente los parámetros con valor no nulo/vacío y omite los demás
    - **Valida: Requisitos 2.4, 2.5**

- [x] 3. Tests del composable useMedia
  - [x] 3.1 Crear `frontend/src/__tests__/composables/useMedia.test.js`
    - Mockear `src/api/media.js` con `vi.mock()` para todas las funciones exportadas
    - Test de instancias independientes: dos invocaciones de `useMedia()` retornan refs distintos
    - Tests para `fetchMedia`: `loading` cambia durante petición, `items`/`total`/`pages` se actualizan, error se captura
    - Tests para `setFilters`: `page` se reinicia a 1, `fetchMedia` se invoca con filtros actualizados
    - Tests para `setPage`: `page` se actualiza, `fetchMedia` se invoca
    - Tests para `hasActiveFilters`: retorna true/false según presencia de filtros
    - Tests para `fetchItem`: `currentItem` se actualiza, `itemLoading` refleja estado de carga
    - Tests para `create`, `update`, `remove`: invocaciones correctas a la API, actualización de estado
    - Tests para `changeStatus`, `changeRating`, `changeTags`: `currentItem` se actualiza, `successMsg` temporal
    - Tests de error: `itemError` contiene mensaje cuando operaciones fallan
    - _Requisitos: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10, 3.11, 3.12, 3.13_

  - [x] 3.2 Test de propiedad para hasActiveFilters
    - **Propiedad 2: hasActiveFilters refleja presencia de filtros**
    - Usar `fast-check` con `fc.record()` generando valores arbitrarios (nulos o no nulos) para `media_type`, `status`, `search`, `tag`
    - Verificar que retorna `true` si y solo si al menos una propiedad tiene valor truthy
    - **Valida: Requisito 3.7**

- [ ] 4. Checkpoint — Verificar tests de API y composable
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Tests de componentes
  - [x] 5.1 Crear `frontend/src/__tests__/components/ConfirmDialog.test.js`
    - Usar `mount` con `attachTo: document.body` para manejar Teleport
    - Tests: no renderiza cuando `open` es false, renderiza título y mensaje cuando open es true
    - Tests: emite `confirm` al clic en Confirm, emite `cancel` al clic en Cancel y al clic en overlay
    - Tests: atributos ARIA correctos (`role="dialog"`, `aria-modal="true"`, `aria-label`)
    - Limpiar con `wrapper.unmount()` en `afterEach`
    - _Requisitos: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

  - [x] 5.2 Crear `frontend/src/__tests__/components/FilterBar.test.js`
    - Usar `mount` para renderizar FilterBar
    - Tests: renderiza los 4 campos de filtro (búsqueda, tipo, estado, tag)
    - Tests: emite `update:filters` con valor correcto al escribir en búsqueda, seleccionar tipo, seleccionar estado
    - Tests: campos vacíos emiten `null` en la propiedad correspondiente
    - _Requisitos: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [x] 5.3 Crear `frontend/src/__tests__/components/MediaCard.test.js`
    - Usar `mount` con stub de `RouterLink`
    - Tests: renderiza título, badges de tipo y estado, enlace a `/media/{id}`
    - Tests: muestra rating "★ N/10" cuando existe, no renderiza rating cuando es null
    - Tests: usa placeholder cuando no hay `image_url`
    - Tests: labels computados mapean valores correctamente (movie→Movie, in_progress→In Progress)
    - _Requisitos: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

  - [x] 5.4 Crear `frontend/src/__tests__/components/MediaForm.test.js`
    - Usar `mount` para renderizar MediaForm
    - Tests: sin `initialData` muestra campos vacíos y botón "Create"
    - Tests: con `initialData` muestra datos populados y botón "Save Changes"
    - Tests: envío sin título muestra "Title is required" y no emite `submit`
    - Tests: envío con título válido emite `submit` con datos formateados
    - Tests: cambio de `initialData` después del montaje actualiza campos
    - Tests: valores opcionales vacíos se emiten como `null`
    - _Requisitos: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

  - [x] 5.5 Crear `frontend/src/__tests__/components/Pagination.test.js`
    - Usar `mount` para renderizar Pagination
    - Tests: no renderiza cuando `pages` ≤ 1
    - Tests: muestra total de items y controles cuando `pages` > 1
    - Tests: botón Prev deshabilitado en primera página, Next deshabilitado en última
    - Tests: emite `update:page` al clic en número de página
    - Tests: `visiblePages` calcula ventana ±2 correctamente
    - _Requisitos: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7_

  - [x] 5.6 Test de propiedad para visiblePages
    - **Propiedad 3: visiblePages calcula ventana correcta**
    - Usar `fast-check` con generador encadenado: `fc.integer({min:2, max:100})` para pages, luego `fc.integer({min:1, max:pages})` para page
    - Verificar que el array contiene exactamente `[max(1, page-2), min(pages, page+2)]`, ordenado, sin duplicados
    - **Valida: Requisitos 8.6, 8.7**

  - [x] 5.7 Crear `frontend/src/__tests__/components/RatingInput.test.js`
    - Usar `mount` para renderizar RatingInput
    - Tests: renderiza 10 botones de estrella cuando no está deshabilitado
    - Tests: muestra mensaje de estado deshabilitado cuando `disabled` es true
    - Tests: emite `update:modelValue` con número correcto al clic en estrella
    - Tests: estrellas hasta `modelValue` tienen clase `active`, muestra texto "N/10"
    - _Requisitos: 9.1, 9.2, 9.3, 9.4_

  - [x] 5.8 Crear `frontend/src/__tests__/components/TagInput.test.js`
    - Usar `mount` para renderizar TagInput
    - Tests: renderiza chips con botón de eliminar para cada tag en `modelValue`
    - Tests: Enter con texto emite `update:modelValue` con array actualizado
    - Tests: tag duplicado no emite evento y limpia campo
    - Tests: al alcanzar `max` muestra mensaje de límite y no permite agregar
    - Tests: clic en eliminar emite array sin el tag eliminado
    - Tests: botón "Add" deshabilitado cuando campo vacío
    - _Requisitos: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6_

- [x] 6. Checkpoint — Verificar tests de componentes
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Tests de vistas
  - [x] 7.1 Crear `frontend/src/__tests__/views/CatalogView.test.js`
    - Usar `shallowMount` con mock de `useMedia` composable
    - Proveer stubs para FilterBar, MediaCard, Pagination y RouterLink
    - Tests: invoca `fetchMedia` al montar
    - Tests: muestra indicador de carga cuando `loading` es true
    - Tests: muestra mensaje de error cuando `error` tiene valor
    - Tests: muestra estado vacío con enlace cuando `items` vacío sin filtros
    - Tests: muestra "No items match your filters" cuando `items` vacío con filtros activos
    - Tests: renderiza MediaCard por cada item y Pagination cuando hay items
    - _Requisitos: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6_

  - [x] 7.2 Crear `frontend/src/__tests__/views/MediaDetailView.test.js`
    - Usar `shallowMount` con mocks de `useMedia`, `useRoute`, `useRouter`
    - Proveer stubs para MediaForm, TagInput, RatingInput, ConfirmDialog y RouterLink
    - Tests: modo creación muestra "Add Media" cuando ruta es `media-create`
    - Tests: modo edición invoca `fetchItem` con ID de la ruta
    - Tests: envío en modo creación invoca `create` y navega al detalle
    - Tests: clic en Delete + confirmar invoca `remove` y navega al catálogo
    - Tests: muestra indicador de carga y mensaje de error según estado
    - _Requisitos: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6_

  - [x] 7.3 Crear `frontend/src/__tests__/views/StatsView.test.js`
    - Usar `shallowMount` con mock de `getStats` de la capa API
    - Tests: invoca `getStats` al montar
    - Tests: muestra secciones by_type, by_status, avg_rating_by_type con datos cargados
    - Tests: `totalItems` se calcula como suma de valores de `by_type`
    - Tests: `formatLabel` convierte "in_progress" a "In Progress"
    - Tests: muestra indicador de carga y mensaje de error según estado
    - _Requisitos: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6_

  - [x] 7.4 Test de propiedad para formatLabel
    - **Propiedad 4: formatLabel transforma claves correctamente**
    - Usar `fast-check` generando cadenas de palabras en minúsculas separadas por guiones bajos
    - Verificar que el resultado reemplaza `_` por espacios y capitaliza la primera letra de cada palabra
    - **Valida: Requisito 13.4**

  - [x] 7.5 Crear `frontend/src/__tests__/views/ImportExportView.test.js`
    - Usar `shallowMount` con mocks de `exportCatalog` e `importCatalog` de la capa API
    - Mockear `FileReader` como clase global, `URL.createObjectURL`, `URL.revokeObjectURL`
    - Tests: clic en Export invoca `exportCatalog` y crea enlace de descarga con blob JSON
    - Tests: error de exportación muestra mensaje de error
    - Tests: seleccionar archivo + Import lee con FileReader, parsea JSON, invoca `importCatalog`
    - Tests: importación exitosa muestra número de items creados
    - Tests: archivo JSON inválido muestra error "Invalid JSON file"
    - Tests: botón Import deshabilitado sin archivo seleccionado
    - Tests: botón Export deshabilitado y muestra "Exporting…" durante exportación
    - _Requisitos: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7_

- [x] 8. Tests del router
  - Crear `frontend/src/__tests__/router/index.test.js`
  - Importar directamente el módulo del router y verificar el array de rutas
  - Tests: existen las 5 rutas (`/`, `/media/new`, `/media/:id`, `/stats`, `/import-export`)
  - Tests: cada ruta tiene el nombre correcto (`catalog`, `media-create`, `media-detail`, `stats`, `import-export`)
  - Tests: componentes de rutas son funciones (lazy loading con import dinámico)
  - _Requisitos: 15.1, 15.2, 15.3_

- [x] 9. Checkpoint final — Validar suite completa
  - Ensure all tests pass, ask the user if questions arise.

## Notas

- Las tareas marcadas con `*` son opcionales y pueden omitirse para un MVP más rápido
- Cada tarea referencia los requisitos específicos que valida
- Los checkpoints permiten validación incremental
- Los tests de propiedades validan invariantes universales con fast-check
- Los tests unitarios validan ejemplos específicos y casos borde
- Todos los archivos de test se ubican bajo `frontend/src/__tests__/` siguiendo la estructura del diseño
