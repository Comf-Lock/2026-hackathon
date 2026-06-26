// The single frontend events data layer. One client for GET /api/events, one error strategy,
// shared by every consumer: LandingView, DashboardView, CalendarView and MapView.
//
// It owns: the camelCase→snake_case query builder, the fetch (single page or paged over a range),
// the filters/events/total/loading/error state, and the local-fixture fallback so no view ever
// looks broken when the API is unreachable. The *filtered* contract (q/city/tag/dates/is_online +
// the full EventOut field set) is the backend's; unknown params are ignored server-side.
import { ref } from 'vue'
import { api } from '../api'

export const EMPTY_FILTERS = { q: '', city: '', tag: '', dateFrom: '', dateTo: '', isOnline: false }

// camelCase filter state → the snake_case query string the API contract expects.
// `center` ({lat,lng}) is the radius-search origin, supplied by useEvents (profile home or
// geolocation), kept out of the filter object because it isn't a user-typed field. Radius is only
// sent when the "Umkreis berücksichtigen" toggle (f.useRadius) is on AND an explicit radius and a
// resolved centre exist — otherwise we degrade to a normal search (the backend ignores a lone
// radius_km anyway).
export function toQuery(f, { limit = 20, offset = 0, center = null } = {}) {
  const p = new URLSearchParams()
  if (f.q) p.set('q', f.q)
  if (f.city) p.set('city', f.city)
  if (f.tag) p.set('tag', f.tag)
  if (f.dateFrom) p.set('date_from', f.dateFrom)
  if (f.dateTo) p.set('date_to', f.dateTo)
  if (f.isOnline) p.set('is_online', 'true')
  if (f.useRadius && f.radiusKm && center && center.lat != null && center.lng != null) {
    p.set('lat', String(center.lat))
    p.set('lng', String(center.lng))
    p.set('radius_km', String(f.radiusKm))
  }
  p.set('limit', String(limit))
  p.set('offset', String(offset))
  return p.toString()
}

/**
 * Reactive events state + loader.
 *
 * @param {object}  [options]
 * @param {number}  [options.limit=20]      page size sent to the API
 * @param {boolean} [options.paginate=false] page through the whole result set (e.g. a calendar
 *                                           period) instead of just the first page
 * @param {number}  [options.maxPages=10]    runaway guard for the paginate loop
 * @param {boolean} [options.geo=false]       enable radius search: seed a default radius, resolve a
 *                                            centre (profile home when logged in, or geolocation via
 *                                            useMyLocation) and send lat/lng/radius_km. Off by default
 *                                            so non-radius consumers (map, calendar) are unchanged.
 * @returns {{ filters, events, total, loading, error, load, center, locating, geo, useMyLocation }}
 */
export function useEvents({ limit = 20, paginate = false, maxPages = 10, geo = false } = {}) {
  // geo mode adds two radius fields: radiusKm (the slider value) and useRadius (the explicit
  // "Umkreis berücksichtigen" toggle). useRadius starts off and flips on once a centre resolves.
  const filters = ref({ ...EMPTY_FILTERS, ...(geo ? { radiusKm: 40, useRadius: false } : {}) })
  const events = ref([])
  const total = ref(0)
  const loading = ref(false)
  const error = ref(null)

  // Radius-search centre {lat,lng} | null. Resolved lazily from the profile home on first load;
  // useMyLocation() overrides it with the browser's geolocation (for logged-out "near me").
  const center = ref(null)
  const locating = ref(false)
  let centerTried = false

  async function resolveProfileCenter() {
    if (!geo || centerTried) return
    centerTried = true
    try {
      const p = await api('/api/profile') // 401 when logged out → caught, centre stays null
      if (p && typeof p.home_lat === 'number' && typeof p.home_lng === 'number') {
        center.value = { lat: p.home_lat, lng: p.home_lng }
        // Logged-in default: a resolved profile home turns the radius on and seeds the slider from
        // the profile's saved radius_km, so the user's own scope applies without re-adjusting.
        // Replace (not mutate) the filter object so bound SearchMask inputs re-sync.
        filters.value = {
          ...filters.value,
          useRadius: true,
          ...(typeof p.radius_km === 'number' && p.radius_km > 0 ? { radiusKm: p.radius_km } : {}),
        }
      }
    } catch {
      /* no profile / logged out → no centre, radius degrades to a normal search */
    }
  }

  // Logged-out "in meiner Nähe": ask the browser for a location, then reload around it.
  function useMyLocation() {
    if (!geo || !navigator.geolocation) return
    locating.value = true
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        center.value = { lat: pos.coords.latitude, lng: pos.coords.longitude }
        // A freshly located centre exists → default the radius on (same rule as the profile home).
        filters.value = { ...filters.value, useRadius: true }
        locating.value = false
        load()
      },
      () => { locating.value = false },
      { enableHighAccuracy: false, timeout: 8000, maximumAge: 300000 },
    )
  }

  async function load() {
    loading.value = true
    error.value = null
    try {
      if (geo) await resolveProfileCenter()
      const c = center.value
      if (paginate) {
        // Page at the API's row cap so a wide window (calendar year view) isn't silently truncated.
        const acc = []
        let offset = 0
        let tot = 0
        for (let page = 0; page < maxPages; page++) {
          const data = await api(`/api/events?${toQuery(filters.value, { limit, offset, center: c })}`)
          const items = data.items || []
          acc.push(...items)
          tot = data.total ?? acc.length
          offset += items.length
          if (items.length === 0 || acc.length >= tot) break
        }
        events.value = acc
        total.value = tot
      } else {
        const data = await api(`/api/events?${toQuery(filters.value, { limit, center: c })}`)
        events.value = data.items || []
        total.value = data.total ?? events.value.length
      }
    } catch (e) {
      // API unreachable / not yet implementing the contract → degrade to local fixtures (filtered
      // client-side) so the UI always demos. One strategy for every consumer.
      error.value = e
      const items = filterFixtures(filters.value, center.value)
      events.value = items
      total.value = items.length
    } finally {
      loading.value = false
    }
  }

  return { filters, events, total, loading, error, load, center, locating, geo, useMyLocation }
}

// --- Local demo fallback (EventOut-shaped) ---------------------------------------------------
// Mirrors the API contract's EventOut so EventCard renders identically whether data is live or
// mocked, and carries lat/lng so the map still shows pins offline. Mainfranken content.
const FIXTURES = [
  {
    id: 9001, title: 'FrankenJS — Vue 3 Deep Dive',
    description: 'Composition API, Suspense und die neuen Reactivity-Transforms in der Praxis.',
    start: '2026-07-18T19:00:00+02:00', end: '2026-07-18T21:30:00+02:00', is_online: false,
    venue_name: 'Mayflower GmbH', address: 'Mainaustraße 0', city: 'Würzburg', postal_code: '97082',
    lat: 49.79, lng: 9.93, organizer: 'FrankenJS', tags: ['Vue', 'Frontend', 'JS'],
    url: 'https://www.meetup.com/frankenjs/', image_url: null, price: 'Kostenlos', language: 'de',
  },
  {
    id: 9002, title: 'Würzburg DATA & ANALYTICS Meetup #27',
    description: 'Data Engineering, BI und KI-Pipelines — mit Pizza & Frankenwein.',
    start: '2026-07-12T18:30:00+02:00', end: null, is_online: false,
    venue_name: 'ZDI Cube', address: null, city: 'Würzburg', postal_code: '97070',
    lat: 49.79, lng: 9.95, organizer: 'ZDI Mainfranken', tags: ['Data', 'KI', 'BI'],
    url: 'https://zdi-mainfranken.de/', image_url: null, price: 'Kostenlos', language: 'de',
  },
  {
    id: 9003, title: 'THWS Platform Engineering Summit',
    description: 'Kubernetes, Plattform-Teams und Developer Experience im Mittelstand.',
    start: '2026-07-21T09:00:00+02:00', end: '2026-07-21T17:00:00+02:00', is_online: false,
    venue_name: 'THWS', address: 'Ignaz-Schön-Str. 11', city: 'Schweinfurt', postal_code: '97421',
    lat: 50.04, lng: 10.23, organizer: 'THWS-FIW', tags: ['DevOps', 'Platform', 'Cloud'],
    url: 'https://fiw.thws.de/', image_url: null, price: 'ab 99 €', language: 'de',
  },
  {
    id: 9004, title: 'AI Remote Pairing Night',
    description: 'Online-Coding-Session rund um LLM-Tooling und Agenten.',
    start: '2026-07-15T19:00:00+02:00', end: null, is_online: true,
    venue_name: null, address: null, city: null, postal_code: null,
    lat: null, lng: null, organizer: 'Mainfranken AI', tags: ['AI/ML', 'Online'],
    url: 'https://example.org/ai-remote', image_url: null, price: 'Kostenlos', language: 'de',
  },
]

// Great-circle distance in km (Haversine) — mirrors the backend's geo.haversine_km so the offline
// fixture fallback filters by radius the same way the API does.
function haversineKm(lat1, lng1, lat2, lng2) {
  const toRad = (d) => (d * Math.PI) / 180
  const dLat = toRad(lat2 - lat1)
  const dLng = toRad(lng2 - lng1)
  const a = Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLng / 2) ** 2
  return 2 * 6371 * Math.asin(Math.sqrt(a))
}

function filterFixtures(f, center = null) {
  return FIXTURES.filter((e) => {
    if (f.q) {
      const hay = `${e.title} ${e.description || ''} ${(e.tags || []).join(' ')}`.toLowerCase()
      if (!hay.includes(f.q.toLowerCase())) return false
    }
    if (f.city && !(e.city || '').toLowerCase().includes(f.city.toLowerCase())) return false
    if (f.tag && !(e.tags || []).some((t) => t.toLowerCase().includes(f.tag.toLowerCase()))) return false
    if (f.isOnline && !e.is_online) return false
    if (f.dateFrom && e.start < f.dateFrom) return false
    if (f.dateTo && e.start.slice(0, 10) > f.dateTo) return false
    if (f.useRadius && f.radiusKm && center && center.lat != null && center.lng != null) {
      if (typeof e.lat !== 'number' || typeof e.lng !== 'number') return false // no coords → excluded
      if (haversineKm(center.lat, center.lng, e.lat, e.lng) > f.radiusKm) return false
    }
    return true
  })
}
