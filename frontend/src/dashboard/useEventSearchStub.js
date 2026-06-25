// TEMP STUB — owned by Agent-2 until Agent-1's real composable lands.
//
// Mirrors the FIXED interface agreed with Agent-1:
//   useEventSearch() -> { filters, events, total, loading, error, search() }
// and the API contract implemented by Agent-3:
//   GET /api/events?q=&city=&tag=&date_from=&date_to=&is_online=&limit=&offset=
//   200: { total: int, items: [EventOut, …] }
//
// Each call returns its OWN reactive state, so the dashboard can run two independent
// searches (the main list + the "Für dich" recommendations) side by side.
//
// While Agent-3's GET /api/events is not deployed, search() falls back to in-memory demo
// events (EventOut-shaped) so the dashboard is fully usable. Swap the whole file out via
// ./searchKit.js once the real composable is merged — no DashboardView changes needed.
import { reactive, ref } from 'vue'
import { api } from '../api'

function emptyFilters() {
  return { q: '', city: '', tag: '', dateFrom: '', dateTo: '', isOnline: false }
}

// Mainfranken demo events in the canonical EventOut shape (see backend models.Event).
const DEMO_EVENTS = [
  {
    id: 1, title: 'Würzburg DATA & ANALYTICS Meetup #27',
    description: 'Data Engineering, BI und KI-Pipelines aus der Region.',
    start: '2026-07-12T18:30:00+02:00', end: null, is_online: false,
    venue_name: 'ZDI Cube', city: 'Würzburg', postal_code: '97070',
    organizer: 'Data Meetup Würzburg', tags: ['Data', 'KI', 'BI'],
    url: 'https://example.org/e/1', price: 'Kostenlos', language: 'de',
  },
  {
    id: 2, title: 'FrankenJS — Vue 3 Deep Dive',
    description: 'Composition API, Reaktivität und Performance in Vue 3.',
    start: '2026-07-18T19:00:00+02:00', end: null, is_online: false,
    venue_name: 'Mayflower GmbH', city: 'Würzburg', postal_code: '97082',
    organizer: 'FrankenJS', tags: ['Vue', 'Frontend', 'JavaScript'],
    url: 'https://example.org/e/2', price: 'Kostenlos', language: 'de',
  },
  {
    id: 3, title: 'AI & Recruiting Night Mainfranken',
    description: 'KI im Recruiting — Praxis und Networking.',
    start: '2026-07-15T19:00:00+02:00', end: null, is_online: false,
    venue_name: 'Posthalle', city: 'Würzburg', postal_code: '97070',
    organizer: 'Mainfranken Tech', tags: ['AI/ML', 'Career', 'Networking'],
    url: 'https://example.org/e/3', price: '15 €', language: 'de',
  },
  {
    id: 4, title: 'THWS Platform Engineering Summit',
    description: 'Kubernetes, Plattformen und Cloud-Betrieb.',
    start: '2026-07-21T09:00:00+02:00', end: null, is_online: false,
    venue_name: 'THWS', city: 'Schweinfurt', postal_code: '97421',
    organizer: 'THWS', tags: ['DevOps', 'Platform', 'Cloud'],
    url: 'https://example.org/e/4', price: 'ab 99 €', language: 'de',
  },
  {
    id: 5, title: 'Python Coding Night',
    description: 'Offener Hack-Abend rund um Python.',
    start: '2026-07-24T18:00:00+02:00', end: null, is_online: true,
    venue_name: null, city: null, postal_code: null,
    organizer: 'PyWürzburg', tags: ['Python', 'Coding'],
    url: 'https://example.org/e/5', price: 'Kostenlos', language: 'de',
  },
  {
    id: 6, title: 'Würzburg Go Hack Night',
    description: 'Go, Concurrency und kleine Tools bauen.',
    start: '2026-07-25T17:30:00+02:00', end: null, is_online: false,
    venue_name: 'TGZ Würzburg', city: 'Würzburg', postal_code: '97080',
    organizer: 'Gophers Mainfranken', tags: ['Go', 'Hackathon'],
    url: 'https://example.org/e/6', price: 'Kostenlos', language: 'de',
  },
]

function includes(hay, needle) {
  return (hay || '').toLowerCase().includes(needle.toLowerCase())
}

function applyDemoFilters(list, f) {
  return list.filter((e) => {
    if (f.q) {
      const hay = [e.title, e.description, (e.tags || []).join(' ')].join(' ')
      if (!includes(hay, f.q)) return false
    }
    if (f.city && !includes(e.city, f.city) && !includes(e.venue_name, f.city)) return false
    if (f.tag && !(e.tags || []).some((t) => includes(t, f.tag))) return false
    if (f.isOnline && !e.is_online) return false
    if (f.dateFrom && e.start && e.start.slice(0, 10) < f.dateFrom) return false
    if (f.dateTo && e.start && e.start.slice(0, 10) > f.dateTo) return false
    return true
  })
}

function buildQuery(f) {
  const p = new URLSearchParams()
  if (f.q) p.set('q', f.q)
  if (f.city) p.set('city', f.city)
  if (f.tag) p.set('tag', f.tag)
  if (f.dateFrom) p.set('date_from', f.dateFrom)
  if (f.dateTo) p.set('date_to', f.dateTo)
  if (f.isOnline) p.set('is_online', 'true')
  p.set('limit', '50')
  return p.toString()
}

export function useEventSearch() {
  const filters = reactive(emptyFilters())
  const events = ref([])
  const total = ref(0)
  const loading = ref(false)
  const error = ref(null)
  // True while running on demo data because the live endpoint was unreachable.
  const usingDemo = ref(false)

  async function search() {
    loading.value = true
    error.value = null
    try {
      const data = await api(`/api/events?${buildQuery(filters)}`)
      events.value = data.items ?? []
      total.value = data.total ?? events.value.length
      usingDemo.value = false
    } catch (e) {
      // GET /api/events (Agent-3) not available yet → graceful demo fallback.
      error.value = e
      const filtered = applyDemoFilters(DEMO_EVENTS, filters)
      events.value = filtered
      total.value = filtered.length
      usingDemo.value = true
    } finally {
      loading.value = false
    }
  }

  return { filters, events, total, loading, error, usingDemo, search }
}
