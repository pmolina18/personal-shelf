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
- Use `role="status"` for loading indicators, `role="alert"` for errors.
- Dialogs: `role="dialog"`, `aria-modal="true"`, auto-focus on open, close on Escape.
- Use `aria-pressed` for toggle buttons (e.g., status buttons).
- Use `aria-current="page"` for active pagination items.

## State Management
- Use composables for shared state — no Vuex/Pinia unless complexity demands it.
- Keep component-local state local; only lift to composables when shared.
- Composables return fresh `ref()` per invocation — no module-level shared state.

---

## CSS Conventions

### Scoped Styles Only
- Always use `<style scoped>`. No global styles except in `App.vue` if needed.
- No CSS frameworks (no Tailwind, no Bootstrap). Plain CSS with scoped styles.

### Naming Convention
- Use flat BEM-inspired class names: `.component-name`, `.component-name__element`, `.component-name--modifier`.
- Actual project pattern uses simplified BEM: `.media-card`, `.card-body`, `.card-title`, `.badge-status--completed`.
- Prefix classes with the component context to avoid collisions even within scoped styles.

### Design Tokens (Project Palette)
Use these consistent values across all components:

```css
/* Primary action */
--color-primary: #4a90d9;
--color-primary-hover: #3a7bc8;

/* Status badges */
--color-status-pending-bg: #eeeeee;
--color-status-pending-text: #616161;
--color-status-in-progress-bg: #e3f2fd;
--color-status-in-progress-text: #1565c0;
--color-status-completed-bg: #e8f5e9;
--color-status-completed-text: #2e7d32;

/* Type badge */
--color-type-bg: #e8eaf6;
--color-type-text: #3949ab;

/* Feedback */
--color-error: #c62828;
--color-error-bg: #ffebee;
--color-success: #2e7d32;
--color-success-bg: #e8f5e9;
--color-rating: #f9a825;

/* Neutral */
--color-border: #e0e0e0;
--color-input-border: #ccc;
--color-text-muted: #666;
--color-text-secondary: #555;
--color-bg-light: #f5f5f5;
```

### Spacing & Sizing
- Use `rem` units for spacing and font sizes (not `px` except for borders).
- Standard border-radius: `6px` for inputs/buttons, `8px` for cards/containers, `4px` for small badges, `12px` for chips/pills.
- Standard padding: `0.5rem 0.75rem` for inputs, `0.5rem 1rem` for buttons, `0.75rem` for card body, `1rem` for view containers.
- Max-width for views: `1200px` (catalog grid), `800px` (stats, import/export), `700px` (detail/form).

### Layout Patterns
- Flexbox for linear layouts (forms, filter bars, button groups, pagination).
- CSS Grid for card grids: `grid-template-columns: repeat(auto-fill, minmax(200px, 1fr))`.
- `gap` property for spacing between flex/grid children (not margins).
- `flex-wrap: wrap` on containers that may overflow on small screens.

### Interactive States
- Hover: subtle background change or `box-shadow` for cards.
- Focus: `outline: 2px solid #4a90d9; outline-offset: 1px` (or `2px` for buttons).
- Disabled: `opacity: 0.4–0.5; cursor: not-allowed`.
- Active/selected: primary color background with white text.
- Transitions: `0.15s–0.2s` for color/shadow changes.

### Typography
- Font sizes: `0.75rem` (badges), `0.85rem` (small text, pagination), `0.9rem` (inputs, labels), `0.95rem` (form inputs), `1rem` (card titles, body), `1.1rem` (section headings), `1.2rem` (dialog titles).
- Font weight: `500` for medium emphasis, `600` for labels/buttons/headings.
- Text overflow: `overflow: hidden; text-overflow: ellipsis; white-space: nowrap` for single-line truncation.

### Responsive
- No media queries yet — rely on `auto-fill`/`auto-fit` grid and `flex-wrap` for natural responsiveness.
- `flex: 1 1 180px` pattern for filter inputs to wrap naturally.

### Overlay/Modal Pattern
- Fixed overlay: `position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 1000`.
- Centered dialog: `max-width: 420px; width: 90%` inside flex-centered overlay.
- Use `<Teleport to="body">` for modals.

### Utility Classes
- `.visually-hidden` for screen-reader-only labels (defined in FilterBar, reuse pattern).

### Vue-Specific CSS Patterns
- Dynamic classes with array syntax: `:class="['badge', 'badge-status', \`badge-status--${item.status}\`]"`.
- Conditional classes with object syntax: `:class="{ active: isActive }"`.
- `v-if`/`v-else-if`/`v-else` chains for loading → error → empty → content states.
