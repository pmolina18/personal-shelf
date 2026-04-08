---
inclusion: fileMatch
fileMatchPattern: "frontend/**/*.{vue,js,ts}"
---

# Vue Frontend Standards — Media Tracker

## Composition API
- Always use `<script setup>` syntax — no Options API.
- Reactive state with `ref()` and `reactive()`.
- Computed properties with `computed()`.
- Lifecycle hooks: `onMounted()`, `onUnmounted()`, etc.

## Component Naming
- Components: PascalCase (e.g., `MediaCard.vue`, `FilterBar.vue`).
- Composables: camelCase with `use` prefix (e.g., `useMedia.js`).
- Views: PascalCase with `View` suffix (e.g., `CatalogView.vue`).

## File Structure (per .vue file)
```
<template> → <script setup> → <style scoped>
```

## API Client
- All HTTP calls go through `frontend/src/api/media.js`.
- Use async/await with proper error handling (try/catch).
- Never call fetch/axios directly from components — always through the API module.

## Props & Emits
- Define props with `defineProps()` and types.
- Define emits with `defineEmits()`.
- Use TypeScript-style prop validation when possible.

## Accessibility
- All interactive elements must have proper ARIA labels.
- Use semantic HTML (`<main>`, `<nav>`, `<section>`, `<article>`).
- Ensure keyboard navigation works for all interactive components.
- Images must have `alt` attributes.

## State Management
- Use composables for shared state — no Vuex/Pinia unless complexity demands it.
- Keep component-local state local; only lift to composables when shared.
