<template>
  <section
    class="register-view"
    aria-label="Register"
  >
    <div class="auth-card">
      <div class="auth-header">
        <svg
          class="auth-logo"
          width="56"
          height="56"
          viewBox="0 0 32 32"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          aria-hidden="true"
        >
          <!-- bookmark -->
          <path
            d="M8 4 h16 v26 l-8 -5.5 l-8 5.5 Z"
            stroke="var(--color-border)"
            stroke-width="1.8"
            stroke-linejoin="round"
            fill="none"
          />
          <!-- play -->
          <path
            d="M13 11 L13 21 L22 16 Z"
            fill="var(--color-primary)"
            stroke="var(--color-primary)"
            stroke-width="1"
            stroke-linejoin="round"
          />
        </svg>
        <h1 class="auth-title">
          Shelf<span class="auth-title-accent">d</span>
        </h1>
        <p class="auth-subtitle">
          Create your account
        </p>
      </div>

      <form
        class="auth-form"
        @submit.prevent="onSubmit"
      >
        <div
          v-if="error"
          class="auth-error"
          role="alert"
        >
          {{ error }}
        </div>

        <div class="form-field">
          <label
            for="register-email"
            class="form-label"
          >Email</label>
          <input
            id="register-email"
            v-model="email"
            type="email"
            required
            autocomplete="email"
            placeholder="you@example.com"
            aria-label="Email address"
            class="form-input"
          >
        </div>

        <div class="form-field">
          <label
            for="register-username"
            class="form-label"
          >Username</label>
          <input
            id="register-username"
            v-model="username"
            type="text"
            required
            autocomplete="username"
            placeholder="Choose a username"
            aria-label="Username"
            class="form-input"
          >
        </div>

        <div class="form-field">
          <label
            for="register-password"
            class="form-label"
          >Password</label>
          <input
            id="register-password"
            v-model="password"
            type="password"
            required
            minlength="8"
            autocomplete="new-password"
            placeholder="At least 8 characters"
            aria-label="Password"
            class="form-input"
          >
          <span
            v-if="password && password.length < 8"
            class="field-hint field-hint--warn"
          >
            Password must be at least 8 characters
          </span>
        </div>

        <button
          type="submit"
          class="btn-submit"
          :disabled="submitting || (password.length > 0 && password.length < 8)"
        >
          {{ submitting ? 'Creating account…' : 'Create account' }}
        </button>
      </form>

      <!-- Sección de acceso denegado (403) -->
      <div
        v-if="accessDenied"
        class="access-denied-section"
      >
        <div
          v-if="accessRequestSent"
          class="access-denied-success"
          role="status"
        >
          Tu solicitud de acceso ha sido enviada y está pendiente de aprobación.
        </div>

        <template v-else>
          <div
            class="auth-error"
            role="alert"
          >
            {{ error }}
          </div>

          <button
            type="button"
            class="btn-request-access"
            :disabled="requestingAccess"
            @click="onRequestAccess"
          >
            {{ requestingAccess ? 'Solicitando...' : 'Solicitar acceso' }}
          </button>

          <div
            v-if="accessRequestError"
            class="access-request-error"
            role="alert"
          >
            {{ accessRequestError }}
          </div>
        </template>
      </div>

      <p class="auth-footer">
        Already have an account?
        <router-link to="/login">
          Sign in
        </router-link>
      </p>
    </div>
  </section>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth.js'
import { requestAccess } from '../api/auth.js'

const router = useRouter()
const { register } = useAuth()

const email = ref('')
const username = ref('')
const password = ref('')
const error = ref('')
const submitting = ref(false)

// Estado para flujo de acceso denegado (403)
const accessDenied = ref(false)
const requestingAccess = ref(false)
const accessRequestSent = ref(false)
const accessRequestError = ref('')

async function onSubmit() {
  if (password.value.length < 8) {
    error.value = 'Password must be at least 8 characters'
    return
  }
  error.value = ''
  accessDenied.value = false
  submitting.value = true
  try {
    await register(email.value, username.value, password.value)
    router.push('/')
  } catch (err) {
    error.value = err.message || 'Registration failed'
    if (err.message && err.message.includes('No estás en la lista')) {
      accessDenied.value = true
    }
  } finally {
    submitting.value = false
  }
}

async function onRequestAccess() {
  requestingAccess.value = true
  accessRequestError.value = ''
  try {
    await requestAccess(email.value)
    accessRequestSent.value = true
  } catch (err) {
    accessRequestError.value = err.message
  } finally {
    requestingAccess.value = false
  }
}
</script>

<style scoped>
.register-view {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
}

.auth-card {
  width: 100%;
  max-width: 400px;
  background: var(--color-surface);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-lg);
  padding: 2.5rem 2rem;
  box-shadow: var(--shadow-md);
}

.auth-header {
  text-align: center;
  margin-bottom: 1.75rem;
}

.auth-logo {
  display: block;
  margin: 0 auto 0.5rem;
}

.auth-title {
  font-size: 1.6rem;
  font-weight: 700;
  color: var(--color-text);
  margin-bottom: 0.2rem;
}

.auth-title-accent {
  color: var(--color-primary);
}

.auth-subtitle {
  font-size: 0.87rem;
  color: var(--color-text-muted);
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.auth-error {
  padding: 0.6rem 0.85rem;
  background: var(--color-error-bg);
  color: var(--color-error);
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
  font-weight: 500;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.form-label {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--color-text-secondary);
}

.form-input {
  padding: 0.55rem 0.75rem;
  border: 1.5px solid var(--color-border);
  border-radius: var(--radius-sm);
  font-size: 0.9rem;
  color: var(--color-text);
  background: var(--color-surface);
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}

.form-input:focus {
  outline: none;
  border-color: var(--color-border-focus);
  box-shadow: 0 0 0 3px var(--color-primary-light);
}

.form-input::placeholder {
  color: var(--color-text-muted);
}

.field-hint {
  font-size: 0.78rem;
}

.field-hint--warn {
  color: var(--color-rating);
}

.btn-submit {
  padding: 0.6rem 1rem;
  background: var(--color-primary);
  color: var(--color-text-inverse);
  border: none;
  border-radius: var(--radius-sm);
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
  transition: background var(--transition-fast);
  margin-top: 0.25rem;
}

.btn-submit:hover:not(:disabled) {
  background: var(--color-primary-hover);
}

.btn-submit:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.auth-footer {
  text-align: center;
  margin-top: 1.25rem;
  font-size: 0.85rem;
  color: var(--color-text-muted);
}

.auth-footer a {
  color: var(--color-primary);
  font-weight: 600;
}

.auth-footer a:hover {
  color: var(--color-primary-hover);
}

.access-denied-section {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-top: 1.25rem;
  padding: 1rem;
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-sm);
}

.access-denied-success {
  padding: 0.6rem 0.85rem;
  background: #e8f5e9;
  color: #2e7d32;
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
  font-weight: 500;
}

.btn-request-access {
  padding: 0.6rem 1rem;
  background: transparent;
  color: var(--color-primary);
  border: 1.5px solid var(--color-primary);
  border-radius: var(--radius-sm);
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
  transition: background var(--transition-fast), color var(--transition-fast);
}

.btn-request-access:hover:not(:disabled) {
  background: var(--color-primary);
  color: var(--color-text-inverse);
}

.btn-request-access:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.access-request-error {
  padding: 0.6rem 0.85rem;
  background: #ffebee;
  color: #c62828;
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
  font-weight: 500;
}
</style>
