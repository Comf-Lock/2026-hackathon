<script setup>
// Renders one canonical event (the API contract's EventOut). Source-agnostic and presentational
// only — owned here, reused by the public index and (optionally) the dashboard. All fields except
// id/title/start are optional, so guard everything.
import { computed } from 'vue'

const props = defineProps({
  event: { type: Object, required: true },
})

const MONTHS = ['JAN', 'FEB', 'MÄR', 'APR', 'MAI', 'JUN', 'JUL', 'AUG', 'SEP', 'OKT', 'NOV', 'DEZ']

const when = computed(() => {
  const d = new Date(props.event.start)
  if (Number.isNaN(d.getTime())) return { day: '–', month: '', time: '' }
  return {
    day: d.getDate(),
    month: MONTHS[d.getMonth()],
    time: d.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' }),
  }
})

const place = computed(() => {
  const e = props.event
  if (e.is_online) return 'Online'
  return [e.venue_name, e.city].filter(Boolean).join(', ') || 'Ort offen'
})

const priceLabel = computed(() => props.event.price || '')
const tags = computed(() => props.event.tags || [])
</script>

<template>
  <article class="ev">
    <div class="date">
      <div class="d">{{ when.day }}</div>
      <div class="m">{{ when.month }}</div>
      <div v-if="when.time" class="t">{{ when.time }}</div>
    </div>

    <div class="body">
      <h3>
        <a v-if="event.url" :href="event.url" target="_blank" rel="noopener">{{ event.title }}</a>
        <template v-else>{{ event.title }}</template>
      </h3>

      <div class="row">
        <span :class="{ online: event.is_online }">{{ event.is_online ? '🌐' : '📍' }} {{ place }}</span>
        <span v-if="priceLabel">· 💰 {{ priceLabel }}</span>
        <span v-if="event.organizer" class="org">· {{ event.organizer }}</span>
      </div>

      <p v-if="event.description" class="desc">{{ event.description }}</p>

      <div v-if="tags.length" class="tagrow">
        <span v-for="t in tags" :key="t" class="tag">{{ t }}</span>
      </div>

      <div class="go">
        <a v-if="event.url" class="btn primary" :href="event.url" target="_blank" rel="noopener">Zum Event</a>
        <button class="btn ghost" type="button">Merken</button>
      </div>
    </div>
  </article>
</template>

<style scoped>
.ev { background: var(--card); border: 1px solid var(--line); border-radius: 16px; padding: 18px; margin-bottom: 14px; box-shadow: var(--shadow); display: flex; gap: 16px; transition: .15s; }
.ev:hover { transform: translateY(-1px); border-color: #d9d3c8; }
.date { flex: 0 0 56px; text-align: center; }
.date .d { font-size: 24px; font-weight: 800; line-height: 1; }
.date .m { font-size: 11px; font-weight: 700; color: var(--accent); text-transform: uppercase; letter-spacing: .5px; }
.date .t { font-size: 11px; color: var(--faint); margin-top: 3px; }
.body { flex: 1; min-width: 0; }
.body h3 { margin: 0 0 5px; font-size: 16.5px; letter-spacing: -.2px; }
.body h3 a { text-decoration: none; }
.body h3 a:hover { color: var(--accent); }
.row { display: flex; flex-wrap: wrap; gap: 4px 8px; color: var(--muted); font-size: 13px; align-items: center; }
.row .online { color: var(--good); font-weight: 600; }
.row .org { color: var(--faint); }
.desc { margin: 8px 0 0; font-size: 13px; color: var(--muted); line-height: 1.5; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.tagrow { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 11px; }
.tag { font-size: 11.5px; background: var(--chip); border-radius: 6px; padding: 3px 9px; color: #55606e; font-weight: 600; }
.go { margin-top: 13px; display: flex; gap: 9px; align-items: center; }
.go .btn { text-decoration: none; display: inline-flex; align-items: center; }
</style>
