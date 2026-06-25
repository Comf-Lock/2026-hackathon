<script setup>
// TEMP STUB — owned by Agent-2 until Agent-1's real SearchMask.vue lands.
// FIXED interface (build against this):
//   props:  modelValue: { q, city, tag, dateFrom, dateTo, isOnline }   (v-model)
//   emits:  'update:modelValue'(filters),  'search'(filters)
import { reactive, watch } from 'vue'

const props = defineProps({
  modelValue: { type: Object, required: true },
})
const emit = defineEmits(['update:modelValue', 'search'])

// Local working copy, kept in sync with the bound model.
const f = reactive({
  q: '', city: '', tag: '', dateFrom: '', dateTo: '', isOnline: false,
  ...props.modelValue,
})
watch(() => props.modelValue, (val) => Object.assign(f, val), { deep: true })

function push() {
  emit('update:modelValue', { ...f })
}
function submit() {
  push()
  emit('search', { ...f })
}
</script>

<template>
  <form class="mask" @submit.prevent="submit">
    <div class="line">
      <label class="grow">
        <span>Suche</span>
        <input v-model="f.q" type="text" placeholder="Vue, Kubernetes, Hackathon…" @input="push" />
      </label>
      <label>
        <span>Ort</span>
        <input v-model="f.city" type="text" placeholder="Würzburg" @input="push" />
      </label>
      <label>
        <span>Tag</span>
        <input v-model="f.tag" type="text" placeholder="Python" @input="push" />
      </label>
    </div>
    <div class="line">
      <label>
        <span>Von</span>
        <input v-model="f.dateFrom" type="date" @change="push" />
      </label>
      <label>
        <span>Bis</span>
        <input v-model="f.dateTo" type="date" @change="push" />
      </label>
      <label class="check">
        <input v-model="f.isOnline" type="checkbox" @change="push" />
        <span>Nur Online</span>
      </label>
      <button class="btn primary go" type="submit">🔎 Suchen</button>
    </div>
  </form>
</template>

<style scoped>
.mask {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 14px;
  box-shadow: var(--shadow);
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.line { display: flex; gap: 10px; flex-wrap: wrap; align-items: flex-end; }
label { display: flex; flex-direction: column; gap: 4px; font-size: 12px; color: var(--muted); }
label.grow { flex: 1; min-width: 180px; }
label span { font-weight: 600; letter-spacing: .2px; }
input[type='text'], input[type='date'] {
  background: var(--bg);
  border: 1px solid var(--line);
  border-radius: 9px;
  padding: 8px 11px;
  color: var(--ink);
  font-size: 14px;
  font-family: inherit;
  outline: none;
}
input[type='text']:focus, input[type='date']:focus { border-color: var(--accent); }
label.check { flex-direction: row; align-items: center; gap: 7px; padding-bottom: 9px; }
label.check input { width: 16px; height: 16px; accent-color: var(--accent); }
.go { margin-left: auto; padding: 9px 18px; }
</style>
