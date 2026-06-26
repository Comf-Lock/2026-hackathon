<script setup>
import { onMounted, reactive, ref } from 'vue'
import { api } from '../api'

const loading = ref(true)
const saving = ref(false)
const saved = ref(false)
const error = ref(null)

const form = reactive({
  interests: [],
  expertise: [],
  home_label: '',
  radius_km: 40,
})

onMounted(async () => {
  // Auth is enforced by the router guard before this view renders — just load the profile.
  try {
    const p = await api('/api/profile')
    form.interests = Array.isArray(p.interests) ? [...p.interests] : []
    form.expertise = Array.isArray(p.expertise) ? [...p.expertise] : []
    form.home_label = p.home_label || ''
    form.radius_km = p.radius_km ?? 40
  } catch (e) {
    error.value = 'Profil konnte nicht geladen werden.'
  } finally {
    loading.value = false
  }
})

// "+" adds a new blank editable row; each row has its own × to remove it. The rows ARE the data
// (v-model binds straight onto the array entries), so what you see is exactly what gets saved —
// there is no separate "commit the typed value into a chip" step that could silently drop an
// entry on save (that was the original bug: a typed-but-not-added interest vanished on reload).
function addRow(list) {
  list.push('')
}

function removeRow(list, i) {
  list.splice(i, 1)
}

// Drop empty/whitespace rows and de-duplicate case-insensitively (first spelling wins) before save.
function clean(list) {
  const seen = new Set()
  const out = []
  for (const raw of list) {
    const val = (raw || '').trim()
    if (!val) continue
    const key = val.toLowerCase()
    if (seen.has(key)) continue
    seen.add(key)
    out.push(val)
  }
  return out
}

async function save() {
  saving.value = true
  saved.value = false
  error.value = null
  try {
    const updated = await api('/api/profile', {
      method: 'PUT',
      body: JSON.stringify({
        interests: clean(form.interests),
        expertise: clean(form.expertise),
        home_label: form.home_label.trim() || null,
        radius_km: Number(form.radius_km),
      }),
    })
    // Reflect the persisted, cleaned state back so the UI matches exactly what was stored.
    form.interests = Array.isArray(updated.interests) ? updated.interests : []
    form.expertise = Array.isArray(updated.expertise) ? updated.expertise : []
    form.home_label = updated.home_label || ''
    form.radius_km = updated.radius_km ?? form.radius_km
    saved.value = true
  } catch (e) {
    error.value = 'Speichern fehlgeschlagen.'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <!-- Shell mirrors LandingView/DashboardView (1240 outer + 854 content column) so the profile
       column lines up at the SAME width and left edge as the event feed — no jump when navigating. -->
  <div class="profile-shell">
    <div class="profile-col">
      <h1 class="title">Dein Profil</h1>
      <p class="lead">Damit findet Event Radar die Events &amp; Communities, die zu dir passen.</p>

      <div v-if="loading" class="muted">Lädt …</div>

      <form v-else class="card" @submit.prevent="save">
        <!-- Interests -->
        <div class="field">
          <label>Interessen</label>
          <div v-if="form.interests.length" class="rows">
            <div v-for="(item, i) in form.interests" :key="i" class="row">
              <input
                v-model="form.interests[i]"
                placeholder="z. B. Frontend, AI/ML, DevOps"
                @keydown.enter.prevent="addRow(form.interests)"
              />
              <button type="button" class="x-btn" aria-label="Entfernen" @click="removeRow(form.interests, i)">×</button>
            </div>
          </div>
          <p v-else class="empty">Noch keine Interessen — füge welche hinzu.</p>
          <button type="button" class="btn ghost add" @click="addRow(form.interests)">+ Interesse</button>
        </div>

        <!-- Expertise -->
        <div class="field">
          <label>Expertise / Fachrichtung</label>
          <div v-if="form.expertise.length" class="rows">
            <div v-for="(item, i) in form.expertise" :key="i" class="row">
              <input
                v-model="form.expertise[i]"
                placeholder="z. B. Vue, Python, Embedded"
                @keydown.enter.prevent="addRow(form.expertise)"
              />
              <button type="button" class="x-btn" aria-label="Entfernen" @click="removeRow(form.expertise, i)">×</button>
            </div>
          </div>
          <p v-else class="empty">Noch keine Expertise — füge welche hinzu.</p>
          <button type="button" class="btn ghost add" @click="addRow(form.expertise)">+ Expertise</button>
        </div>

        <!-- Home location -->
        <div class="field">
          <label>Wohnort</label>
          <input v-model="form.home_label" placeholder="z. B. Würzburg" />
          <span class="hint">Wird beim Speichern auf Koordinaten aufgelöst (Geocoding).</span>
        </div>

        <!-- Radius -->
        <div class="field">
          <label>Suchumkreis: <b>{{ form.radius_km }} km</b></label>
          <input v-model="form.radius_km" type="range" min="5" max="150" step="5" class="slider" />
        </div>

        <div class="actions">
          <button class="btn primary" type="submit" :disabled="saving">
            {{ saving ? 'Speichert …' : 'Profil speichern' }}
          </button>
          <span v-if="saved" class="ok">✓ Gespeichert</span>
          <span v-if="error" class="err">{{ error }}</span>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
.profile-shell { max-width: 1240px; margin: 0 auto; padding: 0 22px 60px; }
.profile-col { max-width: 854px; }

.title { font-size: 24px; letter-spacing: -.5px; margin: 28px 0 4px; }
.lead { color: var(--muted); font-size: 14px; margin: 0 0 20px; }
.muted { color: var(--muted); }

.card { background: var(--card); border: 1px solid var(--line); border-radius: 16px; padding: 22px; box-shadow: var(--shadow); }
.field { margin-bottom: 22px; }
.field > label { display: block; font-size: 13.5px; font-weight: 700; margin-bottom: 8px; }

/* Editable rows: one input per interest/expertise item, each removable. Fixed-width container +
   100%-width inputs mean adding/removing rows only changes height, never the column width. */
.rows { margin-bottom: 8px; }
.row { display: flex; gap: 8px; margin-bottom: 8px; }
.row input { flex: 1; }
.x-btn { flex: none; width: 38px; border: 1px solid var(--line); background: var(--bg); color: var(--muted); border-radius: 9px; cursor: pointer; font-size: 17px; line-height: 1; }
.x-btn:hover { color: var(--accent); border-color: var(--accent); }
.add { margin-top: 2px; }
.empty { color: var(--faint); font-size: 13px; margin: 0 0 8px; }

input { font-family: inherit; font-size: 14px; padding: 9px 12px; border: 1px solid var(--line); border-radius: 9px; width: 100%; background: var(--bg); }
input:focus { outline: none; border-color: var(--accent); }

.slider { padding: 0; accent-color: var(--accent); }
.hint { display: block; font-size: 12px; color: var(--faint); margin-top: 6px; }

.actions { display: flex; align-items: center; gap: 14px; }
.ok { color: var(--good); font-size: 13px; font-weight: 600; }
.err { color: var(--accent); font-size: 13px; font-weight: 600; }

/* Phone: trim the shell + card padding. Rows already stack (input flex:1 + 38px touch × button),
   so only the surrounding spacing needs to shrink. */
@media (max-width: 640px) {
  .profile-shell { padding: 0 14px 40px; }
  .card { padding: 16px; }
  .title { font-size: 21px; }
}
</style>
