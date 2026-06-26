<script setup>
// Public map view (logged out + in). Two columns: an OpenStreetMap (Leaflet) map of events with
// coordinates, plus a compact side-list of ALL relevant events. Clicking a located item flies the
// map to its marker and opens the popup; events without coordinates are listed but greyed.
//
// Data comes through the single useEvents layer (limit=100). When a logged-in user has a profile
// with interests, the list/markers can be filtered to those interests (toggle); otherwise all found
// events are shown. Neutral CSS pins (divIcon) — no marker-image bundling, no reach into
// eventDisplay.js. useEvents is consumed, not modified.
import { computed, ref, watch, onMounted, onBeforeUnmount } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { useEvents } from '../composables/useEvents'
import { api } from '../api'
import { formatDateLabel, venueCity } from '../lib/eventFormat'
import MapEventList from '../map/MapEventList.vue'

// Mainfranken / Würzburg as the default focus when there's nothing to fit to.
const WUERZBURG = [49.7913, 9.9534]

// A broad window so the map shows everything geocoded so far, not just "next 20". geo:true so the
// profile home (logged in) resolves as the radius centre and the "Umkreis berücksichtigen" toggle
// applies the radius here too — the query is built with lat/lng/radius_km when useRadius is on.
const { events, total, loading, error, load, filters, center } = useEvents({ geo: true, limit: 100 })

// Radius toggle state mirrors the geo filter. A centre only exists when a profile home (or, later,
// geolocation) resolved — without one the checkbox is shown disabled (graceful: no empty results).
const hasCenter = computed(() => !!center.value)
const radiusOn = computed(() => !!filters.value.useRadius)
const radiusKm = computed(() => filters.value.radiusKm || 0)

// Toggling the radius changes the API query (server-side radius), so reload to refetch the pins +
// list. The online/Vor-Ort filter stays client-side and composes on top of the refetched set.
function setRadiusOn(on) {
  filters.value = { ...filters.value, useRadius: on }
  load()
}

// --- Profile filter (optional, read-only) ----------------------------------------------------
const profileInterests = ref([])
const profileFilterOn = ref(false)
const hasProfile = computed(() => profileInterests.value.length > 0)

async function loadProfile() {
  try {
    const p = await api('/api/profile') // 401 when logged out → caught, no profile filter
    profileInterests.value = Array.isArray(p?.interests) ? p.interests : []
    profileFilterOn.value = profileInterests.value.length > 0 // default on when we have interests
  } catch {
    profileInterests.value = []
    profileFilterOn.value = false
  }
}

// Events to show: profile-filtered (tags ∩ interests) when the toggle is on, else all found.
const displayEvents = computed(() => {
  if (!profileFilterOn.value || !hasProfile.value) return events.value
  const wanted = profileInterests.value.map((s) => String(s).toLowerCase())
  return events.value.filter((e) =>
    (e.tags || []).some((t) => wanted.includes(String(t).toLowerCase())),
  )
})

// --- Online / Vor Ort filter (segmented toggle in the side-list header) -----------------------
// Applied on top of the profile filter and used for BOTH the pins and the list, so the map and the
// right column always stay in sync. 'inperson' = anything not explicitly online (undefined → in-person).
const placeFilter = ref('all') // 'all' | 'inperson' | 'online'
const filteredEvents = computed(() => {
  const list = displayEvents.value
  if (placeFilter.value === 'online') return list.filter((e) => e.is_online === true)
  if (placeFilter.value === 'inperson') return list.filter((e) => !e.is_online)
  return list
})

const located = computed(() =>
  filteredEvents.value.filter((e) => typeof e.lat === 'number' && typeof e.lng === 'number'),
)
const markerCount = computed(() => located.value.length)
const noCoordsCount = computed(() => filteredEvents.value.length - located.value.length)

const selectedId = ref(null)

// --- Leaflet (kept out of Vue's reactivity) --------------------------------------------------
let map = null
let mapEl = null
let markerLayer = null
const markersById = {}

function escapeHtml(s) {
  return String(s ?? '').replace(/[&<>"']/g, (c) => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
  ))
}

function popupHtml(e) {
  const title = escapeHtml(e.title)
  const when = escapeHtml(formatDateLabel(e.start))
  const place = escapeHtml(venueCity(e))
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

// (Re)draw markers for the current display set into a dedicated layer and fit bounds.
function renderMarkers() {
  if (!map) return
  if (markerLayer) markerLayer.clearLayers()
  else markerLayer = L.layerGroup().addTo(map)
  for (const k of Object.keys(markersById)) delete markersById[k]

  const bounds = []
  for (const e of located.value) {
    const m = L.marker([e.lat, e.lng], { icon: pinIcon })
    m.bindPopup(popupHtml(e))
    m.on('popupopen', () => { selectedId.value = e.id })
    markerLayer.addLayer(m)
    markersById[e.id] = m
    bounds.push([e.lat, e.lng])
  }
  if (bounds.length) map.fitBounds(bounds, { padding: [40, 40], maxZoom: 14 })
}

// Side-list item clicked → fly to its marker and open the popup.
function focusEvent(e) {
  const m = markersById[e.id]
  if (!map || !m) return
  selectedId.value = e.id
  map.flyTo([e.lat, e.lng], Math.max(map.getZoom(), 13), { duration: 0.6 })
  m.openPopup()
}

// Hover sync: highlight the corresponding marker while hovering its list item.
function hoverEvent(e) {
  const el = e && markersById[e.id]?.getElement()
  document.querySelectorAll('.map-pin.hover').forEach((n) => n.classList.remove('hover'))
  if (el) el.classList.add('hover')
}

watch(filteredEvents, renderMarkers, { flush: 'post' })

onMounted(async () => {
  map = L.map(mapEl, { center: WUERZBURG, zoom: 10, scrollWheelZoom: true })
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>-Mitwirkende',
  }).addTo(map)
  await Promise.all([load(), loadProfile()])
  renderMarkers()
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
        <span class="count">{{ markerCount }} auf der Karte</span>
        <span v-if="noCoordsCount" class="hint">· {{ noCoordsCount }} ohne Ort</span>
      </template>
      <label v-if="hasProfile" class="profile-toggle">
        <input type="checkbox" v-model="profileFilterOn" />
        Nach meinem Profil
      </label>
    </div>

    <p v-if="error" class="state err">Konnte Events nicht laden (API nicht erreichbar).</p>

    <div class="maplayout">
      <div class="mapbox">
        <div ref="mapEl" class="leaflet-host"></div>
        <!-- Empty/sparse overlay: the map still renders (centered on Würzburg), just no markers. -->
        <div v-if="!loading && !error && markerCount === 0" class="overlay">
          <div class="card">
            <strong>Noch keine Event-Koordinaten</strong>
            <p v-if="filteredEvents.length">{{ filteredEvents.length }} Event(s) gelistet, aber {{ noCoordsCount }} ohne Geo-Daten — Geocoding läuft serverseitig.</p>
            <p v-else>Sobald Events mit Ort vorliegen, erscheinen sie hier als Marker.</p>
          </div>
        </div>
      </div>

      <MapEventList
        class="side"
        :events="filteredEvents"
        :selected-id="selectedId"
        v-model:filter="placeFilter"
        :radius-on="radiusOn"
        :radius-km="radiusKm"
        :has-center="hasCenter"
        @update:radius-on="setRadiusOn"
        @select="focusEvent"
        @hover="hoverEvent"
      />
    </div>
  </div>
</template>

<style scoped>
.mapwrap { max-width: 1240px; margin: 0 auto; padding: 22px 22px 40px; }
.toolbar { display: flex; align-items: baseline; gap: 10px; flex-wrap: wrap; margin-bottom: 14px; }
.title { font-size: 20px; margin: 0 6px 0 0; letter-spacing: -.3px; }
.count { color: var(--muted); font-size: 13px; font-weight: 600; }
.hint { color: var(--faint); font-size: 12.5px; }
.profile-toggle { margin-left: auto; display: flex; align-items: center; gap: 6px; font-size: 12.5px; color: var(--muted); font-weight: 600; cursor: pointer; }
.state { color: var(--muted); font-size: 14px; }
.state.err { color: var(--accent); }

/* Two columns: wide map + narrow side-list. Both share one height; the list scrolls. */
.maplayout { display: grid; grid-template-columns: 1fr 320px; gap: 14px; height: calc(100vh - 200px); min-height: 380px; }
.mapbox { position: relative; border: 1px solid var(--line); border-radius: 12px; overflow: hidden; box-shadow: var(--shadow); }
.leaflet-host { height: 100%; width: 100%; }
.side { min-height: 0; }

.overlay { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; pointer-events: none; z-index: 500; }
.overlay .card { background: var(--card); border: 1px solid var(--line); border-radius: 12px; padding: 18px 22px; box-shadow: var(--shadow); max-width: 340px; text-align: center; pointer-events: auto; }
.overlay .card p { margin: 6px 0 0; color: var(--muted); font-size: 13px; }

/* Narrow screens: stack the list under the map. */
@media (max-width: 880px) {
  .maplayout { grid-template-columns: 1fr; height: auto; }
  .leaflet-host { height: 56vh; min-height: 320px; }
  .side { height: auto; max-height: 50vh; }
}
</style>

<!-- Unscoped: the divIcon markup is injected by Leaflet outside this component's scope. -->
<style>
.map-pin .dot {
  display: block; width: 16px; height: 16px; border-radius: 50%;
  background: var(--accent, #b8324f); border: 2px solid #fff;
  box-shadow: 0 1px 4px rgba(20, 24, 31, .4);
  transition: transform .12s ease;
}
.map-pin.hover .dot { transform: scale(1.45); }
.mappop a { color: var(--accent, #b8324f); font-weight: 700; text-decoration: none; }
</style>
