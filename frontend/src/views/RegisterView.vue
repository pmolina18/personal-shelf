<template>
  <section
    class="register-view"
    aria-label="Register"
  >
    <div class="auth-card">
      <div class="auth-header">
        <span class="auth-logo">📚</span>
        <h1 class="auth-title">
          Create your account
        </h1>
        <p class="auth-subtitle">
          Start building your personal shelf
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

const router = useRouter()
const { register } = useAuth()

const email = ref('')
const username = ref('')
const password = ref('')
const error = ref('')
const submitting = ref(false)

async function onSubmit() {
  if (password.value.length < 8) {
    error.value = 'Password must be at least 8 characters'
    return
  }
  error.value = ''
  submitting.value = true
  try {
    await register(email.value, username.value, password.value)
    router.push('/')
  } catch (err) {
    error.value = err.message || 'Registration failed'
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.register-view {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 80vh;
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
  font-size: 2.5rem;
  display: block;
  margin-bottom: 0.5rem;
}

.auth-title {
  font-size: 1.4rem;
  font-weight: 700;
  color: var(--color-text);
  margin-bottom: 0.2rem;
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
</style>
