# Diseño — Progressive Web App (PWA)

## 1. Arquitectura

La PWA se implementa enteramente en el frontend. No requiere cambios en el backend. El flujo es:

```
vite build → genera manifest.webmanifest + sw.js (Workbox)
                ↓
index.html ← meta tags PWA + link manifest
                ↓
main.js ← registra service worker (solo producción)
                ↓
ReloadPrompt.vue ← muestra toast cuando hay nueva versión
```

## 2. Dependencias nuevas

| Paquete | Versión | Tipo |
|---------|---------|------|
| `vite-plugin-pwa` | ^0.21 | devDependency |

No se necesita `workbox-*` directamente — `vite-plugin-pwa` lo incluye internamente.

## 3. Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `frontend/package.json` | Añadir `vite-plugin-pwa` |
| `frontend/vite.config.js` | Configurar `VitePWA()` plugin |
| `frontend/index.html` | Meta tags PWA + apple-touch-icon |
| `frontend/src/App.vue` | Incluir `<ReloadPrompt />` |

## 4. Archivos nuevos

| Archivo | Propósito |
|---------|-----------|
| `frontend/src/components/ReloadPrompt.vue` | Toast de actualización |
| `frontend/public/icons/icon-192x192.png` | Icono PWA 192px |
| `frontend/public/icons/icon-512x512.png` | Icono PWA 512px |
| `PWA_INSTALL.md` | Guía de instalación para usuarios |

## 5. Configuración de vite-plugin-pwa

```js
VitePWA({
  registerType: 'prompt',
  includeAssets: ['icons/icon-192x192.png', 'icons/icon-512x512.png'],
  manifest: {
    name: 'Personal Shelf',
    short_name: 'Shelf',
    description: 'Track and share your movies, series, and books',
    theme_color: '#4a90d9',
    background_color: '#ffffff',
    display: 'standalone',
    start_url: '/',
    scope: '/',
    icons: [
      { src: 'icons/icon-192x192.png', sizes: '192x192', type: 'image/png', purpose: 'any maskable' },
      { src: 'icons/icon-512x512.png', sizes: '512x512', type: 'image/png', purpose: 'any maskable' },
    ],
  },
  workbox: {
    globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
    runtimeCaching: [
      {
        urlPattern: /^https:\/\/fonts\.googleapis\.com\/.*/i,
        handler: 'CacheFirst',
        options: {
          cacheName: 'google-fonts-cache',
          expiration: { maxEntries: 10, maxAgeSeconds: 60 * 60 * 24 * 365 },
          cacheableResponse: { statuses: [0, 200] },
        },
      },
      {
        urlPattern: /^https:\/\/fonts\.gstatic\.com\/.*/i,
        handler: 'CacheFirst',
        options: {
          cacheName: 'gstatic-fonts-cache',
          expiration: { maxEntries: 10, maxAgeSeconds: 60 * 60 * 24 * 365 },
          cacheableResponse: { statuses: [0, 200] },
        },
      },
      {
        urlPattern: /\/images\/.*/i,
        handler: 'CacheFirst',
        options: {
          cacheName: 'images-cache',
          expiration: { maxEntries: 200, maxAgeSeconds: 60 * 60 * 24 * 30 },
          cacheableResponse: { statuses: [0, 200] },
        },
      },
    ],
  },
})
```

## 6. ReloadPrompt.vue

Componente que usa la API `virtual:pwa-register/vue` exportada por `vite-plugin-pwa`:

```js
import { useRegisterSW } from 'virtual:pwa-register/vue'

const { needRefresh, updateServiceWorker } = useRegisterSW()
```

- Muestra un toast fijo en la esquina inferior derecha cuando `needRefresh` es `true`.
- Botón "Actualizar" llama a `updateServiceWorker()`.
- Botón "Cerrar" (×) pone `needRefresh.value = false`.
- Estilo consistente con el sistema de diseño existente (CSS custom properties).

## 7. Generación de iconos

Se generan programáticamente con un script Python (mismo patrón que los placeholder PNGs del bugfix de imágenes): canvas de color `#4a90d9` con el emoji 📚 centrado. Alternativamente, se pueden crear como PNGs simples de color sólido con las letras "PS" centradas.

## 8. Vercel — sin cambios necesarios

Vercel sirve archivos estáticos del `dist/` directamente. El `manifest.webmanifest` y `sw.js` se sirven automáticamente. No se necesita configuración adicional en `vercel.json`.

## 9. Testing

No se requieren tests automatizados para la PWA — la validación se hace con:
- Lighthouse PWA audit en Chrome DevTools.
- Verificación manual de instalación en iOS Safari y Android Chrome.
- `vite build` + `vite preview` para probar el service worker localmente.
