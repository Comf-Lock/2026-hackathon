<script setup>
import { computed, onMounted } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'
import BrandLogo from './components/BrandLogo.vue'
import { useAuth } from './composables/useAuth'

const { user, loading, fetchMe, login, logout } = useAuth()
const route = useRoute()

// Dashboard, landing, calendar and map all use the wide (1240px) shell so content lines up under
// the header bar in every view.
const wideHeader = computed(() => ['dashboard', 'landing', 'calendar', 'map'].includes(route.name))

// "Liste" points logged-in users at their dashboard, visitors at the public index.
const listTarget = computed(() => (user.value ? '/dashboard' : '/'))

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
        <RouterLink :to="listTarget" class="vlink" :class="{ on: !['calendar', 'map'].includes(route.name) }">Liste</RouterLink>
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
          <button class="btn ghost" @click="logout">Abmelden</button>
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
</style>
