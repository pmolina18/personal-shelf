<template>
  <div
    id="app"
    :class="{ 'sidebar-collapsed': collapsed }"
  >
    <aside
      v-if="!isAuthPage"
      class="sidebar"
      :class="{ collapsed, 'mobile-open': mobileOpen }"
    >
      <div class="sidebar-top">
        <router-link
          to="/"
          class="brand"
          @click="mobileOpen = false"
        >
          <span class="brand-logo">📚</span>
          <Transition name="fade-text">
            <span
              v-if="!collapsed"
              class="brand-name"
            >Personal<span class="brand-accent">Shelf</span></span>
          </Transition>
        </router-link>
      </div>

      <nav
        class="sidebar-nav"
        aria-label="Main navigation"
      >
        <router-link
          to="/"
          class="nav-item"
          :title="collapsed ? 'Catalog' : undefined"
          @click="mobileOpen = false"
        >
          <svg
            class="nav-icon"
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.8"
            stroke-linecap="round"
            stroke-linejoin="round"
          ><rect
            x="3"
            y="3"
            width="7"
            height="7"
            rx="1"
          /><rect
            x="14"
            y="3"
            width="7"
            height="7"
            rx="1"
          /><rect
            x="3"
            y="14"
            width="7"
            height="7"
            rx="1"
          /><rect
            x="14"
            y="14"
            width="7"
            height="7"
            rx="1"
          /></svg>
          <Transition name="fade-text">
            <span
              v-if="!collapsed"
              class="nav-label"
            >Catalog</span>
          </Transition>
        </router-link>
        <router-link
          to="/stats"
          class="nav-item"
          :title="collapsed ? 'Statistics' : undefined"
          @click="mobileOpen = false"
        >
          <svg
            class="nav-icon"
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.8"
            stroke-linecap="round"
            stroke-linejoin="round"
          ><path d="M18 20V10M12 20V4M6 20v-6" /></svg>
          <Transition name="fade-text">
            <span
              v-if="!collapsed"
              class="nav-label"
            >Statistics</span>
          </Transition>
        </router-link>

        <div
          v-if="isAuthenticated"
          class="nav-divider"
        />

        <router-link
          v-if="isAuthenticated"
          to="/explore"
          class="nav-item"
          :title="collapsed ? 'Explore' : undefined"
          @click="mobileOpen = false"
        >
          <svg
            class="nav-icon"
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.8"
            stroke-linecap="round"
            stroke-linejoin="round"
          ><circle
            cx="12"
            cy="12"
            r="10"
          /><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76" /></svg>
          <Transition name="fade-text">
            <span
              v-if="!collapsed"
              class="nav-label"
            >Explore</span>
          </Transition>
        </router-link>
        <router-link
          v-if="isAuthenticated"
          to="/suggestions"
          class="nav-item"
          :title="collapsed ? 'Suggestions' : undefined"
          @click="mobileOpen = false"
        >
          <svg
            class="nav-icon"
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.8"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path d="M9 18h6" />
            <path d="M10 22h4" />
            <path d="M12 2a7 7 0 0 0-4 12.7V17h8v-2.3A7 7 0 0 0 12 2z" />
          </svg>
          <Transition name="fade-text">
            <span
              v-if="!collapsed"
              class="nav-label"
            >Suggestions</span>
          </Transition>
        </router-link>
        <router-link
          v-if="isAuthenticated"
          to="/friends"
          class="nav-item"
          :title="collapsed ? 'Friends' : undefined"
          @click="mobileOpen = false"
        >
          <svg
            class="nav-icon"
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.8"
            stroke-linecap="round"
            stroke-linejoin="round"
          ><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" /><circle
            cx="9"
            cy="7"
            r="4"
          /><path d="M22 21v-2a4 4 0 0 0-3-3.87" /><path d="M16 3.13a4 4 0 0 1 0 7.75" /></svg>
          <Transition name="fade-text">
            <span
              v-if="!collapsed"
              class="nav-label"
            >Friends</span>
          </Transition>
        </router-link>
        <router-link
          v-if="isAuthenticated"
          to="/recommendations"
          class="nav-item"
          :title="collapsed ? 'Recommendations' : undefined"
          @click="mobileOpen = false"
        >
          <svg
            class="nav-icon"
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.8"
            stroke-linecap="round"
            stroke-linejoin="round"
          ><path d="M20 12v10H4V12" /><path d="M2 7h20v5H2z" /><path d="M12 22V7" /><path d="M12 7H7.5a2.5 2.5 0 0 1 0-5C11 2 12 7 12 7z" /><path d="M12 7h4.5a2.5 2.5 0 0 0 0-5C13 2 12 7 12 7z" /></svg>
          <Transition name="fade-text">
            <span
              v-if="!collapsed"
              class="nav-label"
            >Recommendations</span>
          </Transition>
          <span
            v-if="unreadCount > 0"
            class="nav-badge"
          >{{ unreadCount > 99 ? '99+' : unreadCount }}</span>
        </router-link>
      </nav>

      <div class="sidebar-bottom">
        <button
          class="collapse-btn desktop-only"
          aria-label="Toggle sidebar"
          @click="collapsed = !collapsed"
        >
          <svg
            :class="{ flipped: collapsed }"
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          ><path d="m15 18-6-6 6-6" /></svg>
        </button>
        <template v-if="isAuthenticated">
          <Transition name="fade-text">
            <div
              v-if="!collapsed"
              class="user-info"
            >
              <span class="user-avatar">{{ user?.username?.charAt(0)?.toUpperCase() || '?' }}</span>
              <span class="user-name">{{ user?.username || 'User' }}</span>
            </div>
          </Transition>
          <button
            class="logout-btn"
            :title="collapsed ? 'Logout' : undefined"
            aria-label="Logout"
            @click="onLogout"
          >
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="1.8"
              stroke-linecap="round"
              stroke-linejoin="round"
            ><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><polyline points="16 17 21 12 16 7" /><line
              x1="21"
              y1="12"
              x2="9"
              y2="12"
            /></svg>
            <Transition name="fade-text">
              <span
                v-if="!collapsed"
                class="logout-label"
              >Logout</span>
            </Transition>
          </button>
        </template>
        <Transition name="fade-text">
          <span
            v-if="!collapsed && !isAuthenticated"
            class="sidebar-version"
          >v1.0</span>
        </Transition>
      </div>
    </aside>

    <div
      class="main-wrapper"
      :class="{ 'no-sidebar': isAuthPage }"
    >
      <header
        v-if="!isAuthPage"
        class="topbar mobile-only"
      >
        <button
          class="topbar-toggle"
          aria-label="Toggle menu"
          @click="mobileOpen = !mobileOpen"
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
          ><line
            x1="3"
            y1="6"
            x2="21"
            y2="6"
          /><line
            x1="3"
            y1="12"
            x2="21"
            y2="12"
          /><line
            x1="3"
            y1="18"
            x2="21"
            y2="18"
          /></svg>
        </button>
      </header>
      <main :class="isAuthPage ? 'content content--auth' : 'content'">
        <router-view />
      </main>
    </div>

    <div
      v-if="mobileOpen && !isAuthPage"
      class="overlay"
      @click="mobileOpen = false"
    />

    <ReloadPrompt />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuth } from './composables/useAuth.js'
import { getUnreadCount } from './api/recommendations.js'
import ReloadPrompt from './components/ReloadPrompt.vue'

const router = useRouter()
const route = useRoute()
const isAuthPage = computed(() => !!route.meta?.isAuth)
const { user, isAuthenticated, logout } = useAuth()

const collapsed = ref(false)
const mobileOpen = ref(false)
const unreadCount = ref(0)
let pollInterval = null

async function fetchCount() {
  try {
    const data = await getUnreadCount()
    unreadCount.value = data.count
  } catch {
    // Silenciar errores de polling
  }
}

onMounted(() => {
  if (isAuthenticated.value) {
    fetchCount()
    pollInterval = setInterval(fetchCount, 60000)
  }
})

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval)
})

function onLogout() {
  logout()
  router.push('/login')
}
</script>

<style>
/* ── Reset ─────────────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --color-bg: #f0f5f1;
  --color-bg-warm: #f6faf7;
  --color-surface: #ffffff;
  --color-surface-hover: #f0f5f1;
  --color-border: #dce5de;
  --color-border-light: #e8efe9;
  --color-border-focus: #4ead6b;

  --color-primary: #2d9d5a;
  --color-primary-hover: #258a4e;
  --color-primary-light: #d1f0dd;
  --color-primary-subtle: #e8f7ed;
  --color-primary-ghost: rgba(45, 157, 90, 0.08);

  --color-text: #1a2e22;
  --color-text-secondary: #4a6354;
  --color-text-muted: #8a9f90;
  --color-text-inverse: #ffffff;

  --color-status-pending-bg: #f1f4f2;
  --color-status-pending-text: #6b7f72;
  --color-status-in-progress-bg: #e0f0ff;
  --color-status-in-progress-text: #1a73c7;
  --color-status-completed-bg: #d1f0dd;
  --color-status-completed-text: #1a7a3a;

  --color-type-bg: #ede8f5;
  --color-type-text: #5b3fb5;

  --color-type-movie-bg: #edf2fb;
  --color-type-movie-border: #c0d4f0;
  --color-type-series-bg: #edf7f0;
  --color-type-series-border: #b8dcc8;
  --color-type-book-bg: #faf5eb;
  --color-type-book-border: #e2d0a8;

  --color-error: #d93025;
  --color-error-bg: #fef0ef;
  --color-success: #1a7a3a;
  --color-success-bg: #e8f7ed;
  --color-rating: #e8a317;

  --sidebar-width: 220px;
  --sidebar-collapsed-width: 60px;
  --sidebar-bg: #1a2e22;
  --sidebar-text: #c5d8cc;
  --sidebar-text-active: #ffffff;
  --sidebar-hover: rgba(255, 255, 255, 0.06);
  --sidebar-active: rgba(45, 157, 90, 0.2);

  --shadow-xs: 0 1px 2px rgba(26, 46, 34, 0.04);
  --shadow-sm: 0 1px 3px rgba(26, 46, 34, 0.06), 0 1px 2px rgba(26, 46, 34, 0.04);
  --shadow-md: 0 4px 8px -2px rgba(26, 46, 34, 0.08), 0 2px 4px -2px rgba(26, 46, 34, 0.04);
  --shadow-lg: 0 12px 24px -4px rgba(26, 46, 34, 0.1), 0 4px 8px -4px rgba(26, 46, 34, 0.04);
  --shadow-card: 0 1px 3px rgba(26, 46, 34, 0.05);

  --radius-xs: 4px;
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-xl: 20px;
  --radius-full: 9999px;

  --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-base: 250ms cubic-bezier(0.4, 0, 0.2, 1);
}

html {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  font-size: 15px;
  line-height: 1.6;
  color: var(--color-text);
  background: var(--color-bg);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

body { min-height: 100vh; overflow-x: hidden; }

a { color: var(--color-primary); text-decoration: none; transition: color var(--transition-fast); }
a:hover { color: var(--color-primary-hover); }
img { max-width: 100%; display: block; }
button, input, select, textarea { font-family: inherit; font-size: inherit; }

.visually-hidden {
  position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px;
  overflow: hidden; clip: rect(0,0,0,0); white-space: nowrap; border: 0;
}
</style>

<style scoped>
#app { display: flex; min-height: 100vh; }

/* ── Sidebar ───────────────────────────────────────────── */
.sidebar {
  width: var(--sidebar-width);
  background: var(--sidebar-bg);
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0; left: 0; bottom: 0;
  z-index: 200;
  transition: width var(--transition-base);
  overflow: hidden;
}

.sidebar.collapsed {
  width: var(--sidebar-collapsed-width);
}

.sidebar-top {
  display: flex;
  align-items: center;
  padding: 1.1rem 0.85rem;
  min-height: 3.5rem;
}

.brand {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  text-decoration: none;
  color: var(--sidebar-text-active);
  overflow: hidden;
  white-space: nowrap;
}

.brand-logo { font-size: 1.35rem; flex-shrink: 0; }

.brand-name {
  font-size: 1rem;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.brand-accent { color: var(--color-primary); }

.collapse-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.45rem;
  background: none;
  border: none;
  color: var(--sidebar-text);
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: color var(--transition-fast), background var(--transition-fast);
  flex-shrink: 0;
  width: 100%;
}


.collapse-btn:hover {
  color: var(--sidebar-text-active);
  background: var(--sidebar-hover);
}

.collapse-btn svg {
  transition: transform var(--transition-base);
}

.collapse-btn svg.flipped {
  transform: rotate(180deg);
}

.sidebar-nav {
  flex: 1;
  padding: 0.25rem 0.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  padding: 0.55rem 0.7rem;
  border-radius: var(--radius-sm);
  color: var(--sidebar-text);
  text-decoration: none;
  font-size: 0.87rem;
  font-weight: 500;
  transition: all var(--transition-fast);
  white-space: nowrap;
}

.nav-item:hover {
  background: var(--sidebar-hover);
  color: var(--sidebar-text-active);
}

.nav-item.router-link-exact-active {
  background: var(--sidebar-active);
  color: var(--sidebar-text-active);
}

.nav-icon {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
}

.sidebar-bottom {
  padding: 0.75rem 0.85rem;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  min-height: 2.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  overflow: hidden;
  white-space: nowrap;
}

.user-avatar {
  width: 1.6rem;
  height: 1.6rem;
  border-radius: var(--radius-full);
  background: var(--color-primary);
  color: var(--color-text-inverse);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.72rem;
  font-weight: 700;
  flex-shrink: 0;
}

.user-name {
  font-size: 0.82rem;
  font-weight: 500;
  color: var(--sidebar-text);
  overflow: hidden;
  text-overflow: ellipsis;
}

.logout-btn {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  padding: 0.45rem 0.7rem;
  border-radius: var(--radius-sm);
  background: none;
  border: none;
  color: var(--sidebar-text);
  cursor: pointer;
  font-size: 0.87rem;
  font-weight: 500;
  transition: all var(--transition-fast);
  overflow: hidden;
  white-space: nowrap;
  width: 100%;
}

.logout-btn:hover {
  background: var(--sidebar-hover);
  color: var(--sidebar-text-active);
}

.logout-label {
  font-size: 0.87rem;
}

.nav-divider {
  height: 1px;
  background: rgba(255, 255, 255, 0.06);
  margin: 0.35rem 0.7rem;
}

.nav-badge {
  background: var(--color-primary);
  color: #ffffff;
  border-radius: var(--radius-full);
  font-size: 0.65rem;
  font-weight: 700;
  min-width: 1.1rem;
  height: 1.1rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0 0.3rem;
  margin-left: auto;
  flex-shrink: 0;
}

.sidebar-version {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.2);
}

/* ── Main ──────────────────────────────────────────────── */
.main-wrapper {
  flex: 1;
  margin-left: var(--sidebar-width);
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  transition: margin-left var(--transition-base);
}

.sidebar-collapsed .main-wrapper {
  margin-left: var(--sidebar-collapsed-width);
}

.main-wrapper.no-sidebar {
  margin-left: 0;
}

.topbar {
  display: none;
  align-items: center;
  padding: 0.75rem 1.25rem;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  position: sticky;
  top: 0;
  z-index: 100;
}

.topbar-toggle {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.35rem;
  color: var(--color-text);
  display: flex;
  align-items: center;
}

.content {
  flex: 1;
  padding: 2rem 2.5rem 4rem;
  max-width: 1200px;
  width: 100%;
}

.content--auth {
  max-width: none;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.overlay { display: none; }

/* Text fade transition */
.fade-text-enter-active { transition: opacity 150ms ease 80ms; }
.fade-text-leave-active { transition: opacity 80ms ease; }
.fade-text-enter-from, .fade-text-leave-to { opacity: 0; }

/* ── Responsive ────────────────────────────────────────── */
.desktop-only { display: flex; }
.mobile-only { display: none; }

@media (max-width: 900px) {
  .desktop-only { display: none; }
  .mobile-only { display: flex; }

  .sidebar {
    width: var(--sidebar-width);
    transform: translateX(-100%);
  }

  .sidebar.mobile-open {
    transform: translateX(0);
  }

  .sidebar.collapsed {
    width: var(--sidebar-width);
  }

  .main-wrapper {
    margin-left: 0;
  }

  .sidebar-collapsed .main-wrapper {
    margin-left: 0;
  }

  .content {
    padding: 1.5rem 1.25rem 3rem;
  }

  .overlay {
    display: block;
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.35);
    z-index: 150;
    backdrop-filter: blur(2px);
  }
}

@media (max-width: 500px) {
  .content { padding: 1rem 1rem 2.5rem; }
}
</style>
