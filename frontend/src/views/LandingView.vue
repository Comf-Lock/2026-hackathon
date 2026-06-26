<script setup>
// Public index (logged out). Header pitch + Google login, then the shared SearchMask + EventList
// so visitors can browse Mainfranken events without an account. Logged-in users are bounced to
// /dashboard by the router guard, so this view is only ever seen logged out.
import { onMounted } from 'vue'
import { useAuth } from '../composables/useAuth'
import { useEvents } from '../composables/useEvents'
import SearchMask from '../components/SearchMask.vue'
import EventList from '../components/EventList.vue'

const { login } = useAuth()
const { filters, events, total, loading, load, center, locating, useMyLocation } = useEvents({ geo: true })

// Default the lower date bound to today — the index sells *upcoming* events; past ones stay reachable
// by clearing the field. Radius then narrows "what's on near me".
filters.value.dateFrom = new Date().toISOString().slice(0, 10)

// Show results immediately — visitors see events before typing anything.
onMounted(load)
</script>

<template>
  <div class="landing">
    <section class="hero">
      <span class="kick">Mainfranken Tech-Event-Radar</span>
      <h1>Finde die Tech-Community<br>vor deiner Haustür.</h1>
      <p>
        Alle IT-Events aus Mainfranken an einem Ort — Meetup, Eventbrite, THWS & Co.,
        automatisch zusammengeführt. Stöbere direkt los oder melde dich an für dein
        personalisiertes Dashboard.
      </p>
      <div class="cta">
        <button class="btn primary lg" @click="login">Login mit Google</button>
        <span class="cta-hint">Mit Login: persönliche Empfehlungen nach Interessen & Wohnort.</span>
      </div>
    </section>

    <section class="finder">
      <h2 class="section-title">Events durchsuchen</h2>
      <SearchMask
        v-model="filters"
        :geo="true"
        :locating="locating"
        :has-center="!!center"
        @search="load"
        @locate="useMyLocation"
      />
      <EventList
        :events="events"
        :loading="loading"
        :total="total"
        :savable="false"
        @require-login="login"
      />
    </section>

    <p class="hint">Demo-Stand · echte Events kommen über die Connector-Ingestion (Slice 2 ff.).</p>
  </div>
</template>

<style scoped>
/* Logged-out view is a single, centred column — no rail and therefore no empty "ghost" column on
   the right. The content uses one comfortable reading width, centred under the header. */
.landing { max-width: 900px; margin: 0 auto; padding: 0 22px 60px; }

.hero { padding: 40px 0 20px; }
.hero h1 { font-size: 29px; line-height: 1.2; margin: 0 0 10px; letter-spacing: -.6px; }
.hero p { margin: 0; color: var(--muted); font-size: 15px; max-width: 34em; }
.hero .kick { display: inline-block; font-size: 12px; font-weight: 700; color: var(--accent); text-transform: uppercase; letter-spacing: .8px; margin-bottom: 10px; }
.cta { margin-top: 22px; display: flex; align-items: center; gap: 14px; flex-wrap: wrap; }
.btn.lg { padding: 11px 20px; font-size: 14px; }
.cta-hint { font-size: 12.5px; color: var(--faint); }

.finder { margin-top: 28px; }
.section-title { font-size: 15px; margin: 0 0 12px; letter-spacing: -.2px; }

.hint { font-size: 12px; color: var(--faint); text-align: center; margin-top: 30px; }
</style>
