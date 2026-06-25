---
project: 2026-hackathon
last_verified: 2026-06-25
---

## Concepts & Nomenclature
| Term | Technisch | Wo im Code |
|------|-----------|------------|
| Event Radar | Produktname (IT-Event-Aggregator Mainfranken/ZDI) | `frontend/`, `backend/` |
| User | Google-Identität (Schlüssel `google_sub`) | `backend/app/models.py` → `User` |
| Profile | Interessen/Expertise + Wohnort + Suchradius je User | `backend/app/models.py` → `Profile` |
| Session-Cookie | signierter httpOnly-Cookie, hält nur `user_id` | `backend/app/main.py` (SessionMiddleware) |
| Geocode-Stub | Wohnort-Text → lat/lng via Nominatim | `backend/app/geocode.py` |
| Connector-Ingestion | (noch nicht gebaut) zieht echte Events aus Plattformen | späterer Slice |

## Dev Environment
- **Backend (Docker):** `cd backend && cp .env.example .env && docker compose up --build` → API auf `http://localhost:8000` (Swagger: `/docs`), Postgres+PostGIS auf `:5432`.
- **Backend (ohne Docker):** Postgres lokal bereitstellen, dann `backend/.venv/bin/uvicorn app.main:app --reload` (DATABASE_URL auf localhost).
- **Frontend:** `cd frontend && npm install && npm run dev` → `http://localhost:5173` (Vite-Proxy leitet `/api` → `:8000`).
- **Ports:** Frontend 5173 · API 8000 · Postgres 5432.
- **OAuth:** läuft gegen `.env`-Platzhalter; echter Login erst wenn Google-Client-ID/Secret in `backend/.env` stehen.

<!-- /quickref -->

---

## Architecture

### Stack (gelockt)
- **Frontend:** Vue 3 + Vite, `vue-router`, plain scoped CSS. Einstieg `frontend/src/main.js`.
- **Backend:** FastAPI + SQLModel, Authlib (Google OAuth), httpx. Einstieg `backend/app/main.py`.
- **DB:** PostgreSQL 16 + PostGIS (Image `postgis/postgis:16-3.4`). Laufzeitdaten im Docker-Named-Volume `pgdata` — **nicht** im Repo/Worktree, **nicht** auf der org-Seite (mutabler Runtime-State). Schema-Source-of-Truth = `backend/app/models.py`.

### Auth-Flow (Google OAuth, Authorization-Code)
1. Frontend „Login mit Google" → `GET /api/auth/google/login` → Backend `authorize_redirect` zu Google.
2. Google → `GET /api/auth/google/callback` (direkt auf `:8000`) → Token-Tausch, User-Upsert per `google_sub`, leeres Profile anlegen, **signierten httpOnly-Session-Cookie** setzen (`user_id`).
3. Redirect zu `FRONTEND_URL/profile`. Cookie ist host-basiert (`localhost`, portunabhängig) → gilt für `:5173` und `:8000`.
4. `GET /api/auth/me` liefert den User oder 401; `POST /api/auth/logout` leert die Session.

### Datenmodell
- `User`: `id, google_sub (unique), email, display_name, avatar_url, created_at` — Tabelle `users` (nicht `user`, reserviertes Wort in Postgres).
- `Profile`: `user_id (FK unique), interests[] (JSON), expertise[] (JSON), home_label, home_lat, home_lng, radius_km` — Tabelle `profiles`. 1:1 zu User.

### API
| Route | Methode | Auth | Zweck |
|-------|---------|------|-------|
| `/api/health` | GET | – | Healthcheck |
| `/api/auth/google/login` | GET | – | Start OAuth |
| `/api/auth/google/callback` | GET | – | OAuth-Callback, Cookie setzen |
| `/api/auth/logout` | POST | – | Session leeren |
| `/api/auth/me` | GET | ✅ | aktueller User |
| `/api/profile` | GET/PUT | ✅ | Profil lesen/schreiben (PUT geocodet `home_label` bei Änderung) |

## Active Patterns
- **Same-origin im Dev über Vite-Proxy:** Frontend ruft `/api/...` relativ; Proxy (`vite.config.js`) leitet an `:8000`. Kein CORS-Tanz im Browser; `credentials: 'include'` in `frontend/src/api.js`.
- **Auth-State als Composable-Singleton:** `frontend/src/composables/useAuth.js` (module-level refs), `App.vue` lädt beim Mount `fetchMe()`.
- **Schema via `create_all`** statt Alembic (Slice 1, local-only). Alembic kommt, sobald das Schema stabil ist.

## Known Pitfalls
- **`docker compose` vs. `docker-compose`:** Plugin-Form `docker compose` nötig; Daemon (Docker Desktop) muss laufen — sonst Backend-Container/Postgres nicht startbar.
- **OAuth braucht echte Creds:** mit Platzhaltern startet alles, aber der Login-Klick scheitert am Token-Tausch (400). Werte in `backend/.env`, Redirect-URI `http://localhost:8000/api/auth/google/callback` in der Google Console autorisieren.
- **`backend/.env` ist gitignored** — Secrets nie committen; Vorlage ist `.env.example`.
