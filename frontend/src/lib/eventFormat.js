// The single TZ-safe display-formatting module for events: date / time / month / place.
//
// All date formatting is STRING-BASED, never `new Date(iso)`. An ISO start like
// "2026-07-18T19:00:00+02:00" already encodes its Europe/Berlin wall-clock time; we read the day
// from chars 0–10 and the time from chars 11–16. `new Date(iso)` would re-interpret that instant in
// the *browser's* timezone and shift the day/time for anyone not on Berlin time — the bug this
// module exists to prevent. (This is the same approach the calendar grid math in
// calendar/calendarRange.js relies on; that file now imports its month names from here so there is
// one source of truth instead of three copies.)

export const WEEKDAYS = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So']
export const MONTHS = [
  'Januar', 'Februar', 'März', 'April', 'Mai', 'Juni',
  'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember',
]
export const MONTHS_SHORT = [
  'Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez',
]

// --- raw slices -----------------------------------------------------------------------------
export const dayKey = (iso) => (iso || '').slice(0, 10) // "YYYY-MM-DD"
export const hhmm = (iso) => (iso || '').slice(11, 16) // "HH:MM"

// Local Y-M-D string from a Date built at local midnight (so local getters are correct). Used by
// the calendar grid to key cells; lives here with the other date helpers.
export function ymd(d) {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

// --- formatted labels -----------------------------------------------------------------------
// "14. Jul 2026, 18:30" — the long human label used on the event card, the calendar detail, the
// map side-list and the map popup. TZ-safe (string slices only).
export function formatDateLabel(iso) {
  const d = dayKey(iso)
  if (!d) return 'Termin offen'
  const [y, m, day] = d.split('-')
  const t = hhmm(iso)
  return `${Number(day)}. ${MONTHS_SHORT[Number(m) - 1]} ${y}${t ? `, ${t}` : ''}`
}

// The compact date pill ({ day, month }) for the dashboard mini rows — e.g. { day: 14, month: 'JUL' }.
// month is the uppercase short name. TZ-safe.
export function formatDayPill(iso) {
  const d = dayKey(iso)
  if (!d) return { day: '–', month: '' }
  const [, m, day] = d.split('-')
  return { day: Number(day), month: (MONTHS_SHORT[Number(m) - 1] || '').toUpperCase() }
}

// --- place ----------------------------------------------------------------------------------
// Canonical place label: online events read "Online", otherwise venue + city, else "Ort offen".
// Shared by the card, the calendar detail and the map side-list so the wording never drifts.
export function formatPlace(event) {
  if (!event) return ''
  if (event.is_online) return 'Online'
  return [event.venue_name, event.city].filter(Boolean).join(', ') || 'Ort offen'
}

// Compact place for the dashboard mini rows: just the city (or the online/empty fallback).
export function formatPlaceShort(event) {
  if (!event) return ''
  return event.city || (event.is_online ? 'Online' : 'Ort offen')
}

// Raw "venue, city" with no fallback — for callers that show the place only when present
// (e.g. the map popup, which omits the line entirely when empty).
export function venueCity(event) {
  if (!event) return ''
  return [event.venue_name, event.city].filter(Boolean).join(', ')
}
