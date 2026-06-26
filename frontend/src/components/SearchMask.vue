<script setup>
// Reusable search form. v-model binds the filter object; 'search' fires on submit and, debounced
// (~300ms), as the user types — so both the public index and the dashboard get live + explicit
// search from one component. Keep this index-agnostic: no routing, no auth, no result rendering.
import { reactive, watch } from 'vue'

const props = defineProps({
  modelValue: { type: Object, required: true },
  // Radius search: when on, show the km input + "near me" button. The centre itself is resolved by
  // useEvents (profile home or geolocation) — this component only emits the controls.
  geo: { type: Boolean, default: false },
  locating: { type: Boolean, default: false }, // geolocation request in flight
  hasCenter: { type: Boolean, default: false }, // a centre is resolved → radius is actually applied
})
const emit = defineEmits(['update:modelValue', 'search', 'locate'])

// Local working copy; mirror back to the parent via update:modelValue. Re-sync if the parent
// replaces the bound object (e.g. a "reset filters" action).
const local = reactive({ ...props.modelValue })
watch(() => props.modelValue, (v) => Object.assign(local, v))

let timer
function onInput() {
  emit('update:modelValue', { ...local })
  clearTimeout(timer)
  timer = setTimeout(() => emit('search', { ...local }), 300)
}
function onSubmit() {
  clearTimeout(timer)
  emit('update:modelValue', { ...local })
  emit('search', { ...local })
}
function reset() {
  // Keep the radius value (a search preference, not a query term) so resetting doesn't silently
  // widen the geo scope.
  Object.assign(local, { q: '', city: '', tag: '', dateFrom: '', dateTo: '', isOnline: false })
  onSubmit()
}
</script>

<template>
  <form class="mask" @submit.prevent="onSubmit">
    <div class="primary">
      <label class="search">
        <span class="ic">🔎</span>
        <input
          v-model="local.q" type="search" placeholder="Suche: &quot;Vue&quot;, &quot;Kubernetes&quot;, &quot;KI&quot;…"
          @input="onInput"
        >
      </label>
      <button class="btn primary" type="submit">Suchen</button>
    </div>

    <div class="filters">
      <label class="f">
        <span>Ort</span>
        <input v-model="local.city" type="text" placeholder="z. B. Würzburg" @input="onInput">
      </label>
      <label class="f">
        <span>Tag/Thema</span>
        <input v-model="local.tag" type="text" placeholder="z. B. AI/ML" @input="onInput">
      </label>
      <label class="f">
        <span>Von</span>
        <input v-model="local.dateFrom" type="date" @change="onInput">
      </label>
      <label class="f">
        <span>Bis</span>
        <input v-model="local.dateTo" type="date" @change="onInput">
      </label>
      <label class="f check">
        <input v-model="local.isOnline" type="checkbox" @change="onInput">
        <span>Nur Online</span>
      </label>

      <!-- Radius (Luftlinie) — only when the host enables geo search -->
      <template v-if="geo">
        <label class="f radius">
          <span>Umkreis: {{ local.radiusKm }} km</span>
          <input
            v-model.number="local.radiusKm" type="range" min="5" max="100" step="5"
            @input="onInput"
          >
        </label>
        <button
          class="locate" type="button" :class="{ active: hasCenter }"
          :disabled="locating" @click="emit('locate')"
        >
          📍 {{ locating ? 'Ortung…' : (hasCenter ? 'In meiner Nähe' : 'Standort nutzen') }}
        </button>
      </template>

      <button class="reset" type="button" @click="reset">Zurücksetzen</button>
    </div>
  </form>
</template>

<style scoped>
.mask { background: var(--card); border: 1px solid var(--line); border-radius: 14px; padding: 14px; box-shadow: var(--shadow); }
.primary { display: flex; gap: 10px; }
.search { flex: 1; display: flex; align-items: center; gap: 8px; background: var(--bg); border: 1px solid var(--line); border-radius: 10px; padding: 9px 12px; }
.search .ic { color: var(--faint); }
.search input { flex: 1; background: none; border: none; outline: none; font-size: 14px; font-family: inherit; color: var(--ink); }
.primary .btn { padding: 9px 18px; font-size: 14px; }

.filters { display: flex; flex-wrap: wrap; align-items: flex-end; gap: 10px 14px; margin-top: 12px; }
.f { display: flex; flex-direction: column; gap: 4px; font-size: 12px; color: var(--muted); }
.f > span { font-weight: 600; letter-spacing: .2px; }
.f input[type="text"], .f input[type="date"] { background: var(--bg); border: 1px solid var(--line); border-radius: 8px; padding: 7px 10px; font-size: 13px; font-family: inherit; color: var(--ink); outline: none; min-width: 130px; }
.f input:focus { border-color: var(--accent); }
.f.check { flex-direction: row; align-items: center; gap: 7px; color: var(--ink); font-size: 13px; padding-bottom: 7px; }
.f.check input { width: 15px; height: 15px; accent-color: var(--accent); }
.f.radius { min-width: 160px; }
.f.radius input[type="range"] { accent-color: var(--accent); width: 100%; }
.locate { background: var(--bg); border: 1px solid var(--line); border-radius: 8px; color: var(--muted); font-size: 12.5px; font-family: inherit; cursor: pointer; padding: 7px 12px; align-self: flex-end; }
.locate:hover:not(:disabled) { border-color: var(--accent); color: var(--accent); }
.locate.active { border-color: var(--accent); color: var(--accent); font-weight: 600; }
.locate:disabled { opacity: .6; cursor: progress; }
.reset { margin-left: auto; background: none; border: none; color: var(--faint); font-size: 12.5px; font-family: inherit; cursor: pointer; padding: 7px 4px; }
.reset:hover { color: var(--accent); }
@media (max-width: 560px) { .reset { margin-left: 0; } }

/* Phone: stack everything full-width so nothing is cramped or clipped. The search button drops
   under the input; each filter field, the radius slider and the locate button span the full row. */
@media (max-width: 640px) {
  .primary { flex-wrap: wrap; }
  .primary .btn { width: 100%; }
  .filters { gap: 12px; }
  .f { width: 100%; }
  .f.check { width: auto; padding-bottom: 0; }
  .f input[type="text"], .f input[type="date"] { min-width: 0; width: 100%; }
  .f.radius { min-width: 0; width: 100%; }
  .locate { width: 100%; align-self: stretch; text-align: center; }
  .reset { width: 100%; text-align: center; padding: 9px 4px; }
}
</style>
