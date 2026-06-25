<script setup>
// TEMP STUB — owned by Agent-2 until Agent-1's real EventList.vue lands.
// FIXED interface (build against this):
//   props: events: EventOut[], loading: bool, total: int
// Renders EventOut rows inline (canonical backend Event shape) so the stub stays
// self-contained and does not depend on Agent-1's EventCard.vue.
defineProps({
  events: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  total: { type: Number, default: 0 },
})

const DOW = ['So', 'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa']
const MON = ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez']

function parts(iso) {
  if (!iso) return { d: '–', m: '', dow: '', time: '' }
  const dt = new Date(iso)
  if (Number.isNaN(dt.getTime())) return { d: '–', m: '', dow: '', time: '' }
  const hh = String(dt.getHours()).padStart(2, '0')
  const mm = String(dt.getMinutes()).padStart(2, '0')
  return { d: dt.getDate(), m: MON[dt.getMonth()], dow: DOW[dt.getDay()], time: `${hh}:${mm}` }
}
function place(e) {
  return [e.venue_name, e.city].filter(Boolean).join(', ') || (e.is_online ? 'Online' : 'Ort offen')
}
</script>

<template>
  <div class="list">
    <div v-if="loading" class="state">Lädt Events…</div>
    <div v-else-if="!events.length" class="state">Keine Events für diese Filter.</div>

    <template v-else>
      <article v-for="e in events" :key="e.id ?? e.url ?? e.title" class="row">
        <div class="date">
          <div class="d">{{ parts(e.start).d }}</div>
          <div class="m">{{ parts(e.start).m }}</div>
          <div class="t">{{ parts(e.start).time }}</div>
        </div>
        <div class="body">
          <h3>{{ e.title }}</h3>
          <div class="meta">
            <span>📍 {{ place(e) }}</span>
            <span v-if="e.is_online" class="online">● Online</span>
            <span v-if="e.price">· {{ e.price }}</span>
            <span v-if="e.organizer" class="muted">· {{ e.organizer }}</span>
          </div>
          <div class="tags">
            <span v-for="t in (e.tags || [])" :key="t" class="tag">{{ t }}</span>
          </div>
          <div class="go">
            <a v-if="e.url" class="btn primary" :href="e.url" target="_blank" rel="noopener">Details</a>
            <button class="btn ghost" type="button">Merken</button>
          </div>
        </div>
      </article>
    </template>
  </div>
</template>

<style scoped>
.list { display: flex; flex-direction: column; gap: 12px; }
.state { color: var(--muted); font-size: 14px; padding: 22px; text-align: center; background: var(--card); border: 1px dashed var(--line); border-radius: 12px; }
.row { background: var(--card); border: 1px solid var(--line); border-radius: 14px; padding: 16px; box-shadow: var(--shadow); display: flex; gap: 16px; }
.row:hover { border-color: #d9d3c8; }
.date { flex: 0 0 54px; text-align: center; }
.date .d { font-size: 23px; font-weight: 800; line-height: 1; }
.date .m { font-size: 11px; font-weight: 700; color: var(--accent); text-transform: uppercase; letter-spacing: .5px; }
.date .t { font-size: 11px; color: var(--faint); margin-top: 3px; }
.body { flex: 1; min-width: 0; }
.body h3 { margin: 0 0 5px; font-size: 16px; letter-spacing: -.2px; }
.meta { display: flex; flex-wrap: wrap; gap: 5px 12px; color: var(--muted); font-size: 13px; align-items: center; }
.meta .online { color: var(--good); font-weight: 700; }
.meta .muted { color: var(--faint); }
.tags { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 10px; }
.tag { font-size: 11.5px; background: var(--chip); border-radius: 6px; padding: 3px 9px; color: #55606e; font-weight: 600; }
.go { margin-top: 12px; display: flex; gap: 9px; }
.go .btn { text-decoration: none; display: inline-block; }
</style>
