# Plan — Agent-4: Dummy-Events → echte DB-Events (Integration & Verifikation)

> Branch: `agent/agent-4` · Owner: Integrations-/Verifikations-Agent
> Brief: `_scrape/processed/task-integration-real-events.md`
> Datenkette: **Postgres/SQLite → `GET /api/events` (Agent-3) → `useEventSearch` (Agent-1) → Cards im UI**

## Status

- [x] **Phase 1 — Vorarbeit (unblockiert)** — Datenkette verifiziert, Contract studiert, Mapping-Plan erstellt
- [ ] **Phase 2 — finaler Switch** — GATED, wartet auf Master-Go (Agent-1 + Agent-3 auf master)

---

## Phase 1 — Befunde (Stand 2026-06-25)

### 1. Datenkette von unten — verifiziert, weicht vom Brief ab

| Erwartung (Brief) | Realität (verifiziert) |
|---|---|
| Postgres `backend-db-1` :5432 | **kein Postgres** — Docker-Socket gehört larskohlmorgen (`permission denied`); Dev läuft per **SQLite-Fallback pro Worktree** (HANDOFF) |
| 3 Events: Aschaffenburg, Miltenberg, Sulzfeld | **nicht auffindbar** — kein solcher Seed in irgendeiner DB |
| — | `master/backend/eventradar.db`: **0 Events** (API auf master liefert aktuell `[]`) |
| — | `agent-3/backend/eventradar_dev.db`: **8 echte Events** (Würzburg, Eventbrite-Scraper) — leben nur in agent-3s Worktree |

### 2. API-Contract — `GET /api/events` (master `backend/app/events.py`) weicht vom Brief ab

**Brief behauptet** Filter `q,city,tag,date_from,date_to,is_online` + reiches `EventOut`.
**Tatsächlich gemergt:**

- Query-Params: **nur `limit`, `offset`** — KEINE Filter.
- Response: `{ total, limit, offset, items[] }`.
- `EventOut` = `id, title, start, end, is_online, city, venue_name, organizer, url, image_url` (10 Felder).
- **Im Model vorhanden, aber von `EventOut` NICHT exponiert:** `description, address, postal_code, lat, lng, tags[], price, language`.

### 3. Mapping-Plan `EventOut` → Dummy-Card (`DashboardView.vue`)

Die Dummy-Card ist tief an **erfundene Demo-Felder** gekoppelt, die der Contract nicht liefert.
Rohe Daten einspeisen → **Crash** bei `dominant(e.intent)`, `e.intent.deep`, `e.sources.length`,
`pinStyle()` (Map), Kalender-Filter `e.day === d`.

| Card-Feld | Quelle aus `EventOut` | Entscheidung |
|---|---|---|
| `title` | `title` | **direkt** |
| `tags` | — (Model hat `tags`, EventOut nicht) | Default `[]`; besser: Agent-3 bittet `tags` in EventOut aufzunehmen |
| `date` | `start` | **ableiten** (`DD. Mon YYYY, HH:MM`) |
| `day` (Kalender) | `start` | **ableiten** (Tag d. Monats) |
| `place` | `venue_name` + `city` | **ableiten** (`venue_name, city`, Fallbacks) |
| Online-Badge | `is_online` | **direkt** (neu, ersetzt sinnvoll `dist`) |
| Details-Link | `url` | **wire** „Details anzeigen" → `url` |
| `image_url` | `image_url` | optional (aktuell ungenutzt) |
| `rating`, `reviews` | — | **weglassen** (keine Datenquelle) → Block ausblenden |
| `dist` (km) | — (kein User-Geo, kein Distanz-Calc) | **weglassen** (Slice 3/4) |
| `size` (Teilnehmer) | — | **weglassen** |
| `price` | — (Model hat `price`, EventOut nicht) | weglassen / EventOut erweitern |
| `intent` (deep/recruit/vendor/network) | — (keine Klassifikation) | **neutralisieren** — Card-Block ausblenden; Kalender/Map mit neutraler Default-Farbe; alle `dominant()/intentColor()/pinStyle()` guarden |
| `sources` (Provenance-Abgleich) | — (EventOut ohne Provenance) | **weglassen / minimal** aus `organizer` ableiten; Block ausblenden bei `[]` |
| `blindspot` | — (hängt an `sources`) | weglassen |

**Leitlinie:** Echtes `EventOut` trägt eine **reduzierte, ehrliche Card** (Titel, Datum, Ort, Online-Badge,
Link). Die Analytics-Felder (intent, sources, rating, dist, size) sind Demo-Fixtures ohne Backing —
entweder droppen oder so guarden, dass nichts crasht. Kalender/Map brauchen Neutral-Fallbacks.

---

## BLOCKER / Entscheidungen für den Master

1. **`useEventSearch.js` + `SearchMask.vue` (Agent-1) existieren auf KEINEM Branch** (auch nicht
   agent/agent-1) → Phase 2 vollständig blockiert.
2. **Endpoint hat keine Filter** → SearchMask kann nicht serverseitig filtern. Entweder Agent-3
   erweitert `/api/events` (sein Eigentum) ODER Filterung clientseitig über die gefetchte Liste.
   DoD „Filtern trifft die API sichtbar" sonst nicht erfüllbar.
3. **master-DB ist leer** → für eine E2E-Demo muss master geseedet werden (Scraper-Run/Seed),
   sonst liefert die API `[]`. Die 8 realen Events liegen nur in agent-3s Worktree-DB.
4. **`EventOut` lässt `tags/description/price/lat/lng` weg**, obwohl das Model sie hat — trivial für
   Agent-3 nachzuziehen, würde die Card deutlich aufwerten.
5. **Intent/Sources-UI:** behalten mit synthetischen Defaults oder strippen? Produktentscheidung.

## Phase 2 — nach Go (NICHT vor Master-Signal committen)
- [ ] Branch auf frischen master rebasen/mergen
- [ ] `const events = [...]` in `DashboardView.vue` (+ evtl. `LandingView.vue`) durch `useEventSearch()` ersetzen (importieren, nicht neu schreiben)
- [ ] Card/Kalender/Map gegen fehlende Felder guarden (s. Mapping-Tabelle)
- [ ] E2E verifizieren: `/dashboard` zeigt echte DB-Events; Filter wirkt; Leer-/Fehlerzustand sauber
- [ ] Beweis im Journal (curl-Output + gerenderte Titel)

## Abschluss-Aktionen (bei Plan-Ende)
- Mapping-Tabelle + „reduzierte Card"-Prinzip nach `documentation/technical/README.md`.
- Contract-Realität (`/api/events` nur limit/offset, EventOut-Felder) in die Nomenklatur-Tabelle.
