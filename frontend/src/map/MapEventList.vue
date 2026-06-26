<script setup>
// Compact event side-list for the map. Presentational only: props down, events up. Located events
// (lat/lng) are clickable → the map flies to them; events without coordinates are listed but
// greyed/disabled (no marker to jump to). Own lightweight item rendering — does NOT use EventCard.
import { computed } from 'vue'
import { formatDateLabel, formatPlace } from '../lib/eventFormat'

const props = defineProps({
  events: { type: Array, default: () => [] },
  selectedId: { type: [Number, String, null], default: null },
  // Online / in-person filter (v-model:filter). The host owns the value so it can apply the same
  // filter to the map pins — this component only renders the toggle and emits changes.
  filter: { type: String, default: 'all' }, // 'all' | 'inperson' | 'online'
})
const emit = defineEmits(['select', 'hover', 'update:filter'])

const FILTERS = [
  { key: 'all', label: 'Alle' },
  { key: 'inperson', label: 'Vor Ort' },
  { key: 'online', label: 'Online' },
]

function hasCoords(e) {
  return typeof e.lat === 'number' && typeof e.lng === 'number'
}
const place = formatPlace
const locatedCount = computed(() => props.events.filter(hasCoords).length)

function onActivate(e) {
  if (hasCoords(e)) emit('select', e)
}
</script>

<template>
  <aside class="sidelist">
    <div class="lhead">
      <div class="lcount">
        <strong>{{ events.length }} Event{{ events.length === 1 ? '' : 's' }}</strong>
        <span class="sub">{{ locatedCount }} auf der Karte</span>
      </div>
      <div class="segmented" role="group" aria-label="Nach Ort filtern">
        <button
          v-for="opt in FILTERS" :key="opt.key"
          type="button"
          class="seg" :class="{ on: filter === opt.key }"
          @click="emit('update:filter', opt.key)"
        >{{ opt.label }}</button>
      </div>
    </div>

    <ul class="items">
      <li
        v-for="e in events" :key="e.id"
        class="item"
        :class="{ located: hasCoords(e), disabled: !hasCoords(e), active: e.id === selectedId }"
        :tabindex="hasCoords(e) ? 0 : -1"
        :title="hasCoords(e) ? 'Auf der Karte zeigen' : 'Kein Ort hinterlegt'"
        @click="onActivate(e)"
        @keyup.enter="onActivate(e)"
        @mouseenter="emit('hover', e)"
        @mouseleave="emit('hover', null)"
      >
        <div class="it-top">
          <span class="it-title">{{ e.title }}</span>
          <span v-if="e.is_online" class="badge online">Online</span>
          <span v-else-if="!hasCoords(e)" class="badge nogeo">kein Ort</span>
        </div>
        <div class="it-meta">
          <span>📅 {{ formatDateLabel(e.start) }}</span>
          <span class="it-place">📍 {{ place(e) }}</span>
        </div>
      </li>
    </ul>

    <p v-if="!events.length" class="empty">Keine Events.</p>
  </aside>
</template>

<style scoped>
.sidelist { display: flex; flex-direction: column; min-height: 0; height: 100%; }
.lhead { display: flex; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: wrap; padding: 0 2px 10px; border-bottom: 1px solid var(--line); }
.lcount { display: flex; align-items: baseline; gap: 8px; }
.lhead strong { font-size: 14px; }
.lhead .sub { color: var(--faint); font-size: 12px; }

/* Online / Vor Ort segmented toggle — same visual language as the calendar/header switches.
   Wraps onto its own row on narrow screens (flex-wrap on .lhead) so it stays tappable on mobile. */
.segmented { display: flex; gap: 3px; background: var(--chip); padding: 3px; border-radius: 9px; }
.seg { border: none; background: transparent; padding: 4px 11px; border-radius: 7px; font-size: 12px; font-weight: 700; cursor: pointer; color: var(--muted); font-family: inherit; }
.seg.on { background: var(--card); color: var(--ink); box-shadow: var(--shadow); }
.seg:hover:not(.on) { color: var(--ink); }

.items { list-style: none; margin: 0; padding: 8px 0 0; overflow-y: auto; flex: 1; display: flex; flex-direction: column; gap: 6px; }
.item { background: var(--card); border: 1px solid var(--line); border-radius: 9px; padding: 8px 10px; }
.item.located { cursor: pointer; }
.item.located:hover, .item.active { border-color: var(--accent); box-shadow: var(--shadow); }
.item.active { background: var(--accent-soft); }
.item.disabled { opacity: .55; }

.it-top { display: flex; align-items: center; gap: 6px; }
.it-title { font-size: 13px; font-weight: 700; line-height: 1.3; flex: 1; }
.badge { font-size: 10px; font-weight: 700; padding: 1px 6px; border-radius: 999px; white-space: nowrap; }
.badge.online { background: #e7f5ef; color: var(--good); }
.badge.nogeo { background: var(--chip); color: var(--faint); }

.it-meta { display: flex; flex-direction: column; gap: 1px; margin-top: 4px; font-size: 11.5px; color: var(--muted); }
.it-place { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.empty { color: var(--faint); font-size: 13px; text-align: center; margin-top: 16px; }
</style>
