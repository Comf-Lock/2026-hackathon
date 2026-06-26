import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    vue(),
    // PWA shell (Phase 1a): generates manifest.webmanifest + a Workbox service worker that
    // precaches the built app shell, making the app installable / launchable standalone.
    // No push, no view/responsive changes here — those land in a separate phase.
    VitePWA({
      registerType: 'autoUpdate',
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
      workbox: {
        globPatterns: ['**/*.{js,css,html,svg,png,ico,woff2}'],
        // SPA fallback for the app shell — but never hijack the API: those go to the backend.
        navigateFallback: '/index.html',
        navigateFallbackDenylist: [/^\/api/],
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
})
