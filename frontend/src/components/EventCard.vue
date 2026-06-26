<script setup>
// Renders one canonical event (the API contract's EventOut). Source-agnostic and presentational;
// owned here, reused identically by the public index and the dashboard. Layout adapts the
// Ground-News-style mockup (prototype/dashboard.html): tags + optional rating, a tag-weighting
// spectrum bar, and a source-reconciliation row with a blindspot badge. Colours use the app's
// existing Mainfranken palette variables. All fields except id/title/start are optional → guarded.
import { computed } from 'vue'
import { distinctSources, tagWeights } from '../lib/eventDisplay'

const props = defineProps({
  event: { type: Object, required: true },
  // Save ("Merken") state — driven by the parent (it owns the bookmark set).
  saved: { type: Boolean, default: false },
  // Whether saving is available (only when logged in). When false, the button asks for login.
  savable: { type: Boolean, default: false },
})

const emit = defineEmits(['toggle-save', 'require-login'])

const MONTHS = ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez']

const dateLabel = computed(() => {
  const d = new Date(props.event.start)
  if (Number.isNaN(d.getTime())) return 'Termin offen'
  const time = d.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })
  return `${d.getDate()}. ${MONTHS[d.getMonth()]} ${d.getFullYear()}, ${time}`
})

const place = computed(() => {
  const e = props.event
  if (e.is_online) return 'Online'
  return [e.venue_name, e.city].filter(Boolean).join(', ') || 'Ort offen'
})

const tags = computed(() => props.event.tags || [])
const weights = computed(() => tagWeights(props.event.tags))
const sources = computed(() => distinctSources(props.event.sources))
const isBlindspot = computed(() => sources.value.length === 1)
const rating = computed(() => props.event.rating || null)

function onSave() {
  if (!props.savable) {
    emit('require-login')
    return
  }
  emit('toggle-save', props.event.id)
}
</script>

<template>
  <article class="card">
    <div class="top">
      <div class="head">
        <h3>
          <a v-if="event.url" :href="event.url" target="_blank" rel="noopener">{{ event.title }}</a>
          <template v-else>{{ event.title }}</template>
        </h3>
        <div v-if="tags.length" class="tags">
          <span v-for="t in tags" :key="t" class="tag">{{ t }}</span>
        </div>
      </div>
      <div v-if="rating" class="rating">
        <span class="star">★</span>{{ rating.toFixed ? rating.toFixed(1) : rating }}
        <span v-if="event.reviews" class="muted">({{ event.reviews }})</span>
      </div>
    </div>

    <div class="meta">
      <span>📅 <b>{{ dateLabel }}</b></span>
      <span :class="{ online: event.is_online }">{{ event.is_online ? '🌐' : '📍' }} <b>{{ place }}</b></span>
      <span v-if="event.price">💰 <b>{{ event.price }}</b></span>
      <span v-if="event.organizer" class="org">· {{ event.organizer }}</span>
    </div>

    <p v-if="event.description" class="desc">{{ event.description }}</p>

    <!-- Tag-weighting spectrum (Ground-News intent-bar analog; equal split per tag, LLM-weighted later) -->
    <div v-if="weights.length > 1" class="intent">
      <div class="ihead"><span class="t">Themen-Gewichtung</span></div>
      <div class="bar">
        <i v-for="w in weights" :key="w.tag" :style="{ width: w.pct + '%', background: w.color }" :title="w.tag" />
      </div>
      <div class="legend">
        <span v-for="w in weights" :key="w.tag"><i :style="{ background: w.color }" />{{ w.tag }}</span>
      </div>
    </div>

    <!-- Source reconciliation: where this event was found during scraping -->
    <div v-if="sources.length" class="sources">
      <span class="lab">Quellen-Abgleich ({{ sources.length }})</span>
      <a
        v-for="s in sources"
        :key="s.label"
        class="src"
        :href="s.url"
        target="_blank"
        rel="noopener"
      >
        <span class="ic" :style="{ background: s.color }">{{ s.letter }}</span>{{ s.label }}
      </a>
      <span v-if="isBlindspot" class="blindspot">⚡ Blindspot · nur 1 Quelle</span>
    </div>

    <div class="actions">
      <a v-if="event.url" class="btn ghost" :href="event.url" target="_blank" rel="noopener">Zum Event</a>
      <button class="btn save" :class="{ on: saved }" type="button" @click="onSave">
        {{ saved ? '✓ Gemerkt' : '+ Merken' }}
      </button>
    </div>
  </article>
</template>

<style scoped>
.card { background: var(--card); border: 1px solid var(--line); border-radius: 16px; padding: 18px; margin-bottom: 16px; box-shadow: var(--shadow); transition: .15s; position: relative; overflow: hidden; }
.card:hover { transform: translateY(-1px); border-color: #d9d3c8; box-shadow: 0 2px 4px rgba(20,24,31,.05), 0 14px 34px rgba(20,24,31,.10); }
.muted { color: var(--muted); font-weight: 400; }

.top { display: flex; justify-content: space-between; gap: 14px; align-items: flex-start; }
.head { min-width: 0; }
.head h3 { margin: 0 0 3px; font-size: 17px; font-weight: 700; letter-spacing: -.2px; }
.head h3 a { text-decoration: none; color: inherit; }
.head h3 a:hover { color: var(--accent); }
.tags { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 7px; }
.tag { font-size: 11px; background: var(--chip); border: 1px solid var(--line); border-radius: 6px; padding: 2px 8px; color: var(--muted); }

.rating { display: flex; align-items: center; gap: 5px; background: var(--chip); border: 1px solid var(--line); border-radius: 8px; padding: 5px 10px; font-weight: 700; white-space: nowrap; }
.rating .star { color: #d98a2b; }

.meta { display: flex; flex-wrap: wrap; gap: 8px 16px; margin: 14px 0; color: var(--muted); font-size: 13px; align-items: center; }
.meta b { color: var(--ink, var(--txt)); font-weight: 600; }
.meta .online b { color: var(--good, #1f9d76); }
.meta .org { color: var(--faint); }

.desc { margin: 0 0 12px; font-size: 13px; color: var(--muted); line-height: 1.5; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }

.intent { margin: 14px 0 6px; }
.intent .ihead { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.intent .ihead .t { font-size: 11px; text-transform: uppercase; letter-spacing: .6px; color: var(--faint); }
.bar { display: flex; height: 9px; border-radius: 6px; overflow: hidden; background: var(--chip); }
.bar i { display: block; height: 100%; }
.legend { display: flex; gap: 14px; margin-top: 7px; flex-wrap: wrap; }
.legend span { display: flex; align-items: center; gap: 5px; font-size: 11px; color: var(--muted); }
.legend i { width: 8px; height: 8px; border-radius: 2px; display: inline-block; }

.sources { display: flex; align-items: center; gap: 10px; margin-top: 14px; padding-top: 14px; border-top: 1px solid var(--line); flex-wrap: wrap; }
.sources .lab { font-size: 11px; text-transform: uppercase; letter-spacing: .5px; color: var(--faint); }
.src { display: flex; align-items: center; gap: 6px; background: var(--chip); border: 1px solid var(--line); border-radius: 8px; padding: 4px 9px; font-size: 12px; color: inherit; text-decoration: none; }
.src:hover { border-color: #d9d3c8; }
.src .ic { width: 18px; height: 18px; border-radius: 5px; display: grid; place-items: center; font-weight: 700; font-size: 10px; color: #fff; }
.blindspot { margin-left: auto; display: flex; align-items: center; gap: 6px; font-size: 12px; font-weight: 700; color: #9a6212; background: rgba(217,138,43,.14); border: 1px solid rgba(217,138,43,.4); border-radius: 8px; padding: 4px 10px; }

.actions { display: flex; gap: 10px; margin-top: 16px; }
.btn { text-align: center; border-radius: 9px; padding: 9px 14px; font-weight: 600; cursor: pointer; font-size: 13px; border: 1px solid transparent; text-decoration: none; display: inline-flex; align-items: center; justify-content: center; }
.btn.ghost { background: var(--chip); border-color: var(--line); color: var(--ink, var(--txt)); }
.btn.save { background: var(--chip); border-color: var(--line); color: var(--ink, var(--txt)); margin-left: auto; }
.btn.save.on { background: var(--accent-soft); border-color: var(--accent); color: var(--accent); }
</style>
