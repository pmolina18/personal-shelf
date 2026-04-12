<template>
  <Transition name="slide-up">
    <div
      v-if="needRefresh"
      class="reload-prompt"
      role="alert"
      aria-live="assertive"
    >
      <span class="reload-prompt__text">Nueva versión disponible</span>
      <div class="reload-prompt__actions">
        <button
          type="button"
          class="reload-prompt__btn reload-prompt__btn--update"
          @click="updateServiceWorker()"
        >
          Actualizar
        </button>
        <button
          type="button"
          class="reload-prompt__btn reload-prompt__btn--close"
          aria-label="Cerrar"
          @click="close"
        >
          ×
        </button>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { useRegisterSW } from 'virtual:pwa-register/vue'

const { needRefresh, updateServiceWorker } = useRegisterSW()

function close() {
  needRefresh.value = false
}
</script>

<style scoped>
.reload-prompt {
  position: fixed;
  bottom: 1.5rem;
  right: 1.5rem;
  z-index: 2000;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  background: var(--color-surface, #fff);
  border: 1px solid var(--color-border, #e0e0e0);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  font-size: 0.87rem;
}

.reload-prompt__text {
  color: var(--color-text, #333);
  font-weight: 500;
}

.reload-prompt__actions {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.reload-prompt__btn {
  border: none;
  border-radius: 6px;
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
}

.reload-prompt__btn--update {
  padding: 0.35rem 0.85rem;
  background: var(--color-primary, #4a90d9);
  color: var(--color-text-inverse, #fff);
}

.reload-prompt__btn--update:hover {
  background: var(--color-primary-hover, #3a7bc8);
}

.reload-prompt__btn--update:focus-visible {
  outline: 2px solid var(--color-primary, #4a90d9);
  outline-offset: 2px;
}

.reload-prompt__btn--close {
  padding: 0.2rem 0.5rem;
  background: transparent;
  color: var(--color-text-muted, #666);
  font-size: 1.1rem;
  line-height: 1;
}

.reload-prompt__btn--close:hover {
  background: var(--color-bg-light, #f5f5f5);
}

.reload-prompt__btn--close:focus-visible {
  outline: 2px solid var(--color-primary, #4a90d9);
  outline-offset: 1px;
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  opacity: 0;
  transform: translateY(1rem);
}
</style>
