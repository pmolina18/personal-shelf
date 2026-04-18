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

## [IDEA-2] Buzón de sugerencias ✅ COMPLETADA → `.kiro/specs/suggestion-box/`

- Tipo: feature
- Prioridad: media
- Estado: Implementada el 2026-04-11. Modelo Suggestion, servicio con integración GitHub Issues, 3 endpoints REST, vista con pestañas (todas/mías), formulario inline, badges de tipo, enlace a GitHub issue, paginación, sidebar con icono lightbulb.
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

## [IDEA-6] Eliminar funcionalidad de Import/Export ✅ COMPLETADA

- Tipo: mejora
- Prioridad: media
- Estado: Implementada el 2026-04-10. Eliminados: ExportService, router export_import, ImportExportView, schemas ExportData/ImportResult, funciones API frontend, enlace sidebar, herramientas MCP export/import, y todos los tests asociados.
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

## [IDEA-9] Bordes de color por tipo de media en las tarjetas ✅ COMPLETADA

- Tipo: mejora
- Prioridad: alta
- Estado: Implementada el 2026-04-10. Borde izquierdo pastel por tipo (azul películas, verde series, ámbar libros) en MediaCard + CSS custom properties en App.vue.
- Descripción: Que las tarjetas (MediaCard) tengan un borde de color distinto según el tipo de item (película, serie, libro, etc.). Colores pastel y poco llamativos para que no canten demasiado pero se distinga de un vistazo qué tipo de contenido es cada tarjeta.
- Contexto: Archivo principal: `frontend/src/components/MediaCard.vue`. Los tipos de media están definidos en `backend/schemas/media.py` (MediaType enum). Ya existen CSS custom properties en `App.vue` para el sistema de diseño. Se puede resolver solo con CSS (borde izquierdo o borde completo con color pastel según `media_type`).
- Notas: Con que el borde sea distinto probablemente sea suficiente — no hace falta cambiar el fondo entero de la tarjeta. Colores sugeridos: tonos pastel suaves (azul para películas, verde para series, ámbar para libros, etc.). Definir las variables de color en App.vue y aplicarlas condicionalmente en MediaCard con una clase dinámica tipo `:class="'type-' + item.media_type"`.

---

## [IDEA-10] Login con Google (SSO)

- Tipo: feature
- Prioridad: media
- Descripción: Añadir "Sign in with Google" como método alternativo de autenticación, manteniendo el login con email/password actual. El usuario elige cómo entrar; ambos métodos generan el mismo JWT.
- Contexto: El sistema actual usa JWT con bcrypt (auth_service.py). El flujo sería: frontend obtiene ID token de Google → backend lo verifica con `google-auth` → find-or-create usuario → genera JWT. Requiere `GOOGLE_CLIENT_ID` de Google Cloud Console (gratis). El `password_hash` del modelo User pasaría a ser nullable para usuarios que solo usen Google. La validación de `AllowedUsersService` se aplica igual (el email de Google debe estar en `allowed_users`).
- Notas: Dependencia externa: cuenta en Google Cloud Console con OAuth consent screen configurado. La librería `google-auth` (PyPI) verifica ID tokens sin necesidad de flujo OAuth completo del lado del servidor. En frontend, Google Identity Services se carga con un `<script>` tag y devuelve el credential via callback. Considerar si en el futuro se quieren más proveedores (GitHub, Apple) — si sí, diseñar el modelo con una tabla `oauth_accounts` desde el inicio en vez de meter `google_id` directo en `users`.

---

## [IDEA-11] Progressive Web App (PWA) ✅ COMPLETADA → `.kiro/specs/pwa/`

- Tipo: feature
- Prioridad: alta
- Estado: Implementada el 2026-04-12. vite-plugin-pwa configurado con manifest, service worker (Workbox), runtime caching de fonts e imágenes, ReloadPrompt.vue para actualizaciones, iconos PWA, meta tags, y PWA_INSTALL.md con guía de instalación.
- Descripción: Convertir la SPA Vue actual en una PWA para que los usuarios puedan "instalar" la app desde el navegador en iOS y Android, con icono en el home screen y sin barra del navegador. Es el paso más rápido para ofrecer experiencia móvil sin necesidad de publicar en stores.
- Contexto: Requiere `vite-plugin-pwa` (plugin de Vite), un `manifest.json` (nombre, iconos, colores, start_url), un Service Worker para cache/offline básico, y meta tags en `index.html` (`<meta name="theme-color">`, `<link rel="manifest">`, `<meta name="apple-mobile-web-app-capable">`). El plugin genera el SW automáticamente. Los iconos se necesitan en varios tamaños (192x192, 512x512 mínimo).
- Notas: No requiere cuenta de desarrollador de Apple ni Google. Funciona en iOS 16.4+ con push notifications. Limitación: no aparece en App Store ni Google Play (aunque PWABuilder puede generar paquetes para stores). Es el paso previo natural antes de Capacitor. Incluir un documento tipo `PWA_INSTALL.md` con instrucciones paso a paso para que los usuarios sepan cómo instalar la app en su móvil (iOS: Safari → Compartir → Añadir a pantalla de inicio; Android: Chrome → menú → Instalar app), con capturas o descripciones claras del proceso.

---

## [IDEA-12] Publicar en App Store y Google Play con Capacitor

- Tipo: feature
- Prioridad: baja
- Descripción: Envolver la app Vue en un WebView nativo usando Capacitor (del equipo de Ionic) para publicarla en App Store y Google Play. Reutiliza el 95%+ del código frontend actual sin reescritura.
- Contexto: Requiere `@capacitor/core` + `@capacitor/cli`, luego `npx cap add ios` + `npx cap add android`. El flujo es: `vite build` → `npx cap sync` → abrir Xcode (iOS) / Android Studio (Android) → compilar y publicar. Necesita cuenta de Apple Developer ($99/año) y Google Play Console ($25 una vez). Xcode ya disponible en el Mac actual.
- Notas: El rendimiento es web-en-WebView, más que suficiente para una app de contenido (listas, cards, formularios). Da acceso a APIs nativas (push notifications, haptics, cámara) si se necesitan en el futuro. Tiene sentido hacerlo después de validar la experiencia móvil con la PWA (IDEA-11). Considerar si merece la pena el coste de las cuentas de desarrollador según el número de usuarios.

---

## [IDEA-13] Login con username o email ✅ COMPLETADA → `.kiro/specs/login-username-email/`

- Tipo: mejora
- Prioridad: media
- Estado: Implementada el 2026-04-12. Campo `identifier` en login acepta email o username, detección por `@`, tests actualizados + test nuevo para login por username.
- Descripción: Permitir que el usuario pueda iniciar sesión tanto con su nombre de usuario como con su email. Actualmente el login solo acepta email; con este cambio, el campo de login aceptaría cualquiera de los dos y el backend resolvería si es un email (contiene `@`) o un username para buscar al usuario correspondiente.
- Contexto: Archivos afectados: `backend/services/auth_service.py` (lógica de autenticación), `backend/routers/auth.py` (endpoint de login), `backend/schemas/auth.py` (schema de login request). En frontend: `frontend/src/views/LoginView.vue` (label y placeholder del campo). El modelo `User` ya tiene campos `username` y `email`, ambos únicos.
- Notas: La detección puede ser simple: si el valor contiene `@` se busca por email, si no se busca por username. Considerar también actualizar el placeholder del input en el frontend a algo como "Email o nombre de usuario".

---

## [IDEA-14] Estado de sugerencias (feedback al usuario)

- Tipo: feature
- Prioridad: media
- Descripción: Añadir un campo `status` al modelo de sugerencias (pending → in_progress → implemented → dismissed) con un badge visual en cada tarjeta de sugerencia. Permite que los usuarios vean si su idea fue implementada, está en progreso o fue descartada. Un endpoint PATCH protegido (solo admin) permite cambiar el estado.
- Contexto: Archivos afectados: `backend/models/suggestion.py` (nuevo campo status), `backend/schemas/suggestion.py` (nuevo campo en response + schema de update), `backend/routers/suggestions.py` (endpoint PATCH), `backend/services/suggestion_service.py` (método update_status), `frontend/src/views/SuggestionsView.vue` (badge de estado en la card), migración Alembic. El patrón de badges por estado ya existe en MediaCard (pending/in_progress/completed) y se puede reutilizar el mismo CSS.
- Notas: Reutilizar el patrón de colores de status que ya existe en las CSS custom properties (--color-status-pending-bg, etc.). Considerar también ocultar el link a GitHub issue mientras el repo sea privado (ya hecho). En el futuro, cuando el repo sea público, se puede re-añadir el link condicionalmente.

---

## [IDEA-15] Página de perfil + cambio de usuario y contraseña

- Tipo: feature
- Prioridad: media
- Origen: Sugerencia de usuario (GitHub Issue #3)
- Descripción: Nueva página de perfil que se abra al hacer click en el nombre de usuario en la barra lateral. Muestra datos del usuario y posiblemente integra las estadísticas actuales. Además, permite cambiar el nombre de usuario y la contraseña.
- Contexto: Archivos afectados: nuevo `ProfileView.vue`, `backend/routers/auth.py` (endpoints PATCH para username/password), `backend/services/auth_service.py` (métodos update_username, update_password), `backend/schemas/auth.py` (schemas de update), `frontend/src/router/index.js` (nueva ruta /profile), `App.vue` (link en sidebar al perfil). El modelo `User` ya tiene `username` y `email` con constraints UNIQUE. Las estadísticas actuales están en `StatsView.vue` y `StatsService` — se podrían reutilizar o mover al perfil.
- Notas: Para el cambio de contraseña, pedir la contraseña actual como verificación antes de permitir el cambio. Para el cambio de username, validar unicidad antes de confirmar. Considerar si las estadísticas se mueven al perfil o se mantienen como vista separada con un link desde el perfil.

---

## [IDEA-16] Integración Spotify — Podcasts como nuevo tipo de media

- Tipo: feature
- Prioridad: alta
- Descripción: Añadir `podcast` como nuevo `media_type` con integración de la Spotify Web API para autofill de metadatos (nombre, creador/host, imagen, descripción). El usuario busca podcasts manualmente y los añade a su estantería como cualquier otro tipo de media. Todo el sistema existente (CRUD, recomendaciones, explore, tags, stats) funciona automáticamente con el nuevo tipo.
- Contexto: Spotify Web API Search (`/v1/search?type=show`) devuelve nombre, publisher, descripción, imagen (URL directa) y total de episodios. Usa Client Credentials flow (solo `SPOTIFY_CLIENT_ID` + `SPOTIFY_CLIENT_SECRET`, sin OAuth de usuario). Archivos afectados: `backend/schemas/media.py` (MediaType enum), `backend/services/metadata_service.py` (nuevo `_search_spotify`), `backend/services/image_service.py` (Spotify images ya son URLs externas), `backend/config.py` (nuevas env vars), `frontend/src/components/MediaCard.vue` (icono podcast), `frontend/src/components/FilterBar.vue` (opción podcast en filtro de tipo).
- Notas: Enfoque A (manual, sin OAuth de usuario) como primera fase. Enfoque B (OAuth + sincronización automática de podcasts seguidos) queda como evolución futura. El Client Credentials flow de Spotify requiere registrar la app en [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) (gratis, inmediato). El token de acceso dura 1 hora y se renueva automáticamente. Considerar también buscar episodios individuales además de shows completos.
