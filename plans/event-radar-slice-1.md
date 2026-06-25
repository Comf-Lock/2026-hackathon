# Plan: Event Radar — Vertikaler Slice 1

**Ziel:** Basiswebseite (aus Mockup) + **Google-OAuth-Login** (keine eigene Passwortverwaltung) → nach Login **Profilseite** (Interessen, Expertise, Wohnort, Suchumkreis). Umsetzen **und auf Testserver deployen**.

**Stack (gelockt):** Vue 3 + Vite (frontend, plain scoped CSS) · FastAPI + PostgreSQL/PostGIS (backend) · Redis (später) · Deploy Docker-Compose → x1pro. Logo/Branding „Event Radar" liegt in `frontend/`.

---

## Prerequisites (von Lars / vor dem Build zu klären)

- [ ] **Google-OAuth-Client** anlegen (Google Cloud Console): Client-ID + Secret, autorisierte Redirect-URIs (localhost + Testserver-Domain). → ohne das kein Login-Test.
- [ ] **Testserver-Ziel** festlegen: x1pro? Subdomain/Domain für Frontend + API-Redirect-URI?
- [ ] **Git-Flow**: Branch-Protection auf master lockern (B) oder über PRs (A)? PR #1 noch offen.

## Offene Design-Entscheidungen

- [ ] Auth-Transport: **Session-Cookie** (httpOnly) vs. JWT im Frontend. Empfehlung: httpOnly-Session-Cookie nach OAuth-Callback (einfacher, sicherer fürs Web).
- [ ] OAuth-Flow: **Authorization Code** (Backend-seitig, Authlib) bevorzugt gegenüber reinem ID-Token im Frontend.
- [ ] `vue-router` einführen (Standard für /, /profile) — neue, aber etablierte Dep.

---

## Backend (FastAPI) — `backend/`

- [ ] FastAPI-Skeleton nach Haus-Muster (vgl. mail-ops): `src/main.py`, Settings via pydantic, httpx
- [ ] `docker-compose.yml`: postgres(+postgis) + api; `.env` für Secrets (Google-Client, DB-URL)
- [ ] SQLModel-Modelle:
  - [ ] `User`: id, google_sub (unique), email, display_name, avatar_url, created_at
  - [ ] `Profile`: user_id (FK), interests[] , expertise[] , home_label, home_lat, home_lng, radius_km
- [ ] Alembic init + erste Migration
- [ ] Google OAuth (Authlib, Authorization-Code-Flow):
  - [ ] `GET /api/auth/google/login` → Redirect zu Google
  - [ ] `GET /api/auth/google/callback` → Token tauschen, User upsert (per google_sub), Session-Cookie setzen
  - [ ] `POST /api/auth/logout`
- [ ] `GET /api/auth/me` → aktueller User (oder 401)
- [ ] `GET /api/profile` · `PUT /api/profile` (auth-pflichtig)
- [ ] Geocoding-Stub für Wohnort → lat/lng (Nominatim, später cachen)

## Frontend (Vue 3 + Vite) — `frontend/`

- [ ] Mockup `index.html` in Vue-App-Shell überführen (`src/main.js`, `App.vue`, Komponenten) — Branding/Logo „Event Radar" übernehmen
- [ ] `vue-router`: Routen `/` (Landing), `/profile` (auth-only, Redirect zu Login wenn nicht eingeloggt)
- [ ] Landing-Page aus Mockup (Hero, „Bleib verbunden", Event-Cards als statische Demo)
- [ ] **„Login mit Google"**-Button → `/api/auth/google/login`
- [ ] Auth-State via `GET /api/auth/me` (Composable `useAuth`)
- [ ] **Profilseite**: Interessen (Tags), Expertise/Fachrichtung, Wohnort (Texteingabe → Geocode), Suchumkreis (Slider km) → `PUT /api/profile`
- [ ] Vite-Proxy `/api` → FastAPI im Dev

## Deploy (Testserver)

- [ ] Frontend-Build (`vite build`) → nginx-Container oder static serve
- [ ] `docker-compose` (frontend + api + postgres) auf x1pro
- [ ] Deploy nach Haus-Policy: commit → push → `git pull` + `docker compose up --build` auf x1pro (kein SCP)
- [ ] Google-Redirect-URIs um Testserver-Domain ergänzen
- [ ] Smoke-Test: Login-Flow End-to-End + Profil speichern/laden

---

## Abschluss-Aktionen (bei Slice-1-Abschluss)

- In `documentation/technical/README.md` einfließen lassen: Auth-Flow (Google OAuth), Datenmodell User/Profile, Dev-Env (Ports, compose, Proxy), Deploy-Befehl.
- Architektur-Gesamtbild gehört in `documentation/features/event-radar-architecture.md` (noch zu schreiben — inkl. Ingestion/Connector-Sektion, siehe Vault `patterns/data-integration/connector-architecture.md`).
- Diesen Plan löschen, Lessons in Tech-Doku/Vault übertragen.
