<template>
  <Teleport to="body">
    <div
      v-if="open"
      class="dialog-overlay"
      @click.self="emit('cancel')"
      @keydown.escape="emit('cancel')"
    >
      <div
        ref="dialogRef"
        role="dialog"
        aria-modal="true"
        :aria-label="title"
        class="dialog-box"
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
            class="btn btn-cancel"
            @click="emit('cancel')"
          >
            Cancel
          </button>
          <button
            type="button"
            class="btn btn-confirm"
            @click="emit('confirm')"
          >
            Confirm
          </button>
        </div>
      </div>
    </div>
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
.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog-box {
  background: #fff;
  border-radius: 8px;
  padding: 1.5rem;
  max-width: 420px;
  width: 90%;
  outline: none;
}

.dialog-title {
  margin: 0 0 0.5rem;
  font-size: 1.2rem;
}

.dialog-message {
  margin: 0 0 1.5rem;
  color: #555;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
}

.btn-cancel {
  background: #e0e0e0;
  color: #333;
}

.btn-cancel:hover {
  background: #d0d0d0;
}

.btn-confirm {
  background: #c62828;
  color: #fff;
}

.btn-confirm:hover {
  background: #b71c1c;
}
</style>
