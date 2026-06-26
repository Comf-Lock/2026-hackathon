<script setup>
// One compact event row for the dashboard rail boxes ("Demnächst gespeichert" / "Exklusiv
// gelistet"). Extracted from DashboardView so the two byte-identical mini markups live in one
// place. Presentational only — owns its date pill formatting and styles.
import { computed } from 'vue'

const props = defineProps({
  event: { type: Object, required: true },
})

const MONTHS = ['JAN', 'FEB', 'MÄR', 'APR', 'MAI', 'JUN', 'JUL', 'AUG', 'SEP', 'OKT', 'NOV', 'DEZ']

const date = computed(() => {
  const d = new Date(props.event.start)
  if (Number.isNaN(d.getTime())) return { d: '–', m: '' }
  return { d: d.getDate(), m: MONTHS[d.getMonth()] }
})

const place = computed(() =>
  props.event.city || (props.event.is_online ? 'Online' : 'Ort offen'),
)
</script>

<template>
  <div class="mini">
    <div class="date"><div class="d">{{ date.d }}</div><div class="m">{{ date.m }}</div></div>
    <div class="info"><b>{{ event.title }}</b><span class="muted">{{ place }}</span></div>
  </div>
</template>

<style scoped>
.mini { display: flex; gap: 10px; align-items: center; margin-bottom: 12px; }
.mini:last-child { margin-bottom: 0; }
.mini .date { flex: 0 0 42px; text-align: center; background: var(--chip); border: 1px solid var(--line); border-radius: 8px; padding: 5px 0; }
.mini .date .d { font-size: 16px; font-weight: 800; line-height: 1; }
.mini .date .m { font-size: 10px; color: var(--muted); }
.mini .info { min-width: 0; }
.mini .info b { display: block; font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.mini .info .muted { font-size: 12px; color: var(--muted); }
</style>
