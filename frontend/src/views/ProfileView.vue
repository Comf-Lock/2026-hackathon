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

const interestInput = ref('')
const expertiseInput = ref('')

onMounted(async () => {
  // Auth is enforced by the router guard before this view renders — just load the profile.
  try {
    const p = await api('/api/profile')
    form.interests = p.interests || []
    form.expertise = p.expertise || []
    form.home_label = p.home_label || ''
    form.radius_km = p.radius_km ?? 40
  } catch (e) {
    error.value = 'Profil konnte nicht geladen werden.'
  } finally {
    loading.value = false
  }
})

function addTag(list, inputRef) {
  const val = inputRef.value.trim()
  if (val && !list.includes(val)) list.push(val)
  inputRef.value = ''
}

function removeTag(list, tag) {
  const i = list.indexOf(tag)
  if (i !== -1) list.splice(i, 1)
}

async function save() {
  saving.value = true
  saved.value = false
  error.value = null
  try {
    const updated = await api('/api/profile', {
      method: 'PUT',
      body: JSON.stringify({
        interests: form.interests,
        expertise: form.expertise,
        home_label: form.home_label || null,
        radius_km: Number(form.radius_km),
      }),
    })
    form.home_label = updated.home_label || ''
    saved.value = true
  } catch (e) {
    error.value = 'Speichern fehlgeschlagen.'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="wrap">
    <h1 class="title">Dein Profil</h1>
    <p class="lead">Damit findet Event Radar die Events &amp; Communities, die zu dir passen.</p>

    <div v-if="loading" class="muted">Lädt …</div>

    <form v-else class="card" @submit.prevent="save">
      <!-- Interests -->
      <div class="field">
        <label>Interessen</label>
        <div class="chips">
          <span v-for="t in form.interests" :key="t" class="chip">
            {{ t }}<button type="button" class="x" @click="removeTag(form.interests, t)">×</button>
          </span>
        </div>
        <div class="tag-add">
          <input
            v-model="interestInput"
            placeholder="z. B. Frontend, AI/ML, DevOps"
            @keydown.enter.prevent="addTag(form.interests, interestInput)"
          />
          <button type="button" class="btn ghost" @click="addTag(form.interests, interestInput)">+</button>
        </div>
      </div>

      <!-- Expertise -->
      <div class="field">
        <label>Expertise / Fachrichtung</label>
        <div class="chips">
          <span v-for="t in form.expertise" :key="t" class="chip">
            {{ t }}<button type="button" class="x" @click="removeTag(form.expertise, t)">×</button>
          </span>
        </div>
        <div class="tag-add">
          <input
            v-model="expertiseInput"
            placeholder="z. B. Vue, Python, Embedded"
            @keydown.enter.prevent="addTag(form.expertise, expertiseInput)"
          />
          <button type="button" class="btn ghost" @click="addTag(form.expertise, expertiseInput)">+</button>
        </div>
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
</template>

<style scoped>
.title { font-size: 24px; letter-spacing: -.5px; margin: 28px 0 4px; }
.lead { color: var(--muted); font-size: 14px; margin: 0 0 20px; }
.muted { color: var(--muted); }

.card { background: var(--card); border: 1px solid var(--line); border-radius: 16px; padding: 22px; box-shadow: var(--shadow); }
.field { margin-bottom: 22px; }
.field > label { display: block; font-size: 13.5px; font-weight: 700; margin-bottom: 8px; }

.chips { display: flex; flex-wrap: wrap; gap: 7px; margin-bottom: 8px; }
.chip { display: inline-flex; align-items: center; gap: 5px; background: var(--accent-soft); color: var(--accent); font-size: 12.5px; font-weight: 600; border-radius: 7px; padding: 4px 6px 4px 10px; }
.chip .x { border: none; background: none; color: var(--accent); cursor: pointer; font-size: 15px; line-height: 1; padding: 0 2px; }

.tag-add { display: flex; gap: 8px; }
input { font-family: inherit; font-size: 14px; padding: 9px 12px; border: 1px solid var(--line); border-radius: 9px; width: 100%; background: var(--bg); }
input:focus { outline: none; border-color: var(--accent); }
.tag-add input { flex: 1; }

.slider { padding: 0; accent-color: var(--accent); }
.hint { display: block; font-size: 12px; color: var(--faint); margin-top: 6px; }

.actions { display: flex; align-items: center; gap: 14px; }
.ok { color: var(--good); font-size: 13px; font-weight: 600; }
.err { color: var(--accent); font-size: 13px; font-weight: 600; }
</style>
