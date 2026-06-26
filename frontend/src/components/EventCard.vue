<script setup>
// Renders one canonical event (the API contract's EventOut). Source-agnostic and presentational;
// owned here, reused identically by the public index and the dashboard. Layout adapts the
// Ground-News-style mockup (prototype/dashboard.html): tags + optional rating, a tag-weighting
// spectrum bar, and a source-reconciliation row with a visibility-tier badge. Colours use the app's
// existing Mainfranken palette variables. All fields except id/title/start are optional → guarded.
import { computed, ref } from 'vue'
import { cleanDescription, distinctSources, intentMix, visibilityTier, weightBar } from '../lib/eventDisplay'
import { formatDateLabel, formatPlace } from '../lib/eventFormat'

const props = defineProps({
  event: { type: Object, required: true },
  // Save ("Merken") state — driven by the parent (it owns the bookmark set).
  saved: { type: Boolean, default: false },
  // Whether saving is available (only when logged in). When false, the button asks for login.
  savable: { type: Boolean, default: false },
})

const emit = defineEmits(['toggle-save', 'require-login'])

const dateLabel = computed(() => formatDateLabel(props.event.start))
const place = computed(() => formatPlace(props.event))

// Cleaned, readable description (entities decoded, real line breaks, whitespace normalised).
const desc = computed(() => cleanDescription(props.event.description))
const expanded = ref(false)

// Collapsed-state clamp height (mirror of the CSS -webkit-line-clamp below) and the rough
// characters-per-line for the card's description column at 13px. Used to estimate how many lines
// the text wraps to without measuring the DOM.
const CLAMP_LINES = 3
const CHARS_PER_LINE = 58
// Only worth a toggle if more than ~2 lines would stay hidden behind the clamp. For 1–2 hidden
// lines we just show the full text and let the card grow a little — a toggle there is more
// friction than the saved space is worth.
const HIDDEN_LINE_THRESHOLD = 2

const estimatedLines = computed(() =>
  desc.value
    .split('\n')
    .reduce((sum, line) => sum + Math.max(1, Math.ceil(line.length / CHARS_PER_LINE)), 0),
)
// Toggle (and clamp) only when the text overflows the clamp by more than HIDDEN_LINE_THRESHOLD
// lines; otherwise the full text renders untruncated and no button shows.
const needsToggle = computed(() => estimatedLines.value > CLAMP_LINES + HIDDEN_LINE_THRESHOLD)

const tags = computed(() => props.event.tags || [])
// Real LLM topic weights only, or null when the event has not been scored (then no bar renders —
// "either rated or not shown"). The LLM always estimates, so no "geschätzt" marker — the bar stands
// on its own.
const bar = computed(() => weightBar(props.event))
// Real LLM intent distribution (deep-tech / recruiting / sales / networking); empty until scored.
const intents = computed(() => intentMix(props.event))
const sources = computed(() => distinctSources(props.event.sources))
// Visibility magnitude (replaces the old negative "blindspot" framing): more sources → higher tier.
const tier = computed(() => visibilityTier(sources.value.length))
const rating = computed(() => props.event.rating || null)
// Discreet popularity signal — a real attendee/RSVP count from the source platform (Luma
// guest_count / Meetup "going"). Only shown when a positive number is present.
const attendees = computed(() => {
  const n = props.event.attendee_count
  return typeof n === 'number' && n > 0 ? n : null
})

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
      <span
        v-if="attendees"
        class="people"
        :title="`Teilnehmer laut ${event.attendance_source || 'Quelle'}`"
      >👥 <b>~{{ attendees }}</b> Teilnehmer</span>
      <span v-if="event.organizer" class="org">· {{ event.organizer }}</span>
    </div>

    <template v-if="desc">
      <p class="desc" :class="{ clamp: needsToggle && !expanded }">{{ desc }}</p>
      <button v-if="needsToggle" class="more" type="button" @click="expanded = !expanded">
        {{ expanded ? 'Weniger anzeigen' : 'Mehr lesen' }}
      </button>
    </template>

    <!-- Topic weighting (Ground-News intent-bar analog). Only rendered for LLM-scored events with
         real topic_weights — an unscored event shows no bar at all (no placeholder, no fallback). -->
    <div v-if="bar" class="intent">
      <div class="ihead">
        <span class="t">Themen-Gewichtung</span>
      </div>
      <div class="bar">
        <i v-for="(w, i) in bar.segments" :key="i" :style="{ width: w.pct + '%', background: w.color }" :title="`${w.tag} · ${Math.round(w.pct)}%`" />
      </div>
      <div class="legend">
        <span v-for="w in bar.segments" :key="w.tag" class="seg" :style="{ '--seg': w.color }"><i :style="{ background: w.color }" />{{ w.tag }} <b>{{ Math.round(w.pct) }}%</b></span>
      </div>

      <!-- Intent mix: deep-tech vs recruiting vs sales vs networking (only when LLM-scored) -->
      <div v-if="intents.length" class="imix">
        <span v-for="w in intents" :key="w.tag" class="chip" :style="{ borderColor: w.color }">
          <i :style="{ background: w.color }" />{{ w.tag }} <b>{{ Math.round(w.pct) }}%</b>
        </span>
      </div>
    </div>

    <!-- Source reconciliation: how many independent sources list this event (visibility magnitude) -->
    <div v-if="sources.length" class="sources">
      <span class="lab">Sichtbarkeit · {{ sources.length }} Quellen</span>
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
      <span class="tier" :class="tier.key" :title="tier.tooltip">{{ tier.badge }}</span>
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
/* Discreet popularity signal — accent only on the count, stays inline with the other meta. */
.meta .people b { color: var(--accent); }

/* pre-line honours the real newlines cleanDescription() produces; collapsed state clamps to 3
   lines via the .clamp modifier, expanded shows the full text. */
.desc { margin: 0 0 6px; font-size: 13px; color: var(--muted); line-height: 1.5; white-space: pre-line; overflow-wrap: anywhere; }
.desc.clamp { display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.more { display: inline-block; margin: 0 0 12px; padding: 0; background: none; border: none; color: var(--accent); font-size: 12px; font-weight: 600; cursor: pointer; }
.more:hover { text-decoration: underline; }

.intent { margin: 14px 0 6px; }
.intent .ihead { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.intent .ihead .t { font-size: 11px; text-transform: uppercase; letter-spacing: .6px; color: var(--faint); }
.legend b { font-weight: 700; color: var(--ink, var(--txt)); }
.imix { display: flex; gap: 7px; margin-top: 9px; flex-wrap: wrap; }
.imix .chip { display: inline-flex; align-items: center; gap: 5px; font-size: 11px; color: var(--muted); background: var(--chip); border: 1px solid var(--line); border-left-width: 3px; border-radius: 6px; padding: 2px 8px; }
.imix .chip i { width: 7px; height: 7px; border-radius: 2px; display: inline-block; }
.imix .chip b { font-weight: 700; color: var(--ink, var(--txt)); }
.bar { display: flex; height: 9px; border-radius: 6px; overflow: hidden; background: var(--chip); }
.bar i { display: block; height: 100%; }
.legend { display: flex; gap: 7px; margin-top: 8px; flex-wrap: wrap; }
.legend span { display: inline-flex; align-items: center; gap: 5px; font-size: 11px; color: var(--muted); }
/* Pills carry their bar-segment colour (--seg, the same source the bar paints with) so the
   association segment↔pill is obvious: tinted fill + a clearly coloured border + the matching dot. */
.legend span.seg { color: var(--ink, var(--txt)); font-weight: 600; padding: 3px 9px; border-radius: 999px;
  background: color-mix(in srgb, var(--seg) 16%, transparent);
  border: 1px solid color-mix(in srgb, var(--seg) 55%, var(--line)); }
.legend i { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }

.sources { display: flex; align-items: center; gap: 10px; margin-top: 14px; padding-top: 14px; border-top: 1px solid var(--line); flex-wrap: wrap; }
.sources .lab { font-size: 11px; text-transform: uppercase; letter-spacing: .5px; color: var(--faint); }
.src { display: flex; align-items: center; gap: 6px; background: var(--chip); border: 1px solid var(--line); border-radius: 8px; padding: 4px 9px; font-size: 12px; color: inherit; text-decoration: none; }
.src:hover { border-color: #d9d3c8; }
.src .ic { width: 18px; height: 18px; border-radius: 5px; display: grid; place-items: center; font-weight: 700; font-size: 10px; color: #fff; }
/* Visibility tier — neutral/positive, grows more prominent with the tier (never a warning). */
.tier { margin-left: auto; display: flex; align-items: center; gap: 6px; font-size: 12px; font-weight: 700; border-radius: 8px; padding: 4px 10px; white-space: nowrap; }
.tier.exclusive { color: var(--accent); background: var(--accent-soft); border: 1px solid var(--accent); }
.tier.multi { color: var(--good, #1f9d76); background: rgba(31,157,118,.12); border: 1px solid rgba(31,157,118,.4); }
.tier.high { color: #fff; background: var(--good, #1f9d76); border: 1px solid var(--good, #1f9d76); }

.actions { display: flex; gap: 10px; margin-top: 16px; }
.btn { text-align: center; border-radius: 9px; padding: 9px 14px; font-weight: 600; cursor: pointer; font-size: 13px; border: 1px solid transparent; text-decoration: none; display: inline-flex; align-items: center; justify-content: center; }
.btn.ghost { background: var(--chip); border-color: var(--line); color: var(--ink, var(--txt)); }
.btn.save { background: var(--chip); border-color: var(--line); color: var(--ink, var(--txt)); margin-left: auto; }
.btn.save.on { background: var(--accent-soft); border-color: var(--accent); color: var(--accent); }

/* Phone: trim padding and let the two action buttons share the row evenly so they stay tappable.
   The source-tier badge drops its auto-margin so it wraps cleanly onto its own line when needed. */
@media (max-width: 480px) {
  .card { padding: 14px; border-radius: 14px; }
  .head h3 { font-size: 16px; }
  .actions { gap: 8px; }
  .actions .btn { flex: 1; padding: 10px 8px; }
  .btn.save { margin-left: 0; }
  .tier { margin-left: 0; }
}
</style>
