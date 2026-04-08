<template>
  <div id="app">
    <nav aria-label="Main navigation">
      <router-link to="/">
        Catalog
      </router-link>
      <router-link to="/media/new">
        Add Media
      </router-link>
      <router-link to="/stats">
        Stats
      </router-link>
      <router-link to="/import-export">
        Import / Export
      </router-link>
    </nav>
    <main>
      <router-view />
    </main>
  </div>
</template>

<script setup>
// Root component — renders navigation and the active route view.
</script>
