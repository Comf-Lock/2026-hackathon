<script setup>
// Public map view (logged out + in). Renders events with coordinates as markers on an
// OpenStreetMap (Leaflet) map. Light, self-contained fetch via the shared api() transport — does
// NOT touch useEventSearch/EventCard/DashboardView (the unified data layer comes later in the
// refactor). Neutral CSS pins (divIcon) so we don't depend on Leaflet's bundler-fragile marker
// images and don't reach into eventDisplay.js for colours.
import { ref, onMounted, onBeforeUnmount } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { api } from '../api'
import { MONTHS_SHORT, dayKey, hhmm } from '../calendar/calendarRange'

// Mainfranken / Würzburg as the default focus when there's nothing to fit to.
const WUERZBURG = [49.7913, 9.9534]

const loading = ref(true)
const error = ref(null)
const markerCount = ref(0)
const noCoordsCount = ref(0)
const total = ref(0)

let map = null
let mapEl = null

// TZ-safe (string-slice) date label for the popup — consistent with calendarRange.
function dateLabel(iso) {
  const d = dayKey(iso)
  if (!d) return 'Termin offen'
  const [y, m, day] = d.split('-')
  const t = hhmm(iso)
  return `${Number(day)}. ${MONTHS_SHORT[Number(m) - 1]} ${y}${t ? `, ${t}` : ''}`
}

function escapeHtml(s) {
  return String(s ?? '').replace(/[&<>"']/g, (c) => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
  ))
}

function popupHtml(e) {
  const title = escapeHtml(e.title)
  const when = escapeHtml(dateLabel(e.start))
  const place = escapeHtml([e.venue_name, e.city].filter(Boolean).join(', '))
  const link = e.url
    ? `<a href="${escapeHtml(e.url)}" target="_blank" rel="noopener">Zum Event ↗</a>`
    : ''
  return `<div class="mappop"><strong>${title}</strong><br><span>${when}</span>${place ? `<br><span>${place}</span>` : ''}${link ? `<br>${link}` : ''}</div>`
}

const pinIcon = L.divIcon({
  className: 'map-pin',
  html: '<span class="dot"></span>',
  iconSize: [18, 18],
  iconAnchor: [9, 9],
  popupAnchor: [0, -9],
})

async function load() {
  loading.value = true
  error.value = null
  try {
    // Load a broad window so the map shows everything geocoded so far, not just "next 20".
    const data = await api('/api/events?limit=100')
    const items = data.items || []
    total.value = data.total ?? items.length

    const located = items.filter((e) => typeof e.lat === 'number' && typeof e.lng === 'number')
    noCoordsCount.value = items.length - located.length
    markerCount.value = located.length

    const bounds = []
    for (const e of located) {
      const m = L.marker([e.lat, e.lng], { icon: pinIcon }).addTo(map)
      m.bindPopup(popupHtml(e))
      bounds.push([e.lat, e.lng])
    }
    if (bounds.length) map.fitBounds(bounds, { padding: [40, 40], maxZoom: 14 })
  } catch (e) {
    error.value = e
    markerCount.value = 0
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  map = L.map(mapEl, { center: WUERZBURG, zoom: 10, scrollWheelZoom: true })
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>-Mitwirkende',
  }).addTo(map)
  await load()
})

onBeforeUnmount(() => {
  if (map) { map.remove(); map = null }
})
</script>

<template>
  <div class="mapwrap">
    <div class="toolbar">
      <h1 class="title">Karte</h1>
      <span class="count" v-if="loading">lädt…</span>
      <template v-else>
        <span class="count">{{ markerCount }} Event{{ markerCount === 1 ? '' : 's' }} auf der Karte</span>
        <span v-if="noCoordsCount" class="hint">· {{ noCoordsCount }} ohne Ort werden nicht angezeigt</span>
      </template>
    </div>

    <p v-if="error" class="state err">Konnte Events nicht laden (API nicht erreichbar).</p>

    <div class="mapbox">
      <div ref="mapEl" class="leaflet-host"></div>
      <!-- Empty/sparse overlay: the map still renders (centered on Würzburg), just no markers. -->
      <div v-if="!loading && !error && markerCount === 0" class="overlay">
        <div class="card">
          <strong>Noch keine Event-Koordinaten</strong>
          <p v-if="total">{{ total }} Event{{ total === 1 ? '' : 's' }} vorhanden, aber {{ noCoordsCount }} ohne Geo-Daten — Geocoding läuft serverseitig.</p>
          <p v-else>Sobald Events mit Ort vorliegen, erscheinen sie hier als Marker.</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.mapwrap { max-width: 1240px; margin: 0 auto; padding: 22px 22px 40px; }
.toolbar { display: flex; align-items: baseline; gap: 10px; flex-wrap: wrap; margin-bottom: 14px; }
.title { font-size: 20px; margin: 0 6px 0 0; letter-spacing: -.3px; }
.count { color: var(--muted); font-size: 13px; font-weight: 600; }
.hint { color: var(--faint); font-size: 12.5px; }
.state { color: var(--muted); font-size: 14px; }
.state.err { color: var(--accent); }

.mapbox { position: relative; border: 1px solid var(--line); border-radius: 12px; overflow: hidden; box-shadow: var(--shadow); }
.leaflet-host { height: calc(100vh - 200px); min-height: 360px; width: 100%; }

.overlay { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; pointer-events: none; z-index: 500; }
.overlay .card { background: var(--card); border: 1px solid var(--line); border-radius: 12px; padding: 18px 22px; box-shadow: var(--shadow); max-width: 340px; text-align: center; pointer-events: auto; }
.overlay .card p { margin: 6px 0 0; color: var(--muted); font-size: 13px; }
</style>

<!-- Unscoped: the divIcon markup is injected by Leaflet outside this component's scope. -->
<style>
.map-pin .dot {
  display: block; width: 16px; height: 16px; border-radius: 50%;
  background: var(--accent, #b8324f); border: 2px solid #fff;
  box-shadow: 0 1px 4px rgba(20, 24, 31, .4);
}
.mappop a { color: var(--accent, #b8324f); font-weight: 700; text-decoration: none; }
</style>
