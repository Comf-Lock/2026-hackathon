// Web-Push subscribe / unsubscribe, wrapped as a composable. Feature-detected: on browsers without
// service-worker / Push support (e.g. iOS Safari unless Event Radar is installed to the home
// screen) `supported` is false and the UI shows a hint instead of a broken toggle — no crash.
//
// Backend contract (Agent-3):
//   GET    /api/push/vapid-public-key  -> { publicKey }
//   POST   /api/push/subscription      (body = PushSubscription.toJSON())
//   DELETE /api/push/subscription      ({ endpoint })
import { ref } from 'vue'
import { api } from '../api'

// The browser needs the VAPID public key as a Uint8Array, but it travels as URL-safe base64.
function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4)
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/')
  const raw = atob(base64)
  const out = new Uint8Array(raw.length)
  for (let i = 0; i < raw.length; i++) out[i] = raw.charCodeAt(i)
  return out
}

export function usePush() {
  const supported = ref(
    typeof navigator !== 'undefined' &&
    'serviceWorker' in navigator &&
    typeof window !== 'undefined' &&
    'PushManager' in window &&
    'Notification' in window,
  )
  // 'default' | 'granted' | 'denied' | 'unsupported'
  const permission = ref(supported.value ? Notification.permission : 'unsupported')
  const subscribed = ref(false)
  const busy = ref(false)
  const error = ref(null)

  // Reflect an existing subscription (e.g. after a reload) into the toggle state.
  async function refresh() {
    if (!supported.value) return
    try {
      const reg = await navigator.serviceWorker.ready
      const sub = await reg.pushManager.getSubscription()
      subscribed.value = !!sub
      permission.value = Notification.permission
    } catch {
      /* non-fatal — leave state as-is */
    }
  }

  async function subscribe() {
    if (!supported.value || busy.value) return
    busy.value = true
    error.value = null
    try {
      const perm = await Notification.requestPermission()
      permission.value = perm
      if (perm !== 'granted') {
        error.value = perm === 'denied'
          ? 'Benachrichtigungen sind im Browser blockiert — bitte in den Seiteneinstellungen erlauben.'
          : 'Berechtigung wurde nicht erteilt.'
        return
      }
      const { publicKey } = await api('/api/push/vapid-public-key')
      const reg = await navigator.serviceWorker.ready
      const sub = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(publicKey),
      })
      await api('/api/push/subscription', { method: 'POST', body: JSON.stringify(sub.toJSON()) })
      subscribed.value = true
    } catch {
      error.value = 'Aktivieren fehlgeschlagen — bitte später erneut versuchen.'
    } finally {
      busy.value = false
    }
  }

  async function unsubscribe() {
    if (!supported.value || busy.value) return
    busy.value = true
    error.value = null
    try {
      const reg = await navigator.serviceWorker.ready
      const sub = await reg.pushManager.getSubscription()
      if (sub) {
        const { endpoint } = sub
        await sub.unsubscribe()
        // Best-effort server cleanup — a failed DELETE shouldn't block the local unsubscribe.
        try {
          await api('/api/push/subscription', { method: 'DELETE', body: JSON.stringify({ endpoint }) })
        } catch {
          /* ignore */
        }
      }
      subscribed.value = false
    } catch {
      error.value = 'Deaktivieren fehlgeschlagen.'
    } finally {
      busy.value = false
    }
  }

  function toggle() {
    return subscribed.value ? unsubscribe() : subscribe()
  }

  return { supported, permission, subscribed, busy, error, refresh, subscribe, unsubscribe, toggle }
}
