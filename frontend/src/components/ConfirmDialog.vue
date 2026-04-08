<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="open"
        class="overlay"
        @click.self="emit('cancel')"
        @keydown.escape="emit('cancel')"
      >
        <div
          ref="dialogRef"
          role="dialog"
          aria-modal="true"
          :aria-label="title"
          class="dialog"
          tabindex="-1"
        >
          <h2 class="dialog-title">
            {{ title }}
          </h2>
          <p class="dialog-message">
            {{ message }}
          </p>
          <div class="dialog-actions">
            <button
              type="button"
              class="btn btn--ghost"
              @click="emit('cancel')"
            >
              Cancel
            </button>
            <button
              type="button"
              class="btn btn--danger"
              @click="emit('confirm')"
            >
              Confirm
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'

const props = defineProps({
  open: { type: Boolean, required: true },
  title: { type: String, required: true },
  message: { type: String, required: true },
})

const emit = defineEmits(['confirm', 'cancel'])
const dialogRef = ref(null)

watch(() => props.open, async (isOpen) => {
  if (isOpen) {
    await nextTick()
    dialogRef.value?.focus()
  }
})
</script>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  background: rgba(26, 46, 34, 0.4);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.dialog {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  padding: 1.75rem;
  max-width: 400px;
  width: 100%;
  outline: none;
  box-shadow: var(--shadow-lg);
}

.dialog-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--color-text);
  margin-bottom: 0.4rem;
}

.dialog-message {
  color: var(--color-text-secondary);
  font-size: 0.87rem;
  line-height: 1.55;
  margin-bottom: 1.5rem;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.6rem;
}

.btn {
  padding: 0.5rem 1.1rem;
  border: none;
  border-radius: var(--radius-sm);
  font-weight: 600;
  font-size: 0.87rem;
  cursor: pointer;
  transition: background var(--transition-fast);
}

.btn--ghost {
  background: var(--color-bg);
  color: var(--color-text-secondary);
}

.btn--ghost:hover {
  background: var(--color-border-light);
}

.btn--danger {
  background: var(--color-error);
  color: var(--color-text-inverse);
}

.btn--danger:hover {
  background: #c12a1f;
}

/* Transition */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 200ms ease;
}

.modal-enter-active .dialog,
.modal-leave-active .dialog {
  transition: transform 200ms ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .dialog {
  transform: scale(0.96) translateY(8px);
}

.modal-leave-to .dialog {
  transform: scale(0.96) translateY(8px);
}
</style>
