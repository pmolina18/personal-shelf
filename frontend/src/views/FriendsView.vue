<template>
  <section
    class="friends-view"
    aria-label="Friends"
  >
    <div class="friends-header">
      <h1 class="page-title">
        Friends
      </h1>
      <p class="page-subtitle">
        Manage your connections
      </p>
    </div>

    <!-- Search users -->
    <div class="friends-section">
      <h2 class="section-title">
        Find users
      </h2>
      <div class="search-row">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search by username…"
          aria-label="Search users by username"
          class="search-input"
        >
      </div>
      <div
        v-if="searchError"
        class="inline-error"
        role="alert"
      >
        {{ searchError }}
      </div>
      <ul
        v-if="searchResults.length"
        class="user-list"
      >
        <li
          v-for="u in searchResults"
          :key="u.id"
          class="user-item"
        >
          <span class="user-name">{{ u.username }}</span>
          <button
            class="btn-add-friend"
            :disabled="sendingTo === u.id"
            :aria-label="`Add ${u.username} as friend`"
            @click="onSendRequest(u)"
          >
            <svg
              v-if="sendingTo !== u.id"
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2.5"
              stroke-linecap="round"
            ><path d="M12 5v14M5 12h14" /></svg>
            <span v-else>…</span>
          </button>
        </li>
      </ul>
      <p
        v-if="searchDone && searchResults.length === 0"
        class="empty-hint"
      >
        No users found.
      </p>
    </div>

    <!-- Sent requests (waiting for approval) -->
    <div
      v-if="sent.length"
      class="friends-section"
    >
      <h2 class="section-title">
        Sent requests
      </h2>
      <ul class="user-list">
        <li
          v-for="req in sent"
          :key="req.id"
          class="user-item"
        >
          <span class="user-name">{{ req.to_user.username }}</span>
          <span class="badge-pending">Pending</span>
        </li>
      </ul>
    </div>

    <!-- Pending requests -->
    <div class="friends-section">
      <h2 class="section-title">
        Pending requests
      </h2>
      <div
        v-if="pendingLoading"
        class="inline-loading"
        role="status"
      >
        Loading…
      </div>
      <div
        v-else-if="pendingError"
        class="inline-error"
        role="alert"
      >
        {{ pendingError }}
      </div>
      <p
        v-else-if="pending.length === 0"
        class="empty-hint"
      >
        No pending requests.
      </p>
      <ul
        v-else
        class="user-list"
      >
        <li
          v-for="req in pending"
          :key="req.id"
          class="user-item"
        >
          <span class="user-name">{{ req.from_user.username }}</span>
          <div class="action-group">
            <button
              class="btn-action btn-action--primary"
              @click="onAccept(req.id)"
            >
              Accept
            </button>
            <button
              class="btn-action btn-action--danger"
              @click="onReject(req.id)"
            >
              Reject
            </button>
          </div>
        </li>
      </ul>
    </div>

    <!-- Friends list -->
    <div class="friends-section">
      <h2 class="section-title">
        My friends
      </h2>
      <div
        v-if="friendsLoading"
        class="inline-loading"
        role="status"
      >
        Loading…
      </div>
      <div
        v-else-if="friendsError"
        class="inline-error"
        role="alert"
      >
        {{ friendsError }}
      </div>
      <p
        v-else-if="friends.length === 0"
        class="empty-hint"
      >
        You don't have any friends yet. Search for users above to get started.
      </p>
      <ul
        v-else
        class="user-list"
      >
        <li
          v-for="f in friends"
          :key="f.id"
          class="user-item"
        >
          <router-link
            :to="`/friends/${f.id}/collection`"
            class="user-name user-name--link"
          >
            {{ f.username }}
          </router-link>
          <button
            class="btn-remove-friend"
            :aria-label="`Remove ${f.username}`"
            @click="onRemoveFriend(f.id)"
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2.5"
              stroke-linecap="round"
            ><path d="M5 12h14" /></svg>
          </button>
        </li>
      </ul>
    </div>
  </section>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import {
  searchUsers,
  sendFriendRequest,
  getPendingRequests,
  getSentRequests,
  acceptRequest,
  rejectRequest,
  listFriends,
  removeFriend,
} from '../api/social.js'

// Search
const searchQuery = ref('')
const searchResults = ref([])
const searchError = ref('')
const searchDone = ref(false)
const sendingTo = ref(null)

// Pending
const pending = ref([])
const pendingLoading = ref(false)
const pendingError = ref('')

// Sent requests
const sent = ref([])

// Friends
const friends = ref([])
const friendsLoading = ref(false)
const friendsError = ref('')

async function onSearch() {
  searchError.value = ''
  searchDone.value = false
  try {
    searchResults.value = await searchUsers(searchQuery.value.trim())
  } catch (err) {
    searchError.value = err.message || 'Search failed'
  } finally {
    searchDone.value = true
  }
}

let debounceTimer = null

watch(searchQuery, () => {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(onSearch, 300)
})

onUnmounted(() => {
  if (debounceTimer) clearTimeout(debounceTimer)
})

async function onSendRequest(user) {
  sendingTo.value = user.id
  searchError.value = ''
  try {
    await sendFriendRequest(user.username)
    searchResults.value = searchResults.value.filter(u => u.id !== user.id)
    await fetchSent()
  } catch (err) {
    searchError.value = err.message || 'Failed to send request'
  } finally {
    sendingTo.value = null
  }
}

async function fetchSent() {
  try {
    sent.value = await getSentRequests()
  } catch {
    // silent
  }
}

async function fetchPending() {
  pendingLoading.value = true
  pendingError.value = ''
  try {
    pending.value = await getPendingRequests()
  } catch (err) {
    pendingError.value = err.message || 'Failed to load requests'
  } finally {
    pendingLoading.value = false
  }
}

async function onAccept(id) {
  try {
    await acceptRequest(id)
    pending.value = pending.value.filter(r => r.id !== id)
    await fetchFriends()
  } catch (err) {
    pendingError.value = err.message || 'Failed to accept'
  }
}

async function onReject(id) {
  try {
    await rejectRequest(id)
    pending.value = pending.value.filter(r => r.id !== id)
  } catch (err) {
    pendingError.value = err.message || 'Failed to reject'
  }
}

async function fetchFriends() {
  friendsLoading.value = true
  friendsError.value = ''
  try {
    friends.value = await listFriends()
  } catch (err) {
    friendsError.value = err.message || 'Failed to load friends'
  } finally {
    friendsLoading.value = false
  }
}

async function onRemoveFriend(id) {
  try {
    await removeFriend(id)
    friends.value = friends.value.filter(f => f.id !== id)
  } catch (err) {
    friendsError.value = err.message || 'Failed to remove friend'
  }
}

onMounted(() => {
  fetchPending()
  fetchFriends()
  fetchSent()
  onSearch()
})
</script>

<style scoped>
.friends-view {
  max-width: 700px;
}

.friends-header {
  margin-bottom: 1.75rem;
}

.page-title {
  font-size: 1.6rem;
  font-weight: 700;
  color: var(--color-text);
  line-height: 1.2;
}

.page-subtitle {
  font-size: 0.87rem;
  color: var(--color-text-muted);
  margin-top: 0.15rem;
}

.friends-section {
  background: var(--color-surface);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  padding: 1.25rem;
  margin-bottom: 1rem;
}

.section-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 0.85rem;
}

.search-row {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.search-input {
  flex: 1;
  padding: 0.5rem 0.75rem;
  border: 1.5px solid var(--color-border);
  border-radius: var(--radius-sm);
  font-size: 0.87rem;
  color: var(--color-text);
  background: var(--color-surface);
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}

.search-input:focus {
  outline: none;
  border-color: var(--color-border-focus);
  box-shadow: 0 0 0 3px var(--color-primary-light);
}

.search-input::placeholder {
  color: var(--color-text-muted);
}

.btn-search {
  padding: 0.5rem 1rem;
  background: var(--color-primary);
  color: var(--color-text-inverse);
  border: none;
  border-radius: var(--radius-sm);
  font-weight: 600;
  font-size: 0.85rem;
  cursor: pointer;
  transition: background var(--transition-fast);
  white-space: nowrap;
}

.btn-search:hover:not(:disabled) {
  background: var(--color-primary-hover);
}

.btn-search:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.user-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.user-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.55rem 0.75rem;
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-sm);
  gap: 0.75rem;
}

.user-name {
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--color-text);
}

.user-name--link {
  color: var(--color-primary);
  text-decoration: none;
}

.user-name--link:hover {
  color: var(--color-primary-hover);
  text-decoration: underline;
}

.action-group {
  display: flex;
  gap: 0.35rem;
}

.btn-action {
  padding: 0.3rem 0.7rem;
  border: none;
  border-radius: var(--radius-sm);
  font-weight: 600;
  font-size: 0.78rem;
  cursor: pointer;
  transition: background var(--transition-fast);
}

.btn-action--primary {
  background: var(--color-primary);
  color: var(--color-text-inverse);
}

.btn-action--primary:hover:not(:disabled) {
  background: var(--color-primary-hover);
}

.btn-action--primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-add-friend {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  border-radius: var(--radius-full);
  background: var(--color-primary);
  color: var(--color-text-inverse);
  border: none;
  cursor: pointer;
  transition: background var(--transition-fast), transform var(--transition-fast);
  flex-shrink: 0;
}

.btn-add-friend:hover:not(:disabled) {
  background: var(--color-primary-hover);
  transform: scale(1.1);
}

.btn-add-friend:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-remove-friend {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  border-radius: var(--radius-full);
  background: var(--color-error-bg);
  color: var(--color-error);
  border: none;
  cursor: pointer;
  transition: background var(--transition-fast), color var(--transition-fast), transform var(--transition-fast);
  flex-shrink: 0;
}

.btn-remove-friend:hover {
  background: var(--color-error);
  color: var(--color-text-inverse);
  transform: scale(1.1);
}

.btn-action--danger {
  background: var(--color-error-bg);
  color: var(--color-error);
}

.btn-action--danger:hover {
  background: var(--color-error);
  color: var(--color-text-inverse);
}

.inline-error {
  padding: 0.45rem 0.7rem;
  background: var(--color-error-bg);
  color: var(--color-error);
  border-radius: var(--radius-sm);
  font-size: 0.82rem;
  font-weight: 500;
  margin-bottom: 0.5rem;
}

.inline-loading {
  font-size: 0.85rem;
  color: var(--color-text-muted);
}

.empty-hint {
  font-size: 0.85rem;
  color: var(--color-text-muted);
}

.badge-pending {
  font-size: 0.72rem;
  font-weight: 600;
  padding: 0.15rem 0.55rem;
  border-radius: var(--radius-full);
  background: var(--color-status-pending-bg);
  color: var(--color-status-pending-text);
}
</style>
