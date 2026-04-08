<template>
  <div
    id="app"
    :class="{ 'sidebar-collapsed': collapsed }"
  >
    <aside
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
        <router-link
          to="/import-export"
          class="nav-item"
          :title="collapsed ? 'Import / Export' : undefined"
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
          ><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="17 8 12 3 7 8" /><line
            x1="12"
            y1="3"
            x2="12"
            y2="15"
          /></svg>
          <Transition name="fade-text">
            <span
              v-if="!collapsed"
              class="nav-label"
            >Import / Export</span>
          </Transition>
        </router-link>
      </nav>

      <div class="sidebar-bottom">
        <Transition name="fade-text">
          <span
            v-if="!collapsed"
            class="sidebar-version"
          >v1.0</span>
        </Transition>
      </div>
    </aside>

    <div class="main-wrapper">
      <header class="topbar mobile-only">
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
      <main class="content">
        <router-view />
      </main>
    </div>

    <div
      v-if="mobileOpen"
      class="overlay"
      @click="mobileOpen = false"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
const collapsed = ref(false)
const mobileOpen = ref(false)
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
  justify-content: space-between;
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
  background: none;
  border: none;
  color: var(--sidebar-text);
  cursor: pointer;
  padding: 0.3rem;
  border-radius: var(--radius-xs);
  transition: color var(--transition-fast), background var(--transition-fast);
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
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
  overflow: hidden;
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
