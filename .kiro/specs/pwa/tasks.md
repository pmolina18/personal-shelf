# Tareas — Progressive Web App (PWA)

## Estado: completado ✅

---

## Tarea 1 — Instalar vite-plugin-pwa
- [x] 1.1 Ejecutar `npm install -D vite-plugin-pwa` en `frontend/`
- [x] 1.2 Verificar que aparece en `devDependencies` de `package.json`

**Requisitos:** R1

---

## Tarea 2 — Configurar VitePWA en vite.config.js
- [x] 2.1 Importar `VitePWA` de `vite-plugin-pwa`
- [x] 2.2 Añadir `VitePWA({...})` al array de plugins con la configuración del design.md (manifest, workbox, registerType)

**Requisitos:** R1, R2, R4

---

## Tarea 3 — Meta tags en index.html
- [x] 3.1 Añadir `<meta name="theme-color">`, `<meta name="description">`, meta tags de Apple, y `<link rel="apple-touch-icon">`

**Requisitos:** R3

---

## Tarea 4 — Crear iconos PWA
- [x] 4.1 Generar `frontend/public/icons/icon-192x192.png` (192×192)
- [x] 4.2 Generar `frontend/public/icons/icon-512x512.png` (512×512)

**Requisitos:** R6

---

## Tarea 5 — Crear ReloadPrompt.vue
- [x] 5.1 Crear `frontend/src/components/ReloadPrompt.vue` con `useRegisterSW` de `virtual:pwa-register/vue`
- [x] 5.2 Incluir `<ReloadPrompt />` en `App.vue`

**Requisitos:** R5

---

## Checkpoint 1
- [x] Ejecutar `npm run build` en `frontend/` y verificar que `dist/` contiene `manifest.webmanifest` y `sw.js`
- [x] Build exitoso: PWA v1.2.0, mode generateSW, precache 39 entries (282.51 KiB)

---

## Tarea 6 — Crear PWA_INSTALL.md
- [x] 6.1 Escribir guía de instalación en español con instrucciones para iOS, Android y escritorio

**Requisitos:** R7

---

## Tarea 7 — Verificación final
- [x] 7.1 Build limpio sin errores
- [x] 7.2 Manifest generado en dist/manifest.webmanifest
- [x] 7.3 Service worker generado en dist/sw.js
