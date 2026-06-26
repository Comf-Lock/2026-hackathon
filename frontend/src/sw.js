// Custom service worker (vite-plugin-pwa `injectManifest`). Keeps the installable app-shell
// precaching from the generateSW phase AND adds Web-Push handling (push + notificationclick),
// which generateSW cannot express.
import { precacheAndRoute, createHandlerBoundToURL } from 'workbox-precaching'
import { NavigationRoute, registerRoute } from 'workbox-routing'

// Precache the built app shell. vite-plugin-pwa injects the file manifest into self.__WB_MANIFEST
// at build time (this exact reference is required by injectManifest).
precacheAndRoute(self.__WB_MANIFEST)

// SPA navigation fallback to the precached index.html — but never hijack /api/* (backend) or the
// SW asset itself. Mirrors the old generateSW navigateFallback + denylist.
const navigationRoute = new NavigationRoute(createHandlerBoundToURL('/index.html'), {
  denylist: [/^\/api/, /\/sw\.js$/],
})
registerRoute(navigationRoute)

// registerType:'autoUpdate' — activate the new SW immediately and take over open clients.
self.skipWaiting()
self.addEventListener('activate', (event) => event.waitUntil(self.clients.claim()))

// --- Web Push --------------------------------------------------------------------------------
// A push arrives → show a system notification. Payload is JSON from the backend:
//   { title, body, icon?, url? }. Falls back gracefully if the payload is empty or not JSON.
self.addEventListener('push', (event) => {
  let data = {}
  if (event.data) {
    try {
      data = event.data.json()
    } catch {
      data = { body: event.data.text() }
    }
  }
  const title = data.title || 'Event Radar'
  const options = {
    body: data.body || 'Es gibt neue passende Events.',
    icon: data.icon || '/icons/pwa-192.png',
    badge: '/icons/pwa-192.png',
    data: { url: data.url || '/' },
  }
  event.waitUntil(self.registration.showNotification(title, options))
})

// Clicking the notification → focus an existing app window (navigating it to the target) or open
// a new one.
self.addEventListener('notificationclick', (event) => {
  event.notification.close()
  const targetUrl = (event.notification.data && event.notification.data.url) || '/'
  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      for (const client of clientList) {
        if ('focus' in client) {
          if ('navigate' in client) client.navigate(targetUrl)
          return client.focus()
        }
      }
      if (self.clients.openWindow) return self.clients.openWindow(targetUrl)
      return undefined
    }),
  )
})
