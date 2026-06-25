import { ref } from 'vue'
import { api } from '../api'

// Shared auth state (module-level singletons) across the app.
const user = ref(null)
const loading = ref(true)
let fetched = false

async function fetchMe(force = false) {
  if (fetched && !force) return user.value
  loading.value = true
  try {
    user.value = await api('/api/auth/me')
  } catch {
    user.value = null
  } finally {
    loading.value = false
    fetched = true
  }
  return user.value
}

function login() {
  // Full-page navigation into the backend OAuth flow.
  window.location.href = '/api/auth/google/login'
}

async function logout() {
  try {
    await api('/api/auth/logout', { method: 'POST' })
  } finally {
    user.value = null
  }
}

export function useAuth() {
  return { user, loading, fetchMe, login, logout }
}
