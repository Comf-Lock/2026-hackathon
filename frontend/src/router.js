import { createRouter, createWebHistory } from 'vue-router'
import LandingView from './views/LandingView.vue'
import DashboardView from './views/DashboardView.vue'
import ProfileView from './views/ProfileView.vue'
import CalendarView from './views/CalendarView.vue'
import { useAuth } from './composables/useAuth'

const routes = [
  { path: '/', name: 'landing', component: LandingView },
  // Public calendar — usable logged out AND in (no requiresAuth).
  { path: '/calendar', name: 'calendar', component: CalendarView },
  { path: '/dashboard', name: 'dashboard', component: DashboardView, meta: { requiresAuth: true } },
  { path: '/profile', name: 'profile', component: ProfileView, meta: { requiresAuth: true } },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Auth gate: resolve the session once (cached), then protect auth-only routes and bounce
// already-logged-in users from the public landing straight to their dashboard.
router.beforeEach(async (to) => {
  const { user, fetchMe } = useAuth()
  await fetchMe()
  if (to.meta.requiresAuth && !user.value) return { name: 'landing' }
  if (to.name === 'landing' && user.value) return { name: 'dashboard' }
})
