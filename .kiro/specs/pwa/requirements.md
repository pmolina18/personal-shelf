# Requisitos — Progressive Web App (PWA)

## Contexto

Personal Shelf es una SPA Vue 3 + Vite servida desde Vercel (frontend) con backend FastAPI en Render. Los usuarios acceden desde navegadores móviles y de escritorio. Actualmente no hay soporte PWA: no hay manifest, service worker, ni meta tags para instalación.

La IDEA-11 pide convertir la app en PWA para que los usuarios puedan "instalar" la app desde el navegador en iOS y Android, con icono en el home screen y sin barra del navegador.

## Fuera de alcance

- Push notifications (se puede añadir en el futuro).
- Modo offline completo con cache de datos de API (solo cache de assets estáticos).
- Publicación en App Store / Google Play (eso es IDEA-12, Capacitor).
- Generación automática de iconos desde un SVG fuente (se proporcionan manualmente).

---

## Requisitos funcionales

### Requisito 1 — Plugin PWA en Vite
- **Descripción:** Instalar y configurar `vite-plugin-pwa` en el proyecto frontend.
- **Criterio de aceptación:** `vite build` genera un `manifest.webmanifest` y un service worker (`sw.js`) en el directorio `dist/`.

### Requisito 2 — Web App Manifest
- **Descripción:** Configurar el manifest con los datos de la app: nombre, short_name, description, theme_color, background_color, display mode, start_url, scope, e iconos en múltiples tamaños.
- **Criterio de aceptación:**
  - `name`: "Personal Shelf"
  - `short_name`: "Shelf"
  - `description`: "Track and share your movies, series, and books"
  - `theme_color`: color primario de la app (`#4a90d9`)
  - `background_color`: `#ffffff`
  - `display`: `standalone`
  - `start_url`: `/`
  - Iconos: 192x192 y 512x512 (PNG), con `purpose: "any maskable"`

### Requisito 3 — Meta tags en index.html
- **Descripción:** Añadir las meta tags necesarias para PWA en `index.html`.
- **Criterio de aceptación:**
  - `<meta name="theme-color" content="#4a90d9">`
  - `<meta name="apple-mobile-web-app-capable" content="yes">`
  - `<meta name="apple-mobile-web-app-status-bar-style" content="default">`
  - `<link rel="apple-touch-icon" href="/icons/icon-192x192.png">`
  - `<meta name="description" content="Track and share your movies, series, and books">`

### Requisito 4 — Service Worker con estrategia de cache
- **Descripción:** Configurar el service worker generado por Workbox (vía vite-plugin-pwa) para cachear assets estáticos (JS, CSS, imágenes, fuentes).
- **Criterio de aceptación:**
  - `registerType: 'prompt'` — el usuario decide cuándo actualizar.
  - Precache de todos los assets del build (JS, CSS, HTML).
  - Runtime cache de Google Fonts con estrategia `CacheFirst`.
  - Runtime cache de imágenes de la API (`/images/*`) con estrategia `CacheFirst` y expiración de 30 días.

### Requisito 5 — Prompt de actualización
- **Descripción:** Cuando hay una nueva versión disponible del service worker, mostrar un toast/banner al usuario con opción de recargar.
- **Criterio de aceptación:**
  - Se muestra un componente `ReloadPrompt.vue` con mensaje "Nueva versión disponible" y botón "Actualizar".
  - Al hacer click en "Actualizar", se activa el nuevo service worker y se recarga la página.
  - El prompt se puede cerrar sin actualizar (se actualizará en la próxima visita).

### Requisito 6 — Iconos PWA
- **Descripción:** Crear iconos de la app en los tamaños requeridos y colocarlos en `public/icons/`.
- **Criterio de aceptación:**
  - `icon-192x192.png` (192×192 px)
  - `icon-512x512.png` (512×512 px)
  - Diseño: emoji 📚 o representación visual del logo de Personal Shelf sobre fondo del color primario.

### Requisito 7 — Documento de instalación para usuarios (PWA_INSTALL.md)
- **Descripción:** Crear un documento con instrucciones paso a paso para que los usuarios sepan cómo instalar la app en su móvil.
- **Criterio de aceptación:**
  - Instrucciones para iOS (Safari → Compartir → Añadir a pantalla de inicio).
  - Instrucciones para Android (Chrome → menú → Instalar app).
  - Instrucciones para escritorio (Chrome → icono de instalación en barra de direcciones).
  - Escrito en español.

---

## Requisitos no funcionales

- El service worker solo se registra en producción (no en dev mode).
- El build no debe aumentar más de 5 segundos respecto al build actual.
- La app debe seguir funcionando correctamente sin service worker (degradación elegante).
- Compatible con iOS Safari 16.4+, Chrome 90+, Firefox 90+, Edge 90+.
