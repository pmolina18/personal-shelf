<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="show"
        class="recommend-overlay"
        @click.self="emit('close')"
        @keydown.escape="emit('close')"
      >
        <div
          ref="dialogRef"
          role="dialog"
          aria-modal="true"
          :aria-label="`Recomendar ${mediaTitle}`"
          class="recommend-dialog"
          tabindex="-1"
        >
          <div class="recommend-dialog__header">
            <h2 class="recommend-dialog__title">
              Recomendar
            </h2>
            <p class="recommend-dialog__subtitle">
              {{ mediaTitle }}
            </p>
            <button
              type="button"
              class="recommend-dialog__close"
              aria-label="Cerrar"
              @click="emit('close')"
            >
              <svg
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              ><line
                x1="18"
                y1="6"
                x2="6"
                y2="18"
              /><line
                x1="6"
                y1="6"
                x2="18"
                y2="18"
              /></svg>
            </button>
          </div>

          <!-- Cargando amigos -->
          <div
            v-if="friendsLoading"
            class="recommend-dialog__loading"
            role="status"
          >
            <div class="recommend-loader" />
            Cargando amigos…
          </div>

          <!-- Error cargando amigos -->
          <div
            v-else-if="friendsError"
            class="recommend-dialog__error"
            role="alert"
          >
            {{ friendsError }}
          </div>

          <!-- Sin amigos -->
          <div
            v-else-if="friends.length === 0"
            class="recommend-dialog__empty"
          >
            No tienes amigos aún. Agrega amigos para poder enviar recomendaciones.
          </div>

          <!-- Formulario -->
          <template v-else>
            <fieldset class="recommend-dialog__friends">
              <legend class="visually-hidden">
                Seleccionar amigos
              </legend>
              <div
                v-for="f in friends"
                :key="f.id"
                class="recommend-friend"
              >
                <label class="recommend-friend__label">
                  <input
                    v-model="selectedIds"
                    type="checkbox"
                    :value="f.id"
                    class="recommend-friend__checkbox"
                  >
                  <span class="recommend-friend__name">{{ f.username }}</span>
                </label>
              </div>
            </fieldset>

            <div class="recommend-dialog__message">
              <label
                for="recommend-message"
                class="recommend-dialog__label"
              >
                Mensaje (opcional)
              </label>
              <textarea
                id="recommend-message"
                v-model="message"
                class="recommend-dialog__textarea"
                maxlength="500"
                rows="3"
                placeholder="¡Te va a encantar!"
              />
              <span class="recommend-dialog__counter">{{ message.length }}/500</span>
            </div>

            <!-- Error de envío -->
            <div
              v-if="sendError"
              class="recommend-dialog__error"
              role="alert"
            >
              {{ sendError }}
            </div>

            <div class="recommend-dialog__actions">
              <button
                type="button"
                class="recommend-btn recommend-btn--ghost"
                @click="emit('close')"
              >
                Cancelar
              </button>
              <button
                type="button"
                class="recommend-btn recommend-btn--primary"
                :disabled="selectedIds.length === 0 || sending"
                @click="onSend"
              >
                {{ sending ? 'Enviando…' : 'Enviar' }}
              </button>
            </div>
          </template>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { listFriends } from '../api/social.js'
import { sendRecommendation } from '../api/recommendations.js'

const props = defineProps({
  mediaItemId: { type: Number, required: true },
  mediaTitle: { type: String, required: true },
  show: { type: Boolean, required: true },
})

const emit = defineEmits(['close', 'sent'])

const dialogRef = ref(null)
const friends = ref([])
const friendsLoading = ref(false)
const friendsError = ref('')
const selectedIds = ref([])
const message = ref('')
const sending = ref(false)
const sendError = ref('')

// Al abrir: cargar amigos y auto-focus
watch(() => props.show, async (isOpen) => {
  if (isOpen) {
    selectedIds.value = []
    message.value = ''
    sendError.value = ''
    await loadFriends()
    await nextTick()
    dialogRef.value?.focus()
  }
}, { immediate: true })

async function loadFriends() {
  friendsLoading.value = true
  friendsError.value = ''
  try {
    friends.value = await listFriends()
  } catch (err) {
    friendsError.value = err.message || 'Error al cargar amigos'
  } finally {
    friendsLoading.value = false
  }
}

async function onSend() {
  sending.value = true
  sendError.value = ''
  const errors = []

  for (const receiverId of selectedIds.value) {
    try {
      await sendRecommendation(receiverId, props.mediaItemId, message.value || null)
    } catch (err) {
      errors.push(err.message || `Error enviando a usuario ${receiverId}`)
    }
  }

  sending.value = false

  if (errors.length === 0) {
    emit('sent')
    emit('close')
  } else {
    // Fallo parcial o total: mostrar errores inline sin cerrar
    sendError.value = errors.join('. ')
  }
}
</script>

<style scoped>
.recommend-overlay {
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

.recommend-dialog {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  padding: 1.75rem;
  max-width: 420px;
  width: 90%;
  outline: none;
  box-shadow: var(--shadow-lg);
  max-height: 85vh;
  overflow-y: auto;
}

.recommend-dialog__header {
  position: relative;
  margin-bottom: 1.25rem;
}

.recommend-dialog__title {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--color-text);
  margin-bottom: 0.15rem;
}

.recommend-dialog__subtitle {
  font-size: 0.85rem;
  color: var(--color-text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding-right: 2rem;
}

.recommend-dialog__close {
  position: absolute;
  top: 0;
  right: 0;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--color-text-muted);
  padding: 0.25rem;
  border-radius: var(--radius-sm);
  transition: color var(--transition-fast), background var(--transition-fast);
}

.recommend-dialog__close:hover {
  color: var(--color-text);
  background: var(--color-surface-hover);
}

.recommend-dialog__loading {
  text-align: center;
  padding: 2rem 0;
  color: var(--color-text-muted);
  font-size: 0.85rem;
}

.recommend-loader {
  width: 1.5rem;
  height: 1.5rem;
  border: 2.5px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: recommend-spin 0.7s linear infinite;
  margin: 0 auto 0.75rem;
}

@keyframes recommend-spin { to { transform: rotate(360deg); } }

.recommend-dialog__error {
  padding: 0.5rem 0.75rem;
  background: var(--color-error-bg);
  color: var(--color-error);
  border-radius: var(--radius-sm);
  font-size: 0.82rem;
  font-weight: 500;
  margin-bottom: 0.75rem;
}

.recommend-dialog__empty {
  text-align: center;
  padding: 1.5rem 0;
  color: var(--color-text-muted);
  font-size: 0.85rem;
}

.recommend-dialog__friends {
  border: none;
  padding: 0;
  margin: 0 0 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  max-height: 200px;
  overflow-y: auto;
}

.recommend-friend__label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.45rem 0.6rem;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background var(--transition-fast);
}

.recommend-friend__label:hover {
  background: var(--color-surface-hover);
}

.recommend-friend__checkbox {
  accent-color: var(--color-primary);
  width: 1rem;
  height: 1rem;
  flex-shrink: 0;
}

.recommend-friend__name {
  font-size: 0.87rem;
  font-weight: 500;
  color: var(--color-text);
}

.recommend-dialog__message {
  margin-bottom: 1rem;
}

.recommend-dialog__label {
  display: block;
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.35rem;
}

.recommend-dialog__textarea {
  width: 100%;
  padding: 0.5rem 0.75rem;
  border: 1.5px solid var(--color-border);
  border-radius: var(--radius-sm);
  font-size: 0.87rem;
  color: var(--color-text);
  background: var(--color-surface);
  resize: vertical;
  font-family: inherit;
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}

.recommend-dialog__textarea:focus {
  outline: none;
  border-color: var(--color-border-focus);
  box-shadow: 0 0 0 3px var(--color-primary-light);
}

.recommend-dialog__counter {
  display: block;
  text-align: right;
  font-size: 0.72rem;
  color: var(--color-text-muted);
  margin-top: 0.2rem;
}

.recommend-dialog__actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.6rem;
}

.recommend-btn {
  padding: 0.5rem 1.1rem;
  border: none;
  border-radius: var(--radius-sm);
  font-weight: 600;
  font-size: 0.87rem;
  cursor: pointer;
  transition: background var(--transition-fast);
}

.recommend-btn--ghost {
  background: var(--color-bg);
  color: var(--color-text-secondary);
}

.recommend-btn--ghost:hover {
  background: var(--color-border-light);
}

.recommend-btn--primary {
  background: var(--color-primary);
  color: var(--color-text-inverse);
}

.recommend-btn--primary:hover:not(:disabled) {
  background: var(--color-primary-hover);
}

.recommend-btn--primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Transition */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 200ms ease;
}

.modal-enter-active .recommend-dialog,
.modal-leave-active .recommend-dialog {
  transition: transform 200ms ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .recommend-dialog {
  transform: scale(0.96) translateY(8px);
}

.modal-leave-to .recommend-dialog {
  transform: scale(0.96) translateY(8px);
}

.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
</style>
