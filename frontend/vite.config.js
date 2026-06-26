import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    vue(),
    // PWA: manifest.webmanifest + a service worker. We use `injectManifest` (our own src/sw.js)
    // so the SW can handle Web-Push (push / notificationclick) on top of Workbox precaching — the
    // installable app-shell behaviour from the generateSW phase is preserved inside src/sw.js.
    VitePWA({
      registerType: 'autoUpdate',
      strategies: 'injectManifest',
      srcDir: 'src',
      filename: 'sw.js',
      // Auto-inject the SW registration into index.html so main.js / app code stays untouched.
      injectRegister: 'auto',
      includeAssets: ['logo.svg', 'icons/apple-touch-icon.png'],
      manifest: {
        name: 'Event Radar',
        short_name: 'Event Radar',
        description: 'Alle IT-Events aus Mainfranken an einem Ort — automatisch zusammengeführt.',
        lang: 'de',
        start_url: '/',
        scope: '/',
        display: 'standalone',
        orientation: 'portrait',
        background_color: '#f7f6f3',
        theme_color: '#b8324f',
        icons: [
          { src: 'icons/pwa-192.png', sizes: '192x192', type: 'image/png', purpose: 'any' },
          { src: 'icons/pwa-512.png', sizes: '512x512', type: 'image/png', purpose: 'any' },
          { src: 'icons/pwa-maskable-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
        ],
      },
      // injectManifest controls which built files get precached into self.__WB_MANIFEST. The SPA
      // navigateFallback + /api denylist now live in src/sw.js (NavigationRoute).
      injectManifest: {
        globPatterns: ['**/*.{js,css,html,svg,png,ico,woff2}'],
      },
      devOptions: {
        // Keep the SW off during `vite dev` to avoid caching surprises while developing.
        enabled: false,
      },
    }),
  ],
  server: {
    port: 5173,
    // Allow access via the Tailscale hostname (on-device PWA testing on the phone).
    allowedHosts: ['macbook-pro-von-lars.tail7629bb.ts.net', '.ts.net'],
    proxy: {
      // Proxy API calls to the FastAPI backend so the dev frontend is same-origin
      // (session cookie just works, no CORS dance in the browser).
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  // `vite preview` serves the production build (with the real service worker enabled) — used behind
  // Tailscale Serve over HTTPS so the PWA is installable on the phone. Mirrors `server` so /api +
  // the OAuth login keep working same-origin (X-Forwarded-Host from Tailscale → host-aware redirect).
  preview: {
    port: 4173,
    allowedHosts: ['macbook-pro-von-lars.tail7629bb.ts.net', '.ts.net'],
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
