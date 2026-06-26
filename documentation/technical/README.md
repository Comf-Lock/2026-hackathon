---
project: 2026-hackathon
last_verified: 2026-06-26
---

## Concepts & Nomenclature
| Term | Technisch | Wo im Code |
|------|-----------|------------|
| Event Radar | Produktname (IT-Event-Aggregator Mainfranken/ZDI) | `frontend/`, `backend/` |
| User / Profile | Google-Identität (`google_sub`) + Interessen/Wohnort/Radius | `backend/app/models.py` |
| Session-Cookie | signierter httpOnly-Cookie, hält nur `user_id` | `backend/app/main.py` (SessionMiddleware) |
| Event | kanonisches, quell-agnostisches Event (was die App liest) | `backend/app/models.py` → `Event` |
| EventSource | Provenance: woher ein Event kam (`source_adapter`+`external_id` unique) | `backend/app/models.py` → `EventSource` |
| Dedup-Key | `dedup_key` auf `Event` = Cross-Source-Zusammenführung gleicher Events (1 Event : N Sources) | `backend/app/ingest/dedup.py` |
| RawEventRecord / SourceAdapter | Adapter-Output-DTO + Vertrag `fetch(scope) -> Sequence[RawEventRecord]` | `backend/app/ingest/types.py`, `base.py` |
| GeoScope | konfigurierbares Such-/Filter-Fenster (Default Mainfranken) + IT-Keyword-Gate | `backend/app/ingest/types.py` |
| FeedSource (Feed) | laufzeit-registrierte ICS/RSS-Quelle (DB statt Code, `enabled` = Sichtbarkeit im Lauf) | `backend/app/models.py` → `FeedSource` |
| Bookmark | von einem User gemerktes Event (`(user_id, event_id)` unique) | `backend/app/models.py` → `Bookmark` |
| topic_weights / intent_weights | LLM-Scores je Event, `{slug:int}` (Summe 100/Achse) | `backend/app/enrichment/score.py` |
| attendee_count / RSVP | Beliebtheits-Signal aus Quell-RSVP (Luma guest_count, Meetup „going") | `backend/app/enrichment/attendance.py` |
| useEvents | Composable: reaktiver Events-State (Filter, Pagination, camel↔snake, Fixture-Fallback) | `frontend/src/composables/useEvents.js` |
| Views | Landing · Dashboard · Profile · Kalender (W/M/J) · Karte (Leaflet-Pins) | `frontend/src/views/` |

## Dev Environment
- **Backend (Docker):** `cd backend && cp .env.example .env && docker compose up --build` → API `http://localhost:8000` (Swagger `/docs`), Postgres+PostGIS `:5432`.
- **Backend (ohne Docker):** Postgres bereitstellen, dann `backend/.venv/bin/uvicorn app.main:app --reload` (DATABASE_URL=localhost; SQLite-Fallback via `.env` möglich).
- **Frontend:** `cd frontend && npm install && npm run dev` → `http://localhost:5173` (Vite-Proxy `/api` → `:8000`).
- **Ports:** Frontend 5173 · API 8000 · Postgres 5432.
- **Ingest-CLI:** `python -m app.ingest [run|list|geocode|score|attendance]` (run=fetch+upsert, `--dry-run`/`--source`/`--radius-km`; score/attendance brauchen `ANTHROPIC_API_KEY` bzw. laufen ohne Key graceful).
- **Schema:** `create_all` beim Startup (kein Alembic; kommt mit PostGIS in Slice 3). **OAuth** gegen `.env`-Platzhalter; echter Login erst mit Google-Client-ID/Secret in `backend/.env`.

<!-- /quickref -->

---

## Architecture

### Stack (gelockt)
- **Frontend:** Vue 3 + Vite, `vue-router`, plain scoped CSS, Leaflet (Karte). Einstieg `frontend/src/main.js`.
- **Backend:** FastAPI + SQLModel, Authlib (Google OAuth), httpx, Anthropic SDK (Scoring). Einstieg `backend/app/main.py`.
- **DB:** PostgreSQL 16 + PostGIS (`postgis/postgis:16-3.4`). Laufzeitdaten im Named-Volume `pgdata` (nicht im Repo). Schema-Source-of-Truth = `backend/app/models.py`. SQLite-Fallback für Tests/lokal.

### Auth-Flow (Google OAuth, Authorization-Code)
1. `GET /api/auth/google/login` → `authorize_redirect` zu Google.
2. `GET /api/auth/google/callback` → Token-Tausch, User-Upsert per `google_sub`, leeres Profile, **httpOnly-Session-Cookie** (`user_id`) → Redirect `FRONTEND_URL/dashboard`.
3. `GET /api/auth/me` (→ `UserOut`) liefert User oder 401; `POST /api/auth/logout` leert die Session.
4. **Startup-Secrets-Guard** (`main.py`): warnt in Dev / **fail-fast in Production**, wenn `session_secret`/Google-Creds noch Dev-Defaults sind.

### Datenmodell (`backend/app/models.py`)
- `User` (`users`): `id, google_sub (unique), email, display_name, avatar_url, created_at`.
- `Profile` (`profiles`): `user_id (FK unique), interests[]/expertise[] (JSON), home_label/lat/lng, radius_km`. 1:1 zu User.
- `Event` (`events`): kanonische Felder (`title…language`) + Geo (`lat/lng` als floats, **noch kein** PostGIS-Geometry) + **Scoring** (`topic_weights/intent_weights (JSON), score_confidence, score_model, scored_text_hash`) + **Attendance** (`attendee_count, attendance_source, attendance_checked_at`) + **Dedup** (`dedup_key`, indexiert).
- `EventSource` (`event_sources`): Provenance — `event_id (FK), source_adapter, external_id, source_url, fetched_at, origin_type (scrape|feed|api|organizer|crowd), trust_tier (1=hoch…3=niedrig), raw_payload (JSON)`. **Unique `(source_adapter, external_id)`** = idempotenter Upsert-Key.
- `FeedSource` (`feed_sources`): `name, type (ics|rss), url (unique), organizer, tags[], default_city, trust_tier, broad, enabled, created_at, created_by`.
- `Bookmark` (`bookmarks`): `user_id (FK), event_id (FK), created_at`. **Unique `(user_id, event_id)`**.
- Zeit-Util: `app/_time.py` `utcnow()` ist die *eine* UTC-Quelle für Default-Timestamps.

### API
| Route | Methode | Auth | Zweck |
|-------|---------|------|-------|
| `/api/health` | GET | – | Healthcheck |
| `/api/auth/google/login` · `/callback` | GET | – | OAuth starten / Callback (Cookie setzen) |
| `/api/auth/logout` | POST | – | Session leeren |
| `/api/auth/me` | GET | ✅ | aktueller User (`UserOut`) |
| `/api/profile` | GET/PUT | ✅ | Profil lesen/schreiben (PUT geocodet `home_label` bei Änderung) |
| `/api/events` | GET | – | Event-Suche (`q`, `city`, `tag[]`, `date_from`, `date_to`, `is_online`, `upcoming`, `sort=start`, `limit`≤100, `offset`) → `{total, items}` |
| `/api/events/{id}` | GET | – | Einzel-Event inkl. Provenance (`sources[]`) |
| `/api/bookmarks` | GET | ✅ | gemerkte Events (soonest first) |
| `/api/bookmarks/{event_id}` | POST/DELETE | ✅ | merken/entfernen (idempotent, 204) |
| `/api/feeds` | GET/POST | ✅ | Feeds listen / registrieren (POST validiert URL + `type` ics\|rss, 201) |
| `/api/feeds/{feed_id}` | DELETE | ✅ | Feed entfernen (idempotent, 204) |

> **Kein Geo-Query-Filter (`radius`/`lat`/`lng`) auf `/api/events`.** Geografische Filterung passiert **beim Ingest** über `GeoScope` (Haversine-Radius/PLZ/Stadt, `filters.passes_geo`). Ein räumlicher Umkreis-Query auf der API ist ein Slice-3-Thema (PostGIS-Geometry + Alembic).

### Ingestion (`backend/app/ingest/`)
- **CLI** `python -m app.ingest`:
  - `run` — alle (oder `--source NAME`) Adapter fetchen → filtern → upserten. `--dry-run` (In-Memory-SQLite), `--geocode`, `--radius-km`, `--center lat,lng`.
  - `list` — alle registrierten Adapter (Code + Config-Feeds + enabled DB-Feeds).
  - `geocode` — fehlende `lat/lng` per Nominatim nachfüllen (idempotent, ≥1 req/s, gecacht).
  - `score` — LLM-Gewichtung (`--all` re-scort, `--limit N`).
  - `attendance` — RSVP/Attendee-Counts (`--all` re-checkt, `--limit N`).
- **Quellen (≈13 registriert):** 6 Code-Adapter — `meetup`, `eventbrite_wue` (broad), `thws` (broad), `thws_fiw`, `aiweek` (AI Week Mainfranken, IT-native), `zdi_gruenderzentren` (ICS) — plus 7 Config-Feeds in `feeds.yaml` (4 Meetup-ICS, `frizz_wuerzburg`, `nerd2nerd`, `uni_wuerzburg`, alle broad) plus laufzeit-registrierte DB-`FeedSource`s.
- **`broad`-Flag:** broad-Quellen (gemischte Stadtkalender) durchlaufen das IT-Keyword-Gate (`GeoScope.keywords`, hochpräzise deutsche IT-Begriffe); IT-native Quellen (Meetup, THWS-FIW, AI Week) überspringen es, damit Events mit unauffälligem Titel nicht rausfallen.

### Enrichment (`backend/app/enrichment/`)
- **LLM-Scoring** (`score.py`): gewichtet jedes Event auf Topic- und Intent-Achsen (`{slug:int}`, Summe 100), Taxonomie in `taxonomy.py`. Modell **Claude Haiku 4.5** (`score_model`, override via `SCORE_MODEL`); leerer `ANTHROPIC_API_KEY` ⇒ Scoring deaktiviert, App läuft weiter mit leeren Weights. Idempotent über `scored_text_hash` (re-scort nur bei Textänderung).
- **Attendance** (`attendance.py`): realer Attendee-Count aus den RSVP-Zahlen der Quelle — **Luma** `guest_count` (public, kein Key) und **Meetup** „going" (bevorzugt aus dem bereits gescrapten `EventSource.raw_payload`, sonst GraphQL hinter `MEETUP_API_KEY`).
- **Geocoding** (`app/geocode.py`): Nominatim (identifizierende UA, ≥1 req/s, per-Query-Cache). Erwartete Fehler (Netz/HTTP/Decode) werden geloggt + ergeben keine Koordinaten; nur `lat IS NULL`-Events werden angefasst (idempotent).

## Active Patterns
- **Same-origin im Dev über Vite-Proxy:** Frontend ruft `/api/...` relativ; `credentials: 'include'` (`frontend/src/api.js`). Kein CORS-Tanz.
- **useEvents als Daten-Layer:** ein Composable für reaktiven Events-State (Filter/Pagination, camel↔snake-Mapping, Fixture-Fallback wenn API leer) — alle Views konsumieren denselben.
- **Quell-agnostisches Adapter-Pattern:** Kern kennt nie eine Quelle direkt; Adapter mappen Roh-Felder auf `RawEventRecord`, Kern filtert + upsertet. Geteilte Helfer: `adapters/_normalize.py` (Datum/TZ + Text/Geo), `adapters/_fetch.py` (`fetch_pages_deduped`). Referenz: Vault `patterns/data-integration/connector-architecture.md`.
- **Idempotenter Upsert per `(source_adapter, external_id)`:** Re-Runs duplizieren nie; Fallback `stable_external_id()` = `sha256(source_url|title|start)`.
- **Cross-Source-Dedup (`dedup_key`):** dasselbe reale Event aus mehreren Quellen wird zu *einem* `Event` mit mehreren `EventSource`-Rows zusammengeführt; das Frontend zeigt die Quellen-Reconciliation.
- **Named-Logger:** Web-Schicht-Logger `eventradar.*` werden im `main.py`-Lifespan (`_configure_logging`) einheitlich konfiguriert (sonst verschluckt uvicorn die INFO-Zeilen).

## Known Pitfalls
- **`docker compose` (Plugin-Form)** nötig; Docker-Daemon muss laufen.
- **OAuth braucht echte Creds:** mit Platzhaltern startet alles, der Login-Klick scheitert aber am Token-Tausch (400). Redirect-URI `http://localhost:8000/api/auth/google/callback` in der Google Console autorisieren. `backend/.env` ist gitignored.
- **`lat`/`lng` sind floats, kein PostGIS-Geometry (Stand Slice 2):** bewusst, damit der SQLite-Testpfad ohne PostGIS läuft. Geometry-Spalte + räumlicher Query + Alembic kommen in Slice 3.
- **Saison-Quellen liefern leer:** jährliche Festivals (AI Week, Barcamps) sind außerhalb ihres Fensters leer — der Lauf wertet das als Info, nicht als Fehler.
- **Scoring/Attendance ohne Key:** ohne `ANTHROPIC_API_KEY` bleibt Scoring leer (Frontend zeigt „geschätzt"/Placeholder); Attendance ohne `MEETUP_API_KEY` nutzt nur Luma + bereits gescrapte Meetup-Counts.
