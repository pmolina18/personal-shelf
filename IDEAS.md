# Ideas

Backlog de ideas para Personal Shelf. Cuando quieras que convierta una idea en spec, dime cuál.

Cada idea sigue este formato:

```
## [IDEA-XX] Título corto

- Tipo: feature | bugfix | mejora | infra
- Prioridad: alta | media | baja
- Descripción: Qué quieres lograr, en 2-3 frases.
- Contexto: (opcional) Archivos relevantes, APIs externas, inspiración, etc.
- Notas: (opcional) Restricciones, dudas, o cosas que ya tienes claras.
```

---

<!-- Pega tus ideas debajo de esta línea -->

## [IDEA-1] Allowed Users ✅ COMPLETADA → `.kiro/specs/allowed-users/`

- Tipo: feature
- Prioridad: alta
- Descripción: antes de publicarla para todo el mundo, me gustaría ir poco a poco y tener como una especie de Lista de usuarios permitidos.
- Contexto: auth system
- Notas: He pensado que lo mejor sería tener un fichero llamado allowed_users en el que guardar una lista de usuarios permitidos, y antes de permitir crear un usuario, hay que validar si existe en esta lista de usuarios permitidos. También me gustaría que si un usuario no está en esta lista y quiere añadirse, cree una issue en Github (o un PR, lo que prefieras) para que yo cuando lo vea y lo mergee se añada para el futuro.
- Estado: Implementada el 2026-04-09. Spec completa + código desplegable.

---

## [IDEA-2] Buzón de sugerencias

- Tipo: feature
- Prioridad: media
- Descripción: me gustaría permitir que los primeros usuarios, pudiesen tener un sitio donde añadir sugerencias o peticiones de features nuevas
- Contexto: esto serían nuevos endpoints y nuevas vistas
- Notas: (opcional) Esas peticiones nuevas que escribiesen los usuarios de nuevas features o bugs que reporten, automáticamente tendrían que crear issues en Github para que de nuevo, yo pudiese priorizartelos y los fueses resolviendo uno a uno

---

## [IDEA-3] Recomendaciones entre amigos ✅ COMPLETADA → `.kiro/specs/friend-recommendations/`

- Tipo: feature
- Prioridad: alta
- Descripción: me gustaría que existiese la opción de recomendarle a tus amigos alguna película o item que tu hayas visto o estés viendo
- Contexto: en la ventana de catalogo, dentro de cada item tuvieses un botón para recomendar a amigos
- Notas: (opcional) Estaría bien que tuvieses un sistema de mensajes desde la pantalla de catálogo, con una "bolita" en la que aparezca el número de recomendaciones que tienes etc
- Estado: Implementada el 2026-04-10. Botón de recomendar en detalle de media, vista de recomendaciones con badge de contador en el sidebar, aceptar/rechazar recomendaciones.

---


## [IDEA-4] Ventana Explore — Catálogo global con filtros y recomendaciones ✅ COMPLETADA → `.kiro/specs/explore-catalog/`

- Tipo: feature
- Prioridad: alta
- Descripción: Nueva vista "Explore" que muestre un catálogo global de items multimedia que existen en la plataforma (de cualquier usuario), agrupados por título+tipo para evitar duplicados. Permite descubrir contenido nuevo, filtrar por tipo de media, ordenar alfabéticamente (A→Z / Z→A) y ordenar por "recomendaciones de amigos" (cuántos amigos lo tienen o te lo han recomendado).
- Contexto: Se apoya en la infraestructura existente de `MediaItem`, `recommendations`, `friendships`. El filtro por tipo ya existe en `MediaFilters`. La ordenación por recomendaciones requiere JOINs con `recommendations` + `friendships` y un COUNT como criterio de ordenación. Cada item del explore podría mostrar: "N amigos lo tienen", "N amigos te lo recomendaron", con usernames/avatares.
- Notas: Dos opciones para poblar el catálogo: (1) agregar items de todos los usuarios (más orgánico, crece solo), (2) seed inicial con datos de TMDB/Open Library. La opción 1 es más sencilla y coherente con la arquitectura actual. Se puede complementar con un script de seed para contenido popular. No requiere modelo nuevo si se reutiliza `MediaItem` con una query global. Considerar también un endpoint nuevo tipo `GET /api/explore` con parámetros de filtro, orden y paginación.
- Estado: Implementada el 2026-04-10. Vista Explore con deduplicación, señales sociales, filtros, ordenación, botón "Add to shelf", exclusión de items propios, y seed script con 60 items populares.

---


## [IDEA-5] Plataforma / formato de consumo por item

- Tipo: feature
- Prioridad: media
- Descripción: Al crear o editar un item, poder indicar dónde o cómo lo has consumido. Para películas y series: Netflix, HBO, Disney+, Amazon Prime, cine, etc. Para libros: libro físico, Kindle, audiolibro. Esto añade contexto personal a cada item y permite filtrar/agrupar por plataforma en el futuro.
- Contexto: Requiere un nuevo campo `platform` (string, nullable) en `MediaItem` + migración Alembic. En el frontend, un select/dropdown en `MediaForm.vue` cuyas opciones cambien dinámicamente según el `media_type` seleccionado. También actualizar `MediaCreate`, `MediaUpdate`, `MediaResponse` en schemas.
- Notas: Las opciones de plataforma podrían ser un enum en backend o simplemente un campo de texto libre con sugerencias predefinidas en frontend (más flexible para añadir plataformas nuevas sin migración). Considerar también mostrar el icono/logo de la plataforma en `MediaCard` y `MediaDetailView`.

---

## [IDEA-6] Eliminar funcionalidad de Import/Export

- Tipo: mejora
- Prioridad: media
- Descripción: Quitar completamente la funcionalidad de import/export del catálogo. No tiene sentido en el contexto actual de la app como red social. Incluye eliminar: backend (ExportService, endpoints en stats_export router), frontend (ImportExportView, ruta, enlace en sidebar), schemas (ExportData, ImportResult), y tests asociados.
- Contexto: Archivos afectados: `backend/services/export_service.py`, `backend/routers/stats_export.py` (endpoints de export/import), `frontend/src/views/ImportExportView.vue`, `frontend/src/api/media.js` (funciones exportCatalog/importCatalog), router, App.vue (sidebar link). También tests en `tests/` y `frontend/src/__tests__/`.
- Notas: Es una limpieza — eliminar código muerto simplifica el mantenimiento. Hacer una migración Alembic no es necesario ya que no hay cambios en el modelo de datos.

---

## [IDEA-7] Tooltips en iconos del sidebar colapsado

- Tipo: mejora
- Prioridad: media
- Descripción: Cuando el sidebar está colapsado (solo iconos visibles), al pasar el ratón sobre cada icono debería aparecer un tooltip con el nombre de la sección (ej: "Catálogo", "Amigos", "Recomendaciones", etc.). Mejora la usabilidad cuando el sidebar está en modo compacto.
- Contexto: Archivo principal: `frontend/src/App.vue` (sidebar). Se puede implementar con `title` attribute nativo (simple) o con un tooltip CSS custom (más bonito, consistente con el diseño). Solo aplica cuando `collapsed === true` — con el sidebar expandido el texto ya es visible.
- Notas: La opción CSS custom (pseudo-elemento `::after` con `content: attr(data-tooltip)` + `position: absolute`) da mejor control visual que el `title` nativo, que depende del navegador y tiene delay.

---

## [IDEA-8] Fechas de cambio de estado por item (status timestamps)

- Tipo: feature
- Prioridad: media
- Descripción: Registrar automáticamente la fecha en la que un item cambia a cada estado: cuándo se puso en "pending", cuándo pasó a "in_progress" y cuándo se marcó como "completed". Así queda reflejado el historial temporal de consumo de cada item.
- Contexto: Requiere tres nuevos campos nullable en `MediaItem`: `pending_at`, `in_progress_at`, `completed_at` (DateTime, nullable) + migración Alembic. Cada vez que se actualice el `status` de un item (vía `MediaService.update_media` o el endpoint PATCH de status), se rellena el campo correspondiente con `datetime.utcnow()`. También actualizar `MediaResponse` en schemas para exponer las fechas, y mostrarlas en `MediaDetailView.vue` (ej: "En pending desde 12 mar 2026", "Completado el 5 abr 2026").
- Notas: Los items existentes tendrán los tres campos a `null` — solo se rellenan a partir de ahora. Si un item vuelve a un estado anterior (ej: de completed a in_progress), se sobreescribe la fecha de ese estado con la nueva. Considerar mostrar una mini-timeline visual en el detalle del item con los tres hitos.

## [IDEA-9] Bordes de color por tipo de media en las tarjetas

- Tipo: mejora
- Prioridad: alta
- Descripción: Que las tarjetas (MediaCard) tengan un borde de color distinto según el tipo de item (película, serie, libro, etc.). Colores pastel y poco llamativos para que no canten demasiado pero se distinga de un vistazo qué tipo de contenido es cada tarjeta.
- Contexto: Archivo principal: `frontend/src/components/MediaCard.vue`. Los tipos de media están definidos en `backend/schemas/media.py` (MediaType enum). Ya existen CSS custom properties en `App.vue` para el sistema de diseño. Se puede resolver solo con CSS (borde izquierdo o borde completo con color pastel según `media_type`).
- Notas: Con que el borde sea distinto probablemente sea suficiente — no hace falta cambiar el fondo entero de la tarjeta. Colores sugeridos: tonos pastel suaves (azul para películas, verde para series, ámbar para libros, etc.). Definir las variables de color en App.vue y aplicarlas condicionalmente en MediaCard con una clase dinámica tipo `:class="'type-' + item.media_type"`.
