<script setup>
// Compact event detail for the calendar's narrow side column. Shows the SAME information as the
// search / list items (title, date, place, tags, description excerpt, topic weighting, source
// visibility, link) but stacked vertically and tuned for a narrow column. Presentational only —
// event in, external link out. Reuses the shared eventDisplay helpers and does NOT touch
// EventCard.vue / eventDisplay.js internals (owned by Agent-3) — it only consumes the pure helpers.
import { computed, ref, watch } from 'vue'
import { formatDateLabel } from './calendarRange'
import { cleanDescription, distinctSources, intentMix, visibilityTier, weightBar } from '../lib/eventDisplay'

const props = defineProps({
  event: { type: Object, default: null },
  // True when the shown event is the auto-picked "next upcoming" default (not an explicit click).
  isDefault: { type: Boolean, default: false },
})

const place = computed(() => {
  const e = props.event
  if (!e) return ''
  if (e.is_online) return 'Online'
  return [e.venue_name, e.city].filter(Boolean).join(', ') || 'Ort offen'
})
const tags = computed(() => props.event?.tags || [])
const desc = computed(() => cleanDescription(props.event?.description))
const bar = computed(() => (props.event ? weightBar(props.event) : null))
const intents = computed(() => (props.event ? intentMix(props.event) : []))
const sources = computed(() => distinctSources(props.event?.sources))
const tier = computed(() => visibilityTier(sources.value.length))
const rating = computed(() => props.event?.rating || null)

// Collapsed description with a toggle, mirroring the card but with a tighter threshold for the
// narrow column. Reset to collapsed whenever the shown event changes.
const expanded = ref(false)
const needsToggle = computed(() => desc.value.length > 160 || (desc.value.match(/\n/g) || []).length >= 2)
watch(() => props.event?.id, () => { expanded.value = false })
</script>

<template>
  <aside class="detail">
    <!-- Default / empty state: nothing selected and no upcoming event to fall back to. -->
    <div v-if="!event" class="placeholder">
      <div class="pic">🗓</div>
      <p>Wähle ein Event im Kalender, um hier die Details zu sehen.</p>
    </div>

    <div v-else class="card">
      <span v-if="isDefault" class="lead">Nächstes Event</span>

      <div class="top">
        <h3 class="title">
          <a v-if="event.url" :href="event.url" target="_blank" rel="noopener">{{ event.title }}</a>
          <template v-else>{{ event.title }}</template>
        </h3>
        <div v-if="rating" class="rating">
          <span class="star">★</span>{{ rating.toFixed ? rating.toFixed(1) : rating }}
          <span v-if="event.reviews" class="muted">({{ event.reviews }})</span>
        </div>
      </div>

      <div class="meta">
        <span>📅 <b>{{ formatDateLabel(event.start) }}</b></span>
        <span :class="{ online: event.is_online }">{{ event.is_online ? '🌐' : '📍' }} <b>{{ place }}</b></span>
        <span v-if="event.price">💰 <b>{{ event.price }}</b></span>
        <span v-if="event.organizer" class="org">· {{ event.organizer }}</span>
      </div>

      <div v-if="tags.length" class="tags">
        <span v-for="t in tags" :key="t" class="tag">{{ t }}</span>
      </div>

      <template v-if="desc">
        <p class="desc" :class="{ clamp: needsToggle && !expanded }">{{ desc }}</p>
        <button v-if="needsToggle" class="more" type="button" @click="expanded = !expanded">
          {{ expanded ? 'Weniger anzeigen' : 'Mehr lesen' }}
        </button>
      </template>

      <!-- Topic weighting — only for LLM-scored events with real topic_weights (no placeholder). -->
      <div v-if="bar" class="intent">
        <span class="ihead">Themen-Gewichtung<span v-if="bar.estimated" class="est"> · geschätzt</span></span>
        <div class="wbar">
          <i v-for="(w, i) in bar.segments" :key="i" :style="{ width: w.pct + '%', background: w.color }" :title="`${w.tag} · ${Math.round(w.pct)}%`" />
        </div>
        <div class="legend">
          <span v-for="w in bar.segments" :key="w.tag"><i :style="{ background: w.color }" />{{ w.tag }} <b>{{ Math.round(w.pct) }}%</b></span>
        </div>
        <div v-if="intents.length" class="imix">
          <span v-for="w in intents" :key="w.tag" class="ichip" :style="{ borderLeftColor: w.color }">{{ w.tag }} <b>{{ Math.round(w.pct) }}%</b></span>
        </div>
      </div>

      <!-- Source reconciliation: how many independent sources list this event (visibility). -->
      <div v-if="sources.length" class="sources">
        <span class="lab">Sichtbarkeit · {{ sources.length }} Quellen</span>
        <div class="srcs">
          <a v-for="s in sources" :key="s.label" class="src" :href="s.url" target="_blank" rel="noopener">
            <span class="sic" :style="{ background: s.color }">{{ s.letter }}</span>{{ s.label }}
          </a>
        </div>
        <span class="tier" :class="tier.key" :title="tier.tooltip">{{ tier.badge }}</span>
      </div>

      <a v-if="event.url" class="btn" :href="event.url" target="_blank" rel="noopener">Zum Event ↗</a>
    </div>
  </aside>
</template>

<style scoped>
.detail { background: var(--card); border: 1px solid var(--line); border-radius: 14px; padding: 16px; box-shadow: var(--shadow); }
.muted { color: var(--muted); font-weight: 400; }

/* Empty / default state */
.placeholder { text-align: center; color: var(--faint); padding: 26px 8px; }
.placeholder .pic { font-size: 30px; margin-bottom: 8px; }
.placeholder p { font-size: 13px; margin: 0; line-height: 1.5; }

.lead { display: inline-block; font-size: 10px; font-weight: 800; text-transform: uppercase; letter-spacing: .6px; color: var(--accent); background: var(--accent-soft); border-radius: 6px; padding: 2px 8px; margin-bottom: 10px; }

.top { display: flex; align-items: flex-start; justify-content: space-between; gap: 10px; }
.title { margin: 0; font-size: 16px; font-weight: 700; letter-spacing: -.2px; line-height: 1.3; min-width: 0; }
.title a { text-decoration: none; color: inherit; }
.title a:hover { color: var(--accent); }
.rating { display: flex; align-items: center; gap: 4px; background: var(--chip); border: 1px solid var(--line); border-radius: 8px; padding: 3px 8px; font-weight: 700; font-size: 12px; white-space: nowrap; }
.rating .star { color: #d98a2b; }

.meta { display: flex; flex-direction: column; gap: 4px; margin: 12px 0; color: var(--muted); font-size: 12.5px; }
.meta b { color: var(--ink, var(--txt)); font-weight: 600; }
.meta .online b { color: var(--good, #1f9d76); }
.meta .org { color: var(--faint); }

.tags { display: flex; gap: 5px; flex-wrap: wrap; margin-bottom: 12px; }
.tag { font-size: 11px; background: var(--chip); border: 1px solid var(--line); border-radius: 6px; padding: 2px 8px; color: var(--muted); }

.desc { margin: 0 0 6px; font-size: 12.5px; color: var(--muted); line-height: 1.5; white-space: pre-line; overflow-wrap: anywhere; }
.desc.clamp { display: -webkit-box; -webkit-line-clamp: 4; -webkit-box-orient: vertical; overflow: hidden; }
.more { display: inline-block; margin: 0 0 10px; padding: 0; background: none; border: none; color: var(--accent); font-size: 12px; font-weight: 600; cursor: pointer; font-family: inherit; }
.more:hover { text-decoration: underline; }

.intent { margin: 12px 0; }
.intent .ihead { display: block; font-size: 10.5px; text-transform: uppercase; letter-spacing: .5px; color: var(--faint); margin-bottom: 6px; }
.intent .ihead .est { color: #9a6212; }
.wbar { display: flex; height: 8px; border-radius: 5px; overflow: hidden; background: var(--chip); }
.wbar i { display: block; height: 100%; }
.legend { display: flex; gap: 6px; margin-top: 7px; flex-wrap: wrap; }
.legend span { display: inline-flex; align-items: center; gap: 4px; font-size: 11px; color: var(--muted); }
.legend i { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.legend b { font-weight: 700; color: var(--ink, var(--txt)); }
.imix { display: flex; gap: 6px; margin-top: 9px; flex-wrap: wrap; }
.ichip { font-size: 11px; color: var(--muted); background: var(--chip); border: 1px solid var(--line); border-left-width: 3px; border-radius: 6px; padding: 2px 8px; }
.ichip b { font-weight: 700; color: var(--ink, var(--txt)); }

.sources { margin: 12px 0; padding-top: 12px; border-top: 1px solid var(--line); }
.sources .lab { display: block; font-size: 10.5px; text-transform: uppercase; letter-spacing: .5px; color: var(--faint); margin-bottom: 7px; }
.srcs { display: flex; flex-wrap: wrap; gap: 6px; }
.src { display: inline-flex; align-items: center; gap: 5px; background: var(--chip); border: 1px solid var(--line); border-radius: 8px; padding: 3px 8px; font-size: 11.5px; color: inherit; text-decoration: none; }
.src:hover { border-color: #d9d3c8; }
.src .sic { width: 16px; height: 16px; border-radius: 5px; display: grid; place-items: center; font-weight: 700; font-size: 9px; color: #fff; }
.tier { display: inline-flex; align-items: center; gap: 6px; font-size: 11.5px; font-weight: 700; border-radius: 8px; padding: 4px 9px; margin-top: 9px; white-space: nowrap; }
.tier.exclusive { color: var(--accent); background: var(--accent-soft); border: 1px solid var(--accent); }
.tier.multi { color: var(--good, #1f9d76); background: rgba(31,157,118,.12); border: 1px solid rgba(31,157,118,.4); }
.tier.high { color: #fff; background: var(--good, #1f9d76); border: 1px solid var(--good, #1f9d76); }

.btn { display: block; text-align: center; margin-top: 14px; border-radius: 9px; padding: 9px 14px; font-weight: 600; font-size: 13px; text-decoration: none; background: var(--accent-soft); border: 1px solid var(--accent); color: var(--accent); }
.btn:hover { background: var(--accent); color: #fff; }
</style>
