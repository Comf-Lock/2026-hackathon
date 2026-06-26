<script setup>
// Public calendar view (logged out + in). Shows events chronologically with a Week / Month / Year
// switch. Loads the *visible* range over GET /api/events using date_from/date_to (limit ≤ 100,
// paginated per period) — not just "next 20". Renders its own compact cells; it does NOT use
// EventCard (owned by Agent-3).
import { ref, computed, onMounted, watch } from 'vue'
import { useEvents } from '../composables/useEvents'
import {
  WEEKDAYS, weekGrid, monthGrid, yearGrid, rangeFor, periodLabel,
  bucketByDay, ymd, hhmm,
} from '../calendar/calendarRange'
import CalendarEventDetail from '../calendar/CalendarEventDetail.vue'

const MODES = [
  { key: 'week', label: 'Woche' },
  { key: 'month', label: 'Monat' },
  { key: 'year', label: 'Jahr' },
]

const mode = ref('month')
const cursor = ref(new Date(new Date().getFullYear(), new Date().getMonth(), new Date().getDate()))
const todayKey = ymd(new Date())

// Single data layer, in paginate mode so a whole period (incl. the year view) is loaded — paging
// at the API's 100-row cap so it isn't silently truncated.
const { filters, events, total, loading, error, load } = useEvents({ limit: 100, paginate: true })

// Point the shared filters at the visible period, then reload through the unified loader.
// Clear the explicit selection so the new period starts on its own default (next upcoming).
function reload() {
  const { from, to } = rangeFor(mode.value, cursor.value)
  filters.value = { ...filters.value, dateFrom: from, dateTo: to }
  selectedId.value = null
  return load()
}

// --- Detail column selection --------------------------------------------------------------
// Clicking an event in the grid fills the side column. With nothing clicked we default to the
// next upcoming event in the loaded period (falling back to the earliest) so the column is never
// empty when there are events to show.
const selectedId = ref(null)
const nowIso = new Date().toISOString()

function selectEvent(e) {
  selectedId.value = e.id
}

const byStart = (a, b) => (a.start < b.start ? -1 : a.start > b.start ? 1 : 0)
const defaultEvent = computed(() => {
  const list = events.value
  if (!list.length) return null
  const upcoming = list.filter((e) => (e.start || '') >= nowIso).sort(byStart)
  return upcoming[0] || [...list].sort(byStart)[0] || null
})
const selectedEvent = computed(() => {
  if (selectedId.value != null) {
    const hit = events.value.find((e) => e.id === selectedId.value)
    if (hit) return hit
  }
  return defaultEvent.value
})
// The column shows the auto-picked default when nothing is (still) explicitly selected.
const showingDefault = computed(
  () => selectedId.value == null || !events.value.some((e) => e.id === selectedId.value),
)

const buckets = computed(() => bucketByDay(events.value))
const weekCells = computed(() => weekGrid(cursor.value))
const monthCells = computed(() => monthGrid(cursor.value))
const yearMonths = computed(() => yearGrid(cursor.value))
const label = computed(() => periodLabel(mode.value, cursor.value))

function eventsOn(key) {
  return buckets.value[key] || []
}
function countOn(key) {
  return (buckets.value[key] || []).length
}
// Map a day's event count to a density class for the year heat cells.
function densityClass(key) {
  const n = countOn(key)
  if (!n) return ''
  if (n >= 4) return 'd3'
  if (n >= 2) return 'd2'
  return 'd1'
}

function step(dir) {
  const c = cursor.value
  if (mode.value === 'week') cursor.value = new Date(c.getFullYear(), c.getMonth(), c.getDate() + 7 * dir)
  else if (mode.value === 'month') cursor.value = new Date(c.getFullYear(), c.getMonth() + dir, 1)
  else cursor.value = new Date(c.getFullYear() + dir, c.getMonth(), 1)
}
function goToday() {
  const n = new Date()
  cursor.value = new Date(n.getFullYear(), n.getMonth(), n.getDate())
}
function jumpToMonth(anchor) {
  cursor.value = new Date(anchor.getFullYear(), anchor.getMonth(), 1)
  mode.value = 'month'
}

// Reload whenever the period or mode changes.
watch([mode, cursor], reload)
onMounted(reload)
</script>

<template>
  <div class="calwrap">
    <div class="toolbar">
      <h1 class="title">Kalender</h1>
      <div class="modes">
        <button
          v-for="m in MODES" :key="m.key"
          class="mode" :class="{ on: mode === m.key }"
          @click="mode = m.key"
        >{{ m.label }}</button>
      </div>
      <div class="nav">
        <button class="chip" aria-label="Zurück" @click="step(-1)">‹</button>
        <button class="chip today" @click="goToday">Heute</button>
        <button class="chip" aria-label="Weiter" @click="step(1)">›</button>
      </div>
      <span class="period">{{ label }}</span>
      <span class="count" v-if="!loading">{{ total }} Event{{ total === 1 ? '' : 's' }}</span>
      <span class="count" v-else>lädt…</span>
    </div>

    <p v-if="error" class="state err">Konnte Events nicht laden (API nicht erreichbar).</p>

    <!-- Two columns: the calendar grid (wide) + a narrow event-detail column. -->
    <div class="callayout">
      <div class="calmain">
        <!-- WEEK -->
        <section v-if="mode === 'week'" class="week">
          <div v-for="c in weekCells" :key="c.key" class="wcol" :class="{ today: c.key === todayKey }">
            <div class="whead">
              <span class="wdow">{{ WEEKDAYS[(c.date.getDay() + 6) % 7] }}</span>
              <span class="wnum">{{ c.date.getDate() }}</span>
            </div>
            <div class="wbody">
              <button
                v-for="e in eventsOn(c.key)" :key="e.id"
                type="button"
                class="wev" :class="{ online: e.is_online, sel: e.id === selectedEvent?.id }"
                :title="e.title"
                @click="selectEvent(e)"
              >
                <span class="t">{{ hhmm(e.start) || '–' }}</span>
                <span class="ti">{{ e.title }}</span>
              </button>
              <p v-if="!eventsOn(c.key).length" class="empty">—</p>
            </div>
          </div>
        </section>

        <!-- MONTH -->
        <section v-else-if="mode === 'month'" class="month">
          <div v-for="d in WEEKDAYS" :key="d" class="dow">{{ d }}</div>
          <div
            v-for="c in monthCells" :key="c.key"
            class="day" :class="{ out: !c.inMonth, today: c.key === todayKey }"
          >
            <div class="num">{{ c.date.getDate() }}</div>
            <button
              v-for="e in eventsOn(c.key)" :key="e.id"
              type="button"
              class="chip-ev" :class="{ online: e.is_online, sel: e.id === selectedEvent?.id }"
              :title="`${hhmm(e.start)} · ${e.title}`"
              @click="selectEvent(e)"
            >{{ hhmm(e.start) }} {{ e.title }}</button>
          </div>
        </section>

        <!-- YEAR -->
        <section v-else class="year">
          <div v-for="ym in yearMonths" :key="ym.month" class="mini">
            <button class="minihead" @click="jumpToMonth(ym.anchor)">{{ ym.name }}</button>
            <div class="minigrid">
              <div
                v-for="c in ym.cells" :key="c.key"
                class="cell" :class="[densityClass(c.key), { out: !c.inMonth, today: c.key === todayKey }]"
                :title="countOn(c.key) ? `${c.date.getDate()}.${ym.month + 1}. · ${countOn(c.key)} Event(s)` : ''"
                @click="countOn(c.key) ? jumpToMonth(ym.anchor) : null"
              >{{ c.inMonth ? c.date.getDate() : '' }}</div>
            </div>
          </div>
        </section>

        <p v-if="!loading && !error && total === 0" class="state">Keine Events in diesem Zeitraum.</p>
      </div>

      <CalendarEventDetail class="caldetail" :event="selectedEvent" :is-default="showingDefault" />
    </div>
  </div>
</template>

<style scoped>
.calwrap { max-width: 1240px; margin: 0 auto; padding: 22px 22px 60px; }

.toolbar { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; margin-bottom: 18px; }
.title { font-size: 20px; margin: 0 8px 0 0; letter-spacing: -.3px; }
.modes { display: flex; gap: 4px; background: var(--chip); padding: 3px; border-radius: 10px; }
.mode { border: none; background: transparent; padding: 6px 13px; border-radius: 8px; font-weight: 700; font-size: 13px; cursor: pointer; color: var(--muted); font-family: inherit; }
.mode.on { background: var(--card); color: var(--ink); box-shadow: var(--shadow); }
.nav { display: flex; gap: 5px; }
.chip { border: 1px solid var(--line); background: var(--card); border-radius: 8px; padding: 6px 11px; font-weight: 700; font-size: 13px; cursor: pointer; color: var(--ink); font-family: inherit; }
.chip.today { font-size: 12px; }
.period { font-weight: 800; font-size: 15px; letter-spacing: -.2px; }
.count { color: var(--faint); font-size: 12.5px; margin-left: auto; }

.state { color: var(--muted); text-align: center; margin-top: 30px; font-size: 14px; }
.state.err { color: var(--accent); }

/* Two-column layout: calendar grid + narrow sticky detail column. */
.callayout { display: grid; grid-template-columns: minmax(0, 1fr) 320px; gap: 20px; align-items: start; }
.calmain { min-width: 0; }
.caldetail { position: sticky; top: 16px; }
@media (max-width: 980px) {
  .callayout { grid-template-columns: 1fr; }
  .caldetail { position: static; }
}

/* WEEK */
.week { display: grid; grid-template-columns: repeat(7, 1fr); gap: 8px; }
.wcol { background: var(--bg); border: 1px solid var(--line); border-radius: 10px; min-height: 220px; display: flex; flex-direction: column; }
.wcol.today { border-color: var(--accent); }
.whead { display: flex; align-items: baseline; justify-content: space-between; padding: 8px 10px; border-bottom: 1px solid var(--line); }
.wdow { font-size: 11px; text-transform: uppercase; letter-spacing: .5px; color: var(--faint); font-weight: 700; }
.wnum { font-size: 14px; font-weight: 700; }
.wbody { padding: 7px; display: flex; flex-direction: column; gap: 5px; }
.wev { display: flex; flex-direction: column; gap: 1px; background: var(--card); border: 1px solid var(--line); border-left: 3px solid var(--accent); border-radius: 7px; padding: 5px 7px; text-decoration: none; cursor: pointer; font-family: inherit; text-align: left; width: 100%; }
.wev:hover { border-color: var(--accent); }
.wev.sel { background: var(--accent-soft); border-color: var(--accent); box-shadow: var(--shadow); }
.wev.online { border-left-color: var(--good); }
.wev .t { font-size: 11px; font-weight: 700; color: var(--accent); }
.wev.online .t { color: var(--good); }
.wev .ti { font-size: 12px; line-height: 1.3; color: var(--ink); }
.empty { color: var(--faint); text-align: center; font-size: 12px; margin: 6px 0; }

/* MONTH */
.month { display: grid; grid-template-columns: repeat(7, 1fr); gap: 7px; }
.month .dow { font-size: 11px; color: var(--faint); text-transform: uppercase; text-align: center; padding-bottom: 2px; font-weight: 700; }
.day { min-height: 96px; background: var(--bg); border: 1px solid var(--line); border-radius: 9px; padding: 6px; display: flex; flex-direction: column; gap: 3px; overflow: hidden; }
.day.out { opacity: .4; }
.day.today { border-color: var(--accent); background: var(--accent-soft); }
.day .num { font-size: 12px; color: var(--muted); font-weight: 700; }
.chip-ev { display: block; width: 100%; box-sizing: border-box; border: 1px solid transparent; font-family: inherit; text-align: left; cursor: pointer; font-size: 11px; line-height: 1.25; background: var(--accent-soft); color: var(--accent); border-radius: 5px; padding: 2px 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; text-decoration: none; font-weight: 600; }
.chip-ev:hover { border-color: var(--accent); }
.chip-ev.sel { border-color: var(--accent); box-shadow: inset 0 0 0 1px var(--accent); font-weight: 700; }
.chip-ev.online { background: #e7f5ef; color: var(--good); }

/* YEAR */
.year { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
.mini { background: var(--bg); border: 1px solid var(--line); border-radius: 10px; padding: 10px; }
.minihead { width: 100%; text-align: left; border: none; background: transparent; font-weight: 800; font-size: 13px; cursor: pointer; padding: 0 0 7px; color: var(--ink); font-family: inherit; }
.minigrid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 2px; }
.cell { aspect-ratio: 1; display: flex; align-items: center; justify-content: center; font-size: 9.5px; color: var(--faint); border-radius: 4px; }
.cell.out { color: transparent; }
.cell.d1 { background: var(--accent-soft); color: var(--accent); cursor: pointer; }
.cell.d2 { background: #f6c9d2; color: var(--accent); cursor: pointer; font-weight: 700; }
.cell.d3 { background: var(--accent); color: #fff; cursor: pointer; font-weight: 700; }
.cell.today { outline: 1.5px solid var(--accent); outline-offset: -1px; }

@media (max-width: 860px) {
  .year { grid-template-columns: repeat(2, 1fr); }
  .week { grid-template-columns: 1fr; }
}
</style>
