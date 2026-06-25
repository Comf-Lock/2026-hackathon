<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '../api'

// --- Auth-only view: the rich post-login dashboard (converted from prototype/dashboard.html,
// localized to Mainfranken). Event data is still static demo — real events arrive via the
// ingestion connectors (slice 2 phase C onwards). The profile strip is filled best-effort from
// the real /api/profile so the "Dein Profil" chips reflect the logged-in user.

const view = ref('feed') // 'feed' | 'cal' | 'map'

const homeLabel = ref('Würzburg')
const radiusKm = ref(50)
const interests = ref(['Vue', 'Python', 'AI/ML'])

onMounted(async () => {
  try {
    const p = await api('/api/profile')
    if (p?.home_label) homeLabel.value = p.home_label
    if (p?.radius_km) radiusKm.value = p.radius_km
    if (p?.interests?.length) interests.value = p.interests
  } catch {
    // not logged in / no profile yet → keep demo defaults
  }
})

const INTENT_LABEL = { deep: 'Community/Deep-Tech', recruit: 'Recruiting', vendor: 'Vendor/Sales', network: 'Networking' }
const INTENT_VAR = { deep: 'var(--deep)', recruit: 'var(--recruit)', vendor: 'var(--vendor)', network: 'var(--network)' }
const DEEP_HEX = '#b8324f'

function dominant(intent) {
  return Object.entries(intent).sort((a, b) => b[1] - a[1])[0]
}
function intentColor(key) {
  return INTENT_VAR[key].replace('var(--deep)', DEEP_HEX)
}

// Mainfranken demo events — same shape as the prototype, regional content.
const events = [
  {
    title: 'Würzburg DATA & ANALYTICS Meetup #27', tags: ['Data', 'KI', 'BI'], rating: 4.8, reviews: 64,
    date: '12. Juli 2026, 18:30', day: 12, place: 'ZDI Cube, Würzburg', dist: 1.8, size: 80, price: 'Kostenlos · Pizza & Frankenwein',
    intent: { deep: 72, recruit: 12, vendor: 10, network: 6 },
    sources: [['M', 'Meetup', '60 Anmeld.', '#e5575f'], ['L', 'LinkedIn', '30 Zusagen', '#2f7bd6'], ['E', 'Eventbrite', '—', '#f0762b']],
  },
  {
    title: 'AI & Recruiting Night Mainfranken', tags: ['AI/ML', 'Career', 'Networking'], rating: 3.9, reviews: 41,
    date: '15. Juli 2026, 19:00', day: 15, place: 'Posthalle, Würzburg', dist: 2.1, size: 220, price: '15 €',
    intent: { deep: 20, recruit: 55, vendor: 15, network: 10 },
    sources: [['L', 'LinkedIn', '180 Zusagen', '#2f7bd6'], ['E', 'Eventbrite', '40 Tickets', '#f0762b']],
  },
  {
    title: 'FrankenJS — Vue 3 Deep Dive', tags: ['Vue', 'Frontend', 'JS'], rating: 4.9, reviews: 88,
    date: '18. Juli 2026, 19:00', day: 18, place: 'Mayflower GmbH, Würzburg', dist: 1.2, size: 60, price: 'Kostenlos',
    intent: { deep: 88, recruit: 4, vendor: 3, network: 5 },
    sources: [['M', 'Meetup', '50 Anmeld.', '#e5575f'], ['L', 'LinkedIn', '15 Zusagen', '#2f7bd6']],
  },
  {
    title: 'THWS Platform Engineering Summit', tags: ['DevOps', 'Platform', 'Cloud'], rating: 4.1, reviews: 120,
    date: '21. Juli 2026, 09:00', day: 21, place: 'THWS, Schweinfurt', dist: 28, size: 400, price: 'ab 99 €',
    intent: { deep: 32, recruit: 10, vendor: 48, network: 10 },
    sources: [['E', 'Eventbrite', '300 Tickets', '#f0762b'], ['L', 'LinkedIn', '200 Zusagen', '#2f7bd6'], ['M', 'Meetup', '—', '#e5575f'], ['C', 'THWS-FIW', 'gelistet', '#36c5a0']],
  },
  {
    title: 'Embedded Linux Stammtisch Aschaffenburg', tags: ['Embedded', 'Linux', 'C'], rating: 4.6, reviews: 19,
    date: '22. Juli 2026, 18:00', day: 22, place: 'Stadtwerke Lab, Aschaffenburg', dist: 78, size: 28, price: 'Kostenlos',
    intent: { deep: 82, recruit: 3, vendor: 5, network: 10 }, blindspot: true,
    sources: [['U', 'Luma', '28 Plätze', '#6e8bff']],
  },
  {
    title: 'Würzburg Go Hack Night', tags: ['Go', 'Hackathon'], rating: 4.7, reviews: 52,
    date: '25. Juli 2026, 17:30', day: 25, place: 'TGZ Würzburg', dist: 2.3, size: 70, price: 'Kostenlos',
    intent: { deep: 65, recruit: 10, vendor: 5, network: 20 },
    sources: [['M', 'Meetup', '55 Anmeld.', '#e5575f'], ['U', 'Luma', '20 Plätze', '#6e8bff']],
  },
  {
    title: 'Women in Tech Mixer Mainfranken', tags: ['Networking', 'Career', 'AI/ML'], rating: 4.4, reviews: 33,
    date: '28. Juli 2026, 18:30', day: 28, place: 'IHK Würzburg', dist: 1.9, size: 120, price: 'Kostenlos',
    intent: { deep: 25, recruit: 20, vendor: 5, network: 50 },
    sources: [['L', 'LinkedIn', '90 Zusagen', '#2f7bd6'], ['E', 'Eventbrite', '40 Tickets', '#f0762b']],
  },
]

const activeConnectors = computed(() => {
  const set = new Set()
  events.forEach((e) => e.sources.forEach((s) => set.add(s[1])))
  return set.size
})

// Calendar — July 2026 starts on a Wednesday (1.7.2026 = Mi → 2 empty leading cells).
const dows = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So']
const calDays = computed(() => {
  const cells = []
  for (let i = 0; i < 2; i++) cells.push({ out: true })
  for (let d = 1; d <= 31; d++) {
    cells.push({ num: d, events: events.filter((e) => e.day === d) })
  }
  return cells
})

// Map — pseudo positions around the centre (matches the prototype's layout feel).
const pinPos = [[62, 30], [44, 60], [30, 38], [74, 66], [24, 68], [58, 72], [68, 42]]
function pinStyle(e, i) {
  const [k] = dominant(e.intent)
  const sz = Math.max(22, Math.min(40, e.size / 22))
  return { left: pinPos[i][0] + '%', top: pinPos[i][1] + '%', '--pin-color': intentColor(k), '--pin-size': sz + 'px' }
}
function shortTitle(t) {
  return t.split(' ').slice(0, 2).join(' ')
}
</script>

<template>
  <div class="dash">
    <!-- Profile filter strip -->
    <div class="filterbar">
      <span class="label">Dein Profil</span>
      <span class="chip on">📍 {{ homeLabel }} <span class="x">+{{ radiusKm }} km ▾</span></span>
      <span v-for="tag in interests" :key="tag" class="chip on">🏷 {{ tag }} <span class="x">×</span></span>
      <span class="chip">+ Interesse</span>
      <span class="chip push">⚖️ Intent: Community ▾</span>
    </div>

    <div class="layout">
      <main>
        <div class="searchrow">
          <div class="search">🔎 <input placeholder="Suche: &quot;Vue&quot;, &quot;Kubernetes&quot;, &quot;Schweinfurt&quot;…"></div>
        </div>

        <div class="viewbar">
          <div class="seg">
            <button :class="{ on: view === 'feed' }" @click="view = 'feed'">▦ Feed</button>
            <button :class="{ on: view === 'cal' }" @click="view = 'cal'">📅 Kalender</button>
            <button :class="{ on: view === 'map' }" @click="view = 'map'">🗺 Karte</button>
          </div>
          <span class="count">{{ events.length }} Events · {{ activeConnectors }} Connectoren aktiv</span>
        </div>

        <!-- FEED -->
        <section v-show="view === 'feed'">
          <article v-for="(e, i) in events" :key="i" class="card">
            <div class="top">
              <div>
                <h3>{{ e.title }}</h3>
                <div class="tags"><span v-for="t in e.tags" :key="t" class="tag">{{ t }}</span></div>
              </div>
              <div class="rating"><span class="stars">★</span>{{ e.rating }}<span class="muted rev">({{ e.reviews }})</span></div>
            </div>
            <div class="meta">
              <span>📅 <b>{{ e.date }}</b></span>
              <span>📍 <b>{{ e.place }}</b> · <span class="near">{{ e.dist }} km</span></span>
              <span>👥 <b>~{{ e.size }}</b></span>
              <span>💰 <b>{{ e.price }}</b></span>
            </div>
            <div class="intent">
              <div class="head">
                <span class="t">Event-Intent</span>
                <span class="verdict" :style="{ color: intentColor(dominant(e.intent)[0]) }">
                  ▣ {{ dominant(e.intent)[1] }}% {{ INTENT_LABEL[dominant(e.intent)[0]] }}
                </span>
              </div>
              <div class="bar">
                <i class="seg-deep" :style="{ width: e.intent.deep + '%' }"></i>
                <i class="seg-recruit" :style="{ width: e.intent.recruit + '%' }"></i>
                <i class="seg-vendor" :style="{ width: e.intent.vendor + '%' }"></i>
                <i class="seg-network" :style="{ width: e.intent.network + '%' }"></i>
              </div>
              <div class="legend">
                <span><i class="d-deep"></i>Deep-Tech</span>
                <span><i class="d-recruit"></i>Recruiting</span>
                <span><i class="d-vendor"></i>Vendor</span>
                <span><i class="d-network"></i>Networking</span>
              </div>
            </div>
            <div class="sources">
              <span class="lab">Quellen-Abgleich ({{ e.sources.length }})</span>
              <span v-for="(s, si) in e.sources" :key="si" class="src">
                <span class="ic" :style="{ background: s[3] }">{{ s[0] }}</span>{{ s[1] }} <span class="muted">{{ s[2] }}</span>
              </span>
              <span v-if="e.blindspot" class="blindspot">⚡ Blindspot · nur 1 Quelle</span>
            </div>
            <div class="actions">
              <button class="btn ghost">Details anzeigen</button>
              <button class="btn primary">+ Zum Kalender</button>
            </div>
          </article>
        </section>

        <!-- CALENDAR -->
        <section v-show="view === 'cal'">
          <div class="calendar">
            <div class="calhead">
              <button class="chip">‹</button><h2>Juli 2026</h2><button class="chip">›</button>
              <span class="count push">Farbe = dominanter Intent</span>
            </div>
            <div class="calgrid">
              <div v-for="d in dows" :key="d" class="dow">{{ d }}</div>
              <div v-for="(c, i) in calDays" :key="i" class="day" :class="{ out: c.out }">
                <div v-if="!c.out" class="num">{{ c.num }}</div>
                <div
                  v-for="(e, ei) in (c.events || [])" :key="ei" class="ev"
                  :style="{ background: intentColor(dominant(e.intent)[0]) }" :title="e.title"
                >{{ shortTitle(e.title) }}</div>
              </div>
            </div>
          </div>
        </section>

        <!-- MAP -->
        <section v-show="view === 'map'">
          <div class="map">
            <div class="mapcanvas"></div>
            <div class="grid-lines"></div>
            <div class="radius-circle"></div>
            <div class="me" :title="`Du · ${homeLabel}`"></div>
            <div
              v-for="(e, i) in events" :key="i" class="pin" :style="pinStyle(e, i)"
            >
              <div class="dot"><b>{{ e.size }}</b></div>
              <div class="lab">{{ shortTitle(e.title) }} · {{ e.dist }}km</div>
            </div>
            <div class="maplegend">
              <b>🟢 Du ({{ homeLabel }})</b> · Radius {{ radiusKm }} km<br>
              <span class="muted">Pin-Farbe = Intent · Größe = Teilnehmer</span>
            </div>
          </div>
        </section>
      </main>

      <aside class="rail">
        <div class="box">
          <h4>Warum diese Events?</h4>
          <div class="why"><span class="ic">◆</span><div>Match auf <b>{{ interests[0] }}</b> &amp; <b>{{ interests[1] || 'deine Tags' }}</b> im Profil</div></div>
          <div class="why"><span class="ic">◆</span><div>Alle unter <b>{{ radiusKm }} km</b> von {{ homeLabel }}</div></div>
          <div class="why"><span class="ic">◆</span><div>Gewichtet auf <b>Community/Deep-Tech</b> statt Sales</div></div>
        </div>
        <div class="box">
          <h4>Demnächst gespeichert</h4>
          <div class="mini"><div class="date"><div class="d">12</div><div class="m">JUL</div></div>
            <div class="info"><b>DATA & ANALYTICS #27</b><span class="muted">18:30 · ZDI Cube</span></div></div>
          <div class="mini"><div class="date"><div class="d">18</div><div class="m">JUL</div></div>
            <div class="info"><b>FrankenJS Vue 3</b><span class="muted">19:00 · Mayflower</span></div></div>
        </div>
        <div class="box">
          <h4>⚡ Blindspot-Feed</h4>
          <div class="muted bs-intro">Events, die nur auf <b>einer</b> Plattform gelistet sind — von den großen Aggregatoren übersehen.</div>
          <div class="mini"><div class="date"><div class="d">22</div><div class="m">JUL</div></div>
            <div class="info"><b>Embedded Linux Stammtisch</b><span class="muted">nur Luma · 28 Plätze</span></div></div>
        </div>
      </aside>
    </div>

    <p class="hint">Demo-Daten · echte Events kommen über die Connector-Ingestion (Slice 2 ff.).</p>
  </div>
</template>

<style scoped>
.dash {
  /* local palette derived from the global tokens + the prototype's intent colours */
  --bg2: var(--card);
  --bg3: var(--chip);
  --txt: var(--ink);
  --accent2: var(--good);
  --deep: #b8324f;
  --recruit: #d98a2b;
  --vendor: #9c5cab;
  --network: #1f9d76;
  --radius: 14px;
  max-width: 1240px;
  margin: 0 auto;
  padding: 0 22px 50px;
}
.muted { color: var(--muted); }

/* filter strip */
.filterbar { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; padding: 14px 0 16px; }
.filterbar .label { color: var(--faint); font-size: 12px; text-transform: uppercase; letter-spacing: .5px; }
.chip { display: inline-flex; align-items: center; gap: 6px; background: var(--bg3); border: 1px solid var(--line); border-radius: 20px; padding: 5px 11px; font-size: 13px; cursor: pointer; transition: .15s; }
.chip:hover { border-color: var(--accent); }
.chip.on { background: var(--accent-soft); border-color: var(--accent); color: var(--accent); }
.chip .x { color: var(--faint); font-size: 12px; }
.chip.push { margin-left: auto; }

.layout { display: grid; grid-template-columns: 1fr 320px; gap: 22px; }
@media (max-width: 1000px) { .layout { grid-template-columns: 1fr; } .rail { display: none; } }

.searchrow { margin-bottom: 14px; }
.search { display: flex; align-items: center; gap: 8px; background: var(--bg2); border: 1px solid var(--line); border-radius: 10px; padding: 9px 12px; max-width: 520px; }
.search input { flex: 1; background: none; border: none; color: var(--txt); outline: none; font-size: 14px; font-family: inherit; }

.viewbar { display: flex; align-items: center; gap: 6px; margin-bottom: 18px; }
.seg { display: inline-flex; background: var(--bg2); border: 1px solid var(--line); border-radius: 10px; padding: 3px; }
.seg button { background: none; border: none; color: var(--muted); padding: 7px 16px; border-radius: 7px; cursor: pointer; font-size: 13px; font-weight: 600; font-family: inherit; }
.seg button.on { background: var(--accent); color: #fff; }
.count { margin-left: auto; color: var(--muted); font-size: 13px; }
.count.push { margin-left: auto; }

/* event card */
.card { background: var(--bg2); border: 1px solid var(--line); border-radius: var(--radius); padding: 18px; margin-bottom: 16px; transition: .15s; box-shadow: var(--shadow); }
.card:hover { transform: translateY(-1px); border-color: #d9d3c8; }
.card .top { display: flex; justify-content: space-between; gap: 14px; align-items: flex-start; }
.card h3 { margin: 0 0 3px; font-size: 17px; font-weight: 700; letter-spacing: -.2px; }
.tags { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 7px; }
.tag { font-size: 11px; background: var(--bg3); border: 1px solid var(--line); border-radius: 6px; padding: 2px 8px; color: var(--muted); }
.rating { display: flex; align-items: center; gap: 5px; background: var(--bg3); border: 1px solid var(--line); border-radius: 8px; padding: 5px 10px; font-weight: 700; white-space: nowrap; }
.rating .stars { color: var(--recruit); }
.rating .rev { font-weight: 400; }
.meta { display: flex; flex-wrap: wrap; gap: 16px; margin: 14px 0; color: var(--muted); font-size: 13px; }
.meta b { color: var(--txt); font-weight: 600; }
.meta .near { color: var(--accent2); font-weight: 700; }

.intent { margin: 14px 0 6px; }
.intent .head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.intent .head .t { font-size: 11px; text-transform: uppercase; letter-spacing: .6px; color: var(--faint); }
.intent .head .verdict { font-size: 12px; font-weight: 700; }
.bar { display: flex; height: 9px; border-radius: 6px; overflow: hidden; background: var(--bg3); }
.bar i { display: block; height: 100%; }
.seg-deep { background: var(--deep); } .seg-recruit { background: var(--recruit); }
.seg-vendor { background: var(--vendor); } .seg-network { background: var(--network); }
.legend { display: flex; gap: 14px; margin-top: 7px; flex-wrap: wrap; }
.legend span { display: flex; align-items: center; gap: 5px; font-size: 11px; color: var(--muted); }
.legend i { width: 8px; height: 8px; border-radius: 2px; display: inline-block; }
.d-deep { background: var(--deep); } .d-recruit { background: var(--recruit); }
.d-vendor { background: var(--vendor); } .d-network { background: var(--network); }

.sources { display: flex; align-items: center; gap: 10px; margin-top: 14px; padding-top: 14px; border-top: 1px solid var(--line); flex-wrap: wrap; }
.sources .lab { font-size: 11px; text-transform: uppercase; letter-spacing: .5px; color: var(--faint); }
.src { display: flex; align-items: center; gap: 6px; background: var(--bg3); border: 1px solid var(--line); border-radius: 8px; padding: 4px 9px; font-size: 12px; }
.src .ic { width: 18px; height: 18px; border-radius: 5px; display: grid; place-items: center; font-weight: 700; font-size: 10px; color: #fff; }
.blindspot { margin-left: auto; display: flex; align-items: center; gap: 6px; font-size: 12px; font-weight: 700; color: #9a6212; background: rgba(217, 138, 43, .14); border: 1px solid rgba(217, 138, 43, .4); border-radius: 8px; padding: 4px 10px; }
.actions { display: flex; gap: 10px; margin-top: 16px; }
.actions .btn { flex: 1; }

/* calendar */
.calendar { background: var(--bg2); border: 1px solid var(--line); border-radius: var(--radius); padding: 18px; box-shadow: var(--shadow); }
.calhead { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; }
.calhead h2 { margin: 0; font-size: 17px; }
.calgrid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 7px; }
.dow { font-size: 11px; color: var(--faint); text-transform: uppercase; text-align: center; padding-bottom: 4px; }
.day { min-height: 88px; background: var(--bg); border: 1px solid var(--line); border-radius: 9px; padding: 6px; display: flex; flex-direction: column; gap: 4px; }
.day.out { opacity: .45; }
.day .num { font-size: 12px; color: var(--muted); font-weight: 600; }
.ev { font-size: 10.5px; border-radius: 5px; padding: 3px 6px; color: #fff; font-weight: 700; cursor: pointer; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* map */
.map { background: var(--bg2); border: 1px solid var(--line); border-radius: var(--radius); overflow: hidden; position: relative; height: 560px; box-shadow: var(--shadow); }
.mapcanvas { position: absolute; inset: 0; background: radial-gradient(circle at 50% 48%, rgba(184, 50, 79, .07), transparent 55%), linear-gradient(0deg, #f1efe9, #f7f6f3); }
.grid-lines { position: absolute; inset: 0; background-image: linear-gradient(var(--line) 1px, transparent 1px), linear-gradient(90deg, var(--line) 1px, transparent 1px); background-size: 46px 46px; opacity: .55; }
.radius-circle { position: absolute; left: 50%; top: 48%; width: 340px; height: 340px; transform: translate(-50%, -50%); border-radius: 50%; border: 1.5px dashed rgba(31, 157, 118, .5); background: rgba(31, 157, 118, .05); }
.me { position: absolute; left: 50%; top: 48%; transform: translate(-50%, -50%); width: 14px; height: 14px; border-radius: 50%; background: var(--accent2); box-shadow: 0 0 0 6px rgba(31, 157, 118, .22); }
.pin { position: absolute; transform: translate(-50%, -100%); cursor: pointer; display: flex; flex-direction: column; align-items: center; gap: 3px; }
.pin .dot { width: var(--pin-size); height: var(--pin-size); border-radius: 50% 50% 50% 0; transform: rotate(-45deg); border: 2px solid #fff; box-shadow: 0 2px 6px rgba(20, 24, 31, .2); display: grid; place-items: center; background: var(--pin-color); }
.pin .dot b { transform: rotate(45deg); font-size: 11px; color: #fff; font-weight: 800; }
.pin .lab { background: rgba(255, 255, 255, .92); border: 1px solid var(--line); border-radius: 6px; padding: 2px 7px; font-size: 11px; white-space: nowrap; color: var(--txt); box-shadow: var(--shadow); }
.maplegend { position: absolute; left: 16px; bottom: 16px; background: rgba(255, 255, 255, .92); border: 1px solid var(--line); border-radius: 10px; padding: 12px 14px; font-size: 12px; box-shadow: var(--shadow); }

/* right rail */
.rail .box { background: var(--bg2); border: 1px solid var(--line); border-radius: var(--radius); padding: 16px; margin-bottom: 16px; box-shadow: var(--shadow); }
.rail h4 { margin: 0 0 12px; font-size: 13px; text-transform: uppercase; letter-spacing: .6px; color: var(--faint); }
.why { display: flex; gap: 9px; align-items: flex-start; margin-bottom: 11px; font-size: 13px; }
.why .ic { color: var(--accent); margin-top: 1px; }
.mini { display: flex; gap: 10px; align-items: center; margin-bottom: 12px; }
.mini .date { width: 42px; text-align: center; background: var(--bg3); border: 1px solid var(--line); border-radius: 8px; padding: 5px 0; }
.mini .date .d { font-size: 16px; font-weight: 800; line-height: 1; }
.mini .date .m { font-size: 10px; color: var(--muted); }
.mini .info b { display: block; font-size: 13px; }
.bs-intro { font-size: 13px; margin-bottom: 10px; }
.bs-intro b { color: var(--txt); }

.hint { font-size: 12px; color: var(--faint); text-align: center; margin-top: 26px; }
</style>
