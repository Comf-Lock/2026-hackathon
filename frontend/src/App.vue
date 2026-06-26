<script setup>
import { computed, onMounted } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import BrandLogo from './components/BrandLogo.vue'
import { useAuth } from './composables/useAuth'

const { user, loading, fetchMe, login, logout } = useAuth()
const route = useRoute()
const router = useRouter()

// Every primary view (dashboard, landing, calendar, map AND profile) uses the wide (1240px) shell,
// so the header bar — logo + tabs — stays at the exact same position across all of them and never
// jumps when navigating (the profile route in particular shares the others' width).
const wideHeader = computed(() =>
  ['dashboard', 'landing', 'calendar', 'map', 'profile'].includes(route.name),
)

// "Suche" points logged-in users at their dashboard, visitors at the public index.
const searchTarget = computed(() => (user.value ? '/dashboard' : '/'))

// Logout clears the session, then sends the user back to the public search/landing page — the
// router guard only runs on navigation, so /dashboard would otherwise linger after logout.
async function onLogout() {
  await logout()
  router.push('/')
}

onMounted(() => fetchMe())
</script>

<template>
  <header>
    <div class="bar" :class="{ wide: wideHeader }">
      <RouterLink to="/" class="brand">
        <BrandLogo :size="34" />
        <span class="word">Event&nbsp;<span>Radar</span></span>
      </RouterLink>

      <nav class="views">
        <RouterLink :to="searchTarget" class="vlink" :class="{ on: ['landing', 'dashboard'].includes(route.name) }">Suche</RouterLink>
        <RouterLink to="/calendar" class="vlink" :class="{ on: route.name === 'calendar' }">Kalender</RouterLink>
        <RouterLink to="/map" class="vlink" :class="{ on: route.name === 'map' }">Karte</RouterLink>
      </nav>

      <nav class="actions">
        <template v-if="loading">
          <span class="muted">…</span>
        </template>
        <template v-else-if="user">
          <RouterLink to="/profile" class="profile-link">
            <img v-if="user.avatar_url" :src="user.avatar_url" alt="" class="avatar" />
            <span>{{ user.display_name || 'Profil' }}</span>
          </RouterLink>
          <button class="btn ghost" @click="onLogout">Abmelden</button>
        </template>
        <template v-else>
          <button class="btn primary" @click="login">Login mit Google</button>
        </template>
      </nav>
    </div>
  </header>

  <RouterView />
</template>

<style scoped>
header {
  position: sticky;
  top: 0;
  background: rgba(247, 246, 243, .9);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--line);
  z-index: 5;
}
.bar {
  max-width: 680px;
  margin: 0 auto;
  padding: 13px 18px;
  display: flex;
  align-items: center;
  gap: 12px;
}
.bar.wide {
  max-width: 1240px;
  padding: 13px 22px;
}
.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 800;
  font-size: 19px;
  letter-spacing: -.4px;
  text-decoration: none;
}
.brand .word span { color: var(--accent); }
.views { display: flex; gap: 3px; margin-left: 18px; background: var(--chip); padding: 3px; border-radius: 9px; }
.vlink { padding: 5px 12px; border-radius: 7px; font-size: 13px; font-weight: 700; text-decoration: none; color: var(--muted); }
.vlink.on { background: var(--card); color: var(--ink); box-shadow: var(--shadow); }
.actions { margin-left: auto; display: flex; align-items: center; gap: 10px; }
.muted { color: var(--muted); font-size: 13px; }
.profile-link {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 13.5px;
  font-weight: 600;
  text-decoration: none;
  color: var(--ink);
}
.avatar { width: 26px; height: 26px; border-radius: 50%; }

/* Mobile header: keep the desktop bar untouched, only adapt below 640px. The bar wraps so the
   nav tabs drop onto their own centred row while brand + actions stay on the first row. The
   wideHeader logic (max-width/padding) is intentionally not touched — only the inner flow. */
@media (max-width: 640px) {
  .bar, .bar.wide { padding: 10px 14px; gap: 8px 10px; flex-wrap: wrap; }
  .brand { font-size: 17px; }
  .views { margin-left: 0; order: 3; width: 100%; justify-content: center; }
  .actions { gap: 7px; }
  .profile-link span { max-width: 92px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .btn.primary { font-size: 13px; }
}
/* Very tight: drop the wordmark but keep the logo so the actions still fit on one row. */
@media (max-width: 380px) {
  .brand .word { display: none; }
}
</style>
