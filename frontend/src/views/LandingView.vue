<script setup>
import { ref } from 'vue'
import EventCard from '../components/EventCard.vue'
import { useAuth } from '../composables/useAuth'

const { user, login } = useAuth()

const tabs = ['Für dich', 'Diese Woche', 'Karte']
const activeTab = ref(0)

// Static demo data — real events come from the ingestion connectors in a later slice.
const groups = ref([
  { id: 'js', code: 'JS', color: '#b8324f', name: 'JS Würzburg', members: '412 Mitglieder', following: true },
  { id: 'py', code: 'PY', color: '#1f9d76', name: 'PyData Mainfranken', members: '268 Mitglieder', following: false },
  { id: 'fh', code: 'FH', color: '#2f6bd6', name: 'THWS Tech Talks', members: '530 Mitglieder', following: true },
])

const events = [
  {
    day: '02', month: 'Jul', time: '18:30',
    title: 'JS Würzburg Meetup — Vue 3 Deep Dive',
    place: 'TZ Mainfranken, Würzburg', distance: '1,8 km', price: 'Kostenlos',
    intent: '🛠 Deep-Tech', tags: ['Vue', 'Frontend'],
    source: 'gefunden auf 2 Plattformen', attending: 34, fromGroups: 3,
  },
  {
    day: '04', month: 'Jul', time: '19:00',
    title: 'PyData Mainfranken — LLMs in der Praxis',
    place: 'i-Campus, Schweinfurt', distance: '28 km', price: 'Kostenlos',
    intent: '🛠 Deep-Tech', tags: ['Python', 'AI/ML'],
    source: 'gefunden auf 3 Plattformen', attending: 57, fromGroups: 0,
  },
  {
    day: '06', month: 'Jul', time: '10:00',
    title: 'Maker Day Aschaffenburg — IoT & Embedded',
    place: 'Stadtwerke Lab, Aschaffenburg', distance: '78 km', price: '5 €',
    intent: '👥 Networking', tags: ['Embedded', 'Hardware'],
    source: 'nur auf Luma — Geheimtipp', attending: 19, fromGroups: 0,
  },
]

function toggleFollow(group) {
  group.following = !group.following
}
</script>

<template>
  <div class="wrap">
    <section class="hero">
      <span class="kick">Mainfranken Community Connect</span>
      <h1>Finde die Tech-Community<br>vor deiner Haustür.</h1>
      <p>
        Alle IT-Events aus Mainfranken an einem Ort — Würzburg, Schweinfurt,
        Aschaffenburg. Folge den Gruppen, die dich interessieren, und verpasse nichts mehr.
      </p>
      <div v-if="!user" class="cta">
        <button class="btn primary" @click="login">Login mit Google</button>
        <span class="cta-hint">Anmelden, um dein Profil &amp; deine Gruppen zu speichern.</span>
      </div>
    </section>

    <div class="tabs">
      <button
        v-for="(tab, i) in tabs"
        :key="tab"
        :class="{ on: i === activeTab }"
        @click="activeTab = i"
      >{{ tab }}</button>
    </div>

    <section class="connect">
      <h2>Bleib verbunden</h2>
      <p>Folge den aktiven Communities in Mainfranken — neue Events landen automatisch in „Für dich".</p>
      <div class="follow">
        <div v-for="g in groups" :key="g.id" class="grp">
          <div class="ic" :style="{ background: g.color }">{{ g.code }}</div>
          <div>
            <div class="n">{{ g.name }}</div>
            <div class="s">{{ g.members }}</div>
          </div>
          <button class="f" :class="{ on: g.following }" @click="toggleFollow(g)">
            {{ g.following ? '✓' : '+ Folgen' }}
          </button>
        </div>
      </div>
    </section>

    <div class="section-h">
      <h2>Events in deiner Nähe</h2>
      <span>· {{ events.length }} diese Woche</span>
    </div>

    <EventCard v-for="(ev, i) in events" :key="i" :event="ev" />

    <p class="hint">Demo-Daten · echte Events kommen über die Connector-Ingestion (späterer Slice).</p>
  </div>
</template>

<style scoped>
.hero { padding: 34px 0 12px; }
.hero h1 { font-size: 27px; line-height: 1.2; margin: 0 0 8px; letter-spacing: -.6px; }
.hero p { margin: 0; color: var(--muted); font-size: 15px; }
.hero .kick { display: inline-block; font-size: 12px; font-weight: 700; color: var(--accent); text-transform: uppercase; letter-spacing: .8px; margin-bottom: 10px; }
.cta { margin-top: 18px; display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.cta-hint { font-size: 12.5px; color: var(--faint); }

.tabs { display: flex; gap: 4px; margin: 22px 0 16px; background: var(--card); border: 1px solid var(--line); border-radius: 12px; padding: 4px; width: fit-content; }
.tabs button { border: none; background: none; color: var(--muted); font-weight: 600; font-size: 13.5px; padding: 8px 16px; border-radius: 9px; cursor: pointer; font-family: inherit; }
.tabs button.on { background: var(--ink); color: #fff; }

.section-h { display: flex; align-items: baseline; gap: 8px; margin: 8px 0 14px; }
.section-h h2 { font-size: 15px; margin: 0; letter-spacing: -.2px; }
.section-h span { font-size: 13px; color: var(--faint); }

.connect { background: linear-gradient(120deg, #fff, #fbf4f1); border: 1px solid var(--line); border-radius: 16px; padding: 18px; margin: 6px 0 22px; box-shadow: var(--shadow); }
.connect h2 { margin: 0 0 4px; font-size: 16px; }
.connect p { margin: 0 0 14px; color: var(--muted); font-size: 13.5px; }
.follow { display: flex; gap: 10px; overflow: auto; padding-bottom: 2px; }
.grp { flex: 0 0 auto; background: var(--card); border: 1px solid var(--line); border-radius: 12px; padding: 11px 13px; display: flex; align-items: center; gap: 10px; min-width: 200px; }
.grp .ic { width: 34px; height: 34px; border-radius: 9px; display: grid; place-items: center; font-weight: 800; color: #fff; }
.grp .n { font-size: 13.5px; font-weight: 700; line-height: 1.2; }
.grp .s { font-size: 11.5px; color: var(--faint); }
.grp .f { margin-left: 6px; border: 1px solid var(--line); background: none; border-radius: 7px; padding: 5px 10px; font-size: 12px; font-weight: 700; cursor: pointer; color: var(--accent); font-family: inherit; }
.grp .f.on { background: var(--accent); color: #fff; border-color: var(--accent); }

.hint { font-size: 12px; color: var(--faint); text-align: center; margin-top: 26px; }
</style>
