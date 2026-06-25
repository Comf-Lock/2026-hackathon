<script setup>
defineProps({
  event: { type: Object, required: true },
})
</script>

<template>
  <div class="ev">
    <div class="date">
      <div class="d">{{ event.day }}</div>
      <div class="m">{{ event.month }}</div>
      <div class="t">{{ event.time }}</div>
    </div>
    <div class="body">
      <h3>{{ event.title }}</h3>
      <div class="row">
        <span>📍 {{ event.place }}</span>
        <span v-if="event.distance" class="near">{{ event.distance }}</span>
        <span>· {{ event.price }}</span>
      </div>
      <div class="tagrow">
        <span class="tag intent">{{ event.intent }}</span>
        <span v-for="tag in event.tags" :key="tag" class="tag">{{ tag }}</span>
        <span class="src">{{ event.source }}</span>
      </div>
      <div class="go">
        <button class="btn primary">Ich bin dabei</button>
        <button class="btn ghost">Merken</button>
        <span class="att"><b>{{ event.attending }}</b> dabei{{ event.fromGroups ? ` · ${event.fromGroups} aus deinen Gruppen` : '' }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.ev {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 16px;
  padding: 18px;
  margin-bottom: 14px;
  box-shadow: var(--shadow);
  display: flex;
  gap: 16px;
}
.date { flex: 0 0 56px; text-align: center; }
.date .d { font-size: 24px; font-weight: 800; line-height: 1; }
.date .m { font-size: 11px; font-weight: 700; color: var(--accent); text-transform: uppercase; letter-spacing: .5px; }
.date .t { font-size: 11px; color: var(--faint); margin-top: 3px; }
.body { flex: 1; min-width: 0; }
.body h3 { margin: 0 0 5px; font-size: 16.5px; letter-spacing: -.2px; }
.row { display: flex; flex-wrap: wrap; gap: 6px 14px; color: var(--muted); font-size: 13px; align-items: center; }
.row .near { color: var(--good); font-weight: 600; }
.tagrow { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 11px; align-items: center; }
.tag { font-size: 11.5px; background: var(--chip); border-radius: 6px; padding: 3px 9px; color: #55606e; font-weight: 600; }
.tag.intent { background: var(--accent-soft); color: var(--accent); }
.src { margin-left: auto; font-size: 11.5px; color: var(--faint); }
.go { margin-top: 13px; display: flex; gap: 9px; align-items: center; }
.att { font-size: 12.5px; color: var(--muted); margin-left: auto; }
.att b { color: var(--ink); }
</style>
