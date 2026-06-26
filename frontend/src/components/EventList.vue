<script setup>
// Result list for a set of events. Presentational: loading / empty / list states only — the
// caller owns the data + search. Reused by the public index and the dashboard.
import EventCard from './EventCard.vue'

const props = defineProps({
  events: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  total: { type: Number, default: 0 },
  // Bookmark wiring (logged-in dashboard). savedIds = event ids the user has saved.
  savable: { type: Boolean, default: false },
  savedIds: { type: Array, default: () => [] },
})

defineEmits(['toggle-save', 'require-login'])

function isSaved(id) {
  return props.savedIds.includes(id)
}
</script>

<template>
  <section class="list">
    <div class="bar">
      <span class="count">
        <template v-if="loading">Suche läuft…</template>
        <template v-else>{{ total }} {{ total === 1 ? 'Event' : 'Events' }}</template>
      </span>
    </div>

    <div v-if="loading && !events.length" class="state">Lade Events…</div>
    <div v-else-if="!events.length" class="state empty">
      Keine Events gefunden — Filter anpassen oder Suchbegriff ändern.
    </div>

    <EventCard
      v-for="ev in events"
      :key="ev.id"
      :event="ev"
      :savable="savable"
      :saved="isSaved(ev.id)"
      @toggle-save="$emit('toggle-save', $event)"
      @require-login="$emit('require-login')"
    />
  </section>
</template>

<style scoped>
.list { margin-top: 18px; }
.bar { display: flex; align-items: center; margin-bottom: 12px; }
.count { color: var(--muted); font-size: 13px; font-weight: 600; }
.state { background: var(--card); border: 1px dashed var(--line); border-radius: 14px; padding: 28px 18px; text-align: center; color: var(--muted); font-size: 14px; }
.state.empty { color: var(--faint); }
</style>
