<script setup>
// Logged-in dashboard: the personalised home for authenticated users.
//
// It reuses the SHARED search components (SearchMask + EventList) and the single useEvents data
// layer. On top of the shared search it adds the personalisation that distinguishes it from the
// public index:
//   - greeting with the user's name
//   - filter pre-fill from the profile (interests → tag, home_label → city)
//   - a "Für dich" strip of interest-based recommendations
// Everything degrades cleanly when there is no profile / a 401 / no live event endpoint yet.
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { api } from '../api'
import { useAuth } from '../composables/useAuth'
import { useEvents } from '../composables/useEvents'
import { distinctSources } from '../lib/eventDisplay'
import SearchMask from '../components/SearchMask.vue'
import EventList from '../components/EventList.vue'
import MiniEventRow from '../dashboard/MiniEventRow.vue'

// Auth is resolved by the router guard before this view renders, so `user` is already populated —
// no fetchMe()/redirect here. We only read the user for the greeting.
const { user } = useAuth()

const profile = ref(null)
const profileReady = ref(false)

// Two independent search states: the main list (driven by the SearchMask) and the
// interest-based recommendations ("Für dich"). Destructured so the refs auto-unwrap in template.
const {
  filters: mainFilters, events: mainEvents, total: mainTotal,
  loading: mainLoading, error: mainError, load: mainLoad,
} = useEvents()
const {
  filters: recoFilters, events: recoEvents, total: recoTotal,
  loading: recoLoading, error: recoError, load: recoLoad,
} = useEvents()

// Bookmarks ("Merken"): savedIds drives the card button state; savedEvents fills the rail box.
const savedEvents = ref([])
const savedIds = computed(() => savedEvents.value.map((e) => e.id))

async function loadBookmarks() {
  try {
    savedEvents.value = await api('/api/bookmarks')
  } catch {
    savedEvents.value = []
  }
}

async function toggleSave(eventId) {
  const isSaved = savedIds.value.includes(eventId)
  try {
    await api(`/api/bookmarks/${eventId}`, { method: isSaved ? 'DELETE' : 'POST' })
    await loadBookmarks()
  } catch {
    /* non-fatal — leave state unchanged */
  }
}

// "Exklusiv gelistet": events found on only one source — framed positively as a discovery
// (something you'd miss elsewhere), not as a gap. Cross-source dedup (Slice 5) makes multi-source
// listings real, so this rail surfaces the genuinely single-source finds.
const exclusiveEvents = computed(() =>
  mainEvents.value.filter((e) => distinctSources(e.sources).length <= 1).slice(0, 4),
)

const firstName = computed(() => (user.value?.display_name || '').split(' ')[0] || '')
const interests = computed(() => profile.value?.interests || [])
const homeLabel = computed(() => profile.value?.home_label || '')
const radiusKm = computed(() => profile.value?.radius_km || null)
const primaryInterest = computed(() => interests.value[0] || '')

onMounted(async () => {
  // Best-effort profile load → pre-fill filters. Any failure (401 / no profile) is non-fatal.
  try {
    profile.value = await api('/api/profile')
  } catch {
    profile.value = null
  } finally {
    profileReady.value = true
  }

  // Pre-fill the main + reco filters from the profile. Replace the filter object (not in-place
  // mutation) so the bound SearchMask re-syncs its inputs and search() sees the new values.
  const prefill = {}
  if (homeLabel.value) prefill.city = homeLabel.value
  if (primaryInterest.value) prefill.tag = primaryInterest.value
  if (Object.keys(prefill).length) mainFilters.value = { ...mainFilters.value, ...prefill }
  if (primaryInterest.value) recoFilters.value = { ...recoFilters.value, tag: primaryInterest.value }

  await Promise.all([mainLoad(), recoLoad(), loadBookmarks()])
})

// The live event API was unreachable on the last load → useEvents fell back to demo fixtures
// and set `error`. Surface that instead of failing silently.
const apiError = computed(() => Boolean(mainError.value || recoError.value))
</script>

<template>
  <div class="dash">
    <!-- Greeting + personalised context strip -->
    <section class="hero">
      <div class="hello">
        <h1>Hallo{{ firstName ? `, ${firstName}` : '' }} 👋</h1>
        <p class="sub">Dein persönlicher Event-Radar für Mainfranken.</p>
      </div>
      <RouterLink to="/profile" class="btn ghost edit">Profil bearbeiten</RouterLink>
    </section>

    <div v-if="profileReady" class="profilebar">
      <span class="label">Dein Profil</span>
      <span v-if="homeLabel" class="chip on">📍 {{ homeLabel }}<span v-if="radiusKm" class="x">+{{ radiusKm }} km</span></span>
      <span v-for="t in interests" :key="t" class="chip on">🏷 {{ t }}</span>
      <RouterLink v-if="!homeLabel && !interests.length" to="/profile" class="chip">
        + Profil vervollständigen für bessere Empfehlungen
      </RouterLink>
    </div>

    <div v-if="apiError" class="apierr" role="alert">
      <span class="ic">⚠</span>
      <span>Live-Events konnten gerade nicht geladen werden — angezeigt werden Demo-Daten. Bitte später erneut versuchen.</span>
    </div>

    <div class="layout">
      <main>
        <!-- "Für dich" recommendations (interest-based) -->
        <section v-if="primaryInterest" class="block">
          <div class="blockhead">
            <h2>Für dich</h2>
            <span class="hint">basierend auf <b>{{ primaryInterest }}</b></span>
          </div>
          <EventList
            :events="recoEvents"
            :loading="recoLoading"
            :total="recoTotal"
            :savable="true"
            :savedIds="savedIds"
            @toggle-save="toggleSave"
          />
        </section>

        <!-- Shared search + results (same as the public index) -->
        <section class="block">
          <div class="blockhead">
            <h2>Alle Events</h2>
            <span v-if="mainTotal" class="hint">{{ mainTotal }} Treffer</span>
          </div>
          <SearchMask v-model="mainFilters" @search="mainLoad" />
          <div class="results">
            <EventList
              :events="mainEvents"
              :loading="mainLoading"
              :total="mainTotal"
              :savable="true"
              :savedIds="savedIds"
              @toggle-save="toggleSave"
            />
          </div>
        </section>
      </main>

      <aside class="rail">
        <div class="box">
          <h4>Warum diese Events?</h4>
          <div class="why"><span class="ic">◆</span><div>
            <template v-if="primaryInterest">Match auf <b>{{ primaryInterest }}</b><template v-if="interests[1]"> &amp; <b>{{ interests[1] }}</b></template> aus deinem Profil</template>
            <template v-else>Vervollständige dein Profil für persönliche Treffer</template>
          </div></div>
          <div v-if="homeLabel" class="why"><span class="ic">◆</span><div>Rund um <b>{{ homeLabel }}</b><template v-if="radiusKm"> · {{ radiusKm }} km</template></div></div>
          <div class="why"><span class="ic">◆</span><div>Aggregiert aus mehreren Quellen — Sichtbarkeit pro Event</div></div>
        </div>
        <div v-if="savedEvents.length" class="box">
          <h4>Demnächst gespeichert</h4>
          <MiniEventRow v-for="e in savedEvents.slice(0, 5)" :key="e.id" :event="e" />
        </div>

        <div v-if="exclusiveEvents.length" class="box">
          <h4>★ Exklusiv gelistet</h4>
          <p class="muted bs-note">Events, die wir aktuell auf nur <b>einer</b> Quelle gefunden haben — Entdeckungen, die du anderswo leicht verpasst. Mehr Quellen = höhere Sichtbarkeit.</p>
          <MiniEventRow v-for="e in exclusiveEvents" :key="e.id" :event="e" />
        </div>

        <div class="box tip">
          <h4>Tipp</h4>
          <p class="muted">Passe Interessen, Wohnort und Radius im <RouterLink to="/profile">Profil</RouterLink> an — die Vorschläge richten sich danach.</p>
        </div>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.dash { max-width: 1240px; margin: 0 auto; padding: 18px 22px 50px; }
.muted { color: var(--muted); }

.hero { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }
.hello h1 { margin: 0; font-size: 26px; letter-spacing: -.5px; }
.hello .sub { margin: 4px 0 0; color: var(--muted); font-size: 14px; }
.edit { text-decoration: none; white-space: nowrap; }

.profilebar { display: flex; align-items: center; gap: 9px; flex-wrap: wrap; padding: 16px 0 4px; }
.profilebar .label { color: var(--faint); font-size: 12px; text-transform: uppercase; letter-spacing: .5px; }
.chip { display: inline-flex; align-items: center; gap: 6px; background: var(--chip); border: 1px solid var(--line); border-radius: 20px; padding: 5px 11px; font-size: 13px; text-decoration: none; color: var(--ink); }
.chip.on { background: var(--accent-soft); border-color: var(--accent); color: var(--accent); }
.chip .x { color: var(--faint); font-size: 12px; }

.layout { display: grid; grid-template-columns: 1fr 320px; gap: 22px; margin-top: 16px; }
@media (max-width: 1000px) { .layout { grid-template-columns: 1fr; } .rail { display: none; } }

.block { margin-bottom: 26px; }
.blockhead { display: flex; align-items: baseline; gap: 10px; margin-bottom: 12px; }
.blockhead h2 { margin: 0; font-size: 18px; letter-spacing: -.3px; }
.blockhead .hint { color: var(--muted); font-size: 13px; }
.results { margin-top: 14px; }

.rail .box { background: var(--card); border: 1px solid var(--line); border-radius: 14px; padding: 16px; margin-bottom: 16px; box-shadow: var(--shadow); }
.rail h4 { margin: 0 0 12px; font-size: 13px; text-transform: uppercase; letter-spacing: .6px; color: var(--faint); }
.why { display: flex; gap: 9px; align-items: flex-start; margin-bottom: 11px; font-size: 13px; }
.why .ic { color: var(--accent); margin-top: 1px; }

.bs-note { font-size: 12px; margin: 0 0 12px; line-height: 1.45; }
.bs-note b { color: var(--ink, var(--txt)); }
.tip p { margin: 0; font-size: 13px; }
.tip a { color: var(--accent); font-weight: 600; }

/* API-error banner — visible warning when the live event endpoint was unreachable. */
.apierr { display: flex; align-items: center; gap: 10px; margin-top: 16px; padding: 11px 14px; font-size: 13px; color: #9a3a1f; background: rgba(217,90,43,.10); border: 1px solid rgba(217,90,43,.38); border-radius: 12px; }
.apierr .ic { font-size: 15px; }
</style>
