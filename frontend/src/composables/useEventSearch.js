// Shared event-search state + API client. Used by both the public LandingView and (via the
// same exported shape) the auth-gated DashboardView — one search implementation, two callers.
//
// Talks to GET /api/events with the contract query params (camelCase filters → snake_case query).
// The endpoint is live on this branch already, but the *filtered* contract (q/city/tag/dates/
// is_online + the full EventOut field set) is owned by Agent-3. Until that lands, unknown query
// params are simply ignored server-side, and if the call fails entirely we fall back to a small
// local fixture so the public index always demos. Switching to the full live endpoint is a no-op
// here — it's already the real call.
import { ref } from 'vue'
import { api } from '../api'

export const EMPTY_FILTERS = { q: '', city: '', tag: '', dateFrom: '', dateTo: '', isOnline: false }

// camelCase filter state → the snake_case query string the API contract expects.
function toQuery(f, { limit = 20, offset = 0 } = {}) {
  const p = new URLSearchParams()
  if (f.q) p.set('q', f.q)
  if (f.city) p.set('city', f.city)
  if (f.tag) p.set('tag', f.tag)
  if (f.dateFrom) p.set('date_from', f.dateFrom)
  if (f.dateTo) p.set('date_to', f.dateTo)
  if (f.isOnline) p.set('is_online', 'true')
  p.set('limit', String(limit))
  p.set('offset', String(offset))
  return p.toString()
}

export function useEventSearch() {
  const filters = ref({ ...EMPTY_FILTERS })
  const events = ref([])
  const total = ref(0)
  const loading = ref(false)
  const error = ref(null)

  async function search() {
    loading.value = true
    error.value = null
    try {
      const data = await api(`/api/events?${toQuery(filters.value)}`)
      events.value = data.items || []
      total.value = data.total ?? events.value.length
    } catch (e) {
      // API unreachable / not yet implementing the contract → degrade to local fixtures so the
      // public landing never looks broken in a standalone-frontend demo. Filtered client-side.
      error.value = e
      const items = filterFixtures(filters.value)
      events.value = items
      total.value = items.length
    } finally {
      loading.value = false
    }
  }

  return { filters, events, total, loading, error, search }
}

// --- Local demo fallback (EventOut-shaped) ---------------------------------------------------
// Mirrors the API contract's EventOut so EventCard renders identically whether data is live or
// mocked. Mainfranken content to match the product's regional focus.
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

function filterFixtures(f) {
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
    return true
  })
}
