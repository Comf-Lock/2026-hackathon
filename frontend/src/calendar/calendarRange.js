// Pure date helpers for the calendar view — no Vue, no API. Kept separate so the range/grid
// math is trivially testable and the view stays about rendering.
//
// Event grouping is string-based: an ISO start like "2026-07-18T19:00:00+02:00" is bucketed by
// its first 10 chars (the Europe/Berlin calendar day) and shown at chars 11–16 (HH:MM). This
// matches how useEventSearch compares date_from/date_to and sidesteps timezone-shift bugs that
// `new Date(iso)` grouping would introduce in other browser timezones.

export const WEEKDAYS = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So']
export const MONTHS = [
  'Januar', 'Februar', 'März', 'April', 'Mai', 'Juni',
  'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember',
]
export const MONTHS_SHORT = [
  'Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez',
]

// --- formatting -----------------------------------------------------------------------------
// Local Y-M-D string (date constructed at local midnight, so local getters are correct).
export function ymd(d) {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

export const dayKey = (iso) => (iso || '').slice(0, 10)
export const hhmm = (iso) => (iso || '').slice(11, 16)

// "14. Jul 2026, 18:30" — TZ-safe (string-slice, no `new Date`) human label, shared by the map
// popup and the map side-list so the two never drift.
export function formatDateLabel(iso) {
  const d = dayKey(iso)
  if (!d) return 'Termin offen'
  const [y, m, day] = d.split('-')
  const t = hhmm(iso)
  return `${Number(day)}. ${MONTHS_SHORT[Number(m) - 1]} ${y}${t ? `, ${t}` : ''}`
}

// --- arithmetic -----------------------------------------------------------------------------
export function addDays(d, n) {
  const r = new Date(d)
  r.setDate(r.getDate() + n)
  return r
}
export function addMonths(d, n) {
  const r = new Date(d.getFullYear(), d.getMonth() + n, 1)
  return r
}
export function addYears(d, n) {
  return new Date(d.getFullYear() + n, d.getMonth(), 1)
}

// Monday as first day of week. JS getDay(): Sun=0..Sat=6 → shift so Mon=0.
export function startOfWeek(d) {
  const r = new Date(d.getFullYear(), d.getMonth(), d.getDate())
  const dow = (r.getDay() + 6) % 7
  return addDays(r, -dow)
}

// --- grids ----------------------------------------------------------------------------------
// 7 cells, Monday→Sunday, for the week containing `cursor`.
export function weekGrid(cursor) {
  const start = startOfWeek(cursor)
  return Array.from({ length: 7 }, (_, i) => {
    const date = addDays(start, i)
    return { date, key: ymd(date), inMonth: date.getMonth() === cursor.getMonth() }
  })
}

// 42 cells (6 weeks), Monday-start, including leading/trailing spillover days so the grid is full.
export function monthGrid(cursor) {
  const first = new Date(cursor.getFullYear(), cursor.getMonth(), 1)
  const gridStart = startOfWeek(first)
  return Array.from({ length: 42 }, (_, i) => {
    const date = addDays(gridStart, i)
    return { date, key: ymd(date), inMonth: date.getMonth() === cursor.getMonth() }
  })
}

// 12 mini-months for the year of `cursor`. Each mini-month is its own 42-cell grid.
export function yearGrid(cursor) {
  return Array.from({ length: 12 }, (_, m) => {
    const anchor = new Date(cursor.getFullYear(), m, 1)
    return { month: m, name: MONTHS_SHORT[m], anchor, cells: monthGrid(anchor) }
  })
}

// --- fetch range ----------------------------------------------------------------------------
// The [from, to] (inclusive, YYYY-MM-DD) the API should load for the given mode/cursor. For
// week/month we extend to the full visible grid so spillover days also show their events.
export function rangeFor(mode, cursor) {
  if (mode === 'week') {
    const cells = weekGrid(cursor)
    return { from: cells[0].key, to: cells[cells.length - 1].key }
  }
  if (mode === 'year') {
    return { from: `${cursor.getFullYear()}-01-01`, to: `${cursor.getFullYear()}-12-31` }
  }
  // month
  const cells = monthGrid(cursor)
  return { from: cells[0].key, to: cells[cells.length - 1].key }
}

// Human label for the current cursor/mode (header title).
export function periodLabel(mode, cursor) {
  if (mode === 'year') return String(cursor.getFullYear())
  if (mode === 'month') return `${MONTHS[cursor.getMonth()]} ${cursor.getFullYear()}`
  const cells = weekGrid(cursor)
  const a = cells[0].date
  const b = cells[6].date
  const left = `${a.getDate()}. ${MONTHS_SHORT[a.getMonth()]}`
  const right = `${b.getDate()}. ${MONTHS_SHORT[b.getMonth()]} ${b.getFullYear()}`
  return `${left} – ${right}`
}

// Group events (EventOut-shaped, with .start) by their day key → { 'YYYY-MM-DD': [events…] },
// each day's list sorted chronologically by start time.
export function bucketByDay(events) {
  const map = {}
  for (const e of events || []) {
    const k = dayKey(e.start)
    if (!k) continue
    ;(map[k] ||= []).push(e)
  }
  for (const k of Object.keys(map)) map[k].sort((a, b) => (a.start < b.start ? -1 : a.start > b.start ? 1 : 0))
  return map
}
