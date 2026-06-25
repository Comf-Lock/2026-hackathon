import { createRouter, createWebHistory } from 'vue-router'
import LandingView from './views/LandingView.vue'
import ProfileView from './views/ProfileView.vue'

const routes = [
  { path: '/', name: 'landing', component: LandingView },
  { path: '/profile', name: 'profile', component: ProfileView, meta: { requiresAuth: true } },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})
