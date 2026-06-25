<script setup>
import { useAuth } from '../composables/useAuth'

// Public index / login page. Logged-in visitors are redirected to /dashboard by the router
// guard, so this view is only ever seen logged out — its job is to explain the product and
// get the user into the Google login.
const { login } = useAuth()

const features = [
  { ic: '📡', title: 'Alle Quellen, ein Radar', text: 'Meetup, Eventbrite, THWS, ZDI & Co. — automatisch zusammengeführt statt einzeln durchsuchen.' },
  { ic: '📍', title: 'Vor deiner Haustür', text: 'Gefiltert auf Mainfranken und deinen Suchradius — Würzburg, Schweinfurt, Aschaffenburg.' },
  { ic: '🎯', title: 'Auf dich zugeschnitten', text: 'Nach deinen Interessen und Fachgebieten gewichtet — Deep-Tech statt Sales-Pitches.' },
]
</script>

<template>
  <div class="wrap">
    <section class="hero">
      <span class="kick">Mainfranken Tech-Event-Radar</span>
      <h1>Finde die Tech-Community<br>vor deiner Haustür.</h1>
      <p>
        Alle IT-Events aus Mainfranken an einem Ort. Melde dich an, um dein
        personalisiertes Event-Dashboard zu sehen.
      </p>
      <div class="cta">
        <button class="btn primary lg" @click="login">Login mit Google</button>
        <span class="cta-hint">Nach dem Login landest du direkt auf deinem Dashboard.</span>
      </div>
    </section>

    <section class="features">
      <div v-for="f in features" :key="f.title" class="feature">
        <div class="ic">{{ f.ic }}</div>
        <h3>{{ f.title }}</h3>
        <p>{{ f.text }}</p>
      </div>
    </section>

    <p class="hint">Demo-Stand · echte Events kommen über die Connector-Ingestion (Slice 2 ff.).</p>
  </div>
</template>

<style scoped>
.hero { padding: 40px 0 24px; }
.hero h1 { font-size: 29px; line-height: 1.2; margin: 0 0 10px; letter-spacing: -.6px; }
.hero p { margin: 0; color: var(--muted); font-size: 15px; max-width: 30em; }
.hero .kick { display: inline-block; font-size: 12px; font-weight: 700; color: var(--accent); text-transform: uppercase; letter-spacing: .8px; margin-bottom: 10px; }
.cta { margin-top: 22px; display: flex; align-items: center; gap: 14px; flex-wrap: wrap; }
.btn.lg { padding: 11px 20px; font-size: 14px; }
.cta-hint { font-size: 12.5px; color: var(--faint); }

.features { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin: 26px 0 8px; }
@media (max-width: 640px) { .features { grid-template-columns: 1fr; } }
.feature { background: var(--card); border: 1px solid var(--line); border-radius: 14px; padding: 16px; box-shadow: var(--shadow); }
.feature .ic { font-size: 22px; }
.feature h3 { margin: 8px 0 5px; font-size: 14.5px; letter-spacing: -.2px; }
.feature p { margin: 0; font-size: 13px; color: var(--muted); }

.hint { font-size: 12px; color: var(--faint); text-align: center; margin-top: 30px; }
</style>
