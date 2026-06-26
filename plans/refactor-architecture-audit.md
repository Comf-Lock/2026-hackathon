# Plan — Architektur-Refactor (aus Audit 2026-06-26)

> Quelle: Architektur-Audit der Code-Basis (Backend ~1.860 LOC / Frontend ~1.656 LOC), gebaut von
> 4 parallelen Agenten. Kern-Diagnose: **Konsolidierung, kein Redesign.** Jeder Agent hat dieselbe
> Querschnitts-Infra neu erfunden; die Web-Schicht ist flach (keine Service/Repo-Ebene); die
> Ingest-Pipeline ist bereits vorbildlich und bleibt unangetastet.
>
> **Eigentums-Hinweis:** Viele Befunde liegen in fremdem Agenten-Eigentum (`EventCard.vue`,
> `events.py`, `useEventSearch.js`, Adapter). Jeder ⚠️-Task **mit Master abstimmen**, bevor er
> angefasst wird — sonst Kollision mit parallelen Agenten. Tasks ohne ⚠️ sind unkritisch / agent-4-nah.

## Priorisierung (Impact × Aufwand)

- **P0** — höchster Hebel, deckt zusammen ~80 % der Befunde. Zuerst.
- **P1** — strukturelle Schulden, mittlerer Aufwand.
- **P2** — Quick Wins & Hygiene, klein und risikoarm.

---

## P0 — Konsolidierungs-Refactors (höchster Hebel)

### [ ] P0.1 ⚠️ Geteilte HTTP-Schicht (Backend) — killt Audit-Issue #2
HTTP-UA/Timeout/Client sind **5× dupliziert und driften** (Chrome 124/125/126).
- Neu: `backend/app/ingest/http.py` — *ein* `HEADERS`, *ein* `TIMEOUT`, *ein* `client()` + `fetch_text()`/`fetch_bytes()`.
- Migrieren: `adapters/ics.py:32`, `adapters/rss.py:24`, `ingest/feed_loader.py:40`, `ingest/browser.py:23`, `app/geocode.py` → alle auf das neue Modul. `adapters/_http.py:15` als Basis dort aufgehen lassen.
- Ergebnis: ~5 driftende Kopien weg, eine Anti-Bot-UA-Wahrheit.

### [ ] P0.2 ⚠️ Event-Form auf eine Quelle + Serialisierung aus dem Router (Backend) — Issue #1, #5
Kanonische Event-Form **4× von Hand** gepflegt: `models.Event` / `types.RawEventRecord` /
`events.EventOut` / `core._CANONICAL_FIELDS` (`core.py:66`).
- Neu: `backend/app/schemas.py` (EventOut, SourceOut, EventSearchResponse) + `backend/app/events_service.py` (`sources_for`, `to_event_out`, Such-/Pagination-Logik).
- `events.py` und `bookmarks.py` importieren beide aus dem Service statt Router→Router (`bookmarks.py:15`).
- `core._CANONICAL_FIELDS` aus einer Quelle ableiten (z. B. `RawEventRecord.model_fields ∩ Event`), nicht als handgepflegte String-Liste.

### [ ] P0.3 Ein Frontend-Events-Daten-Layer — Issue #4 + 4 Fehler-Strategien
Zwei getrennte `/api/events`-Clients: `useEventSearch.js:16` (limit=20) vs `CalendarView.vue:39`
(eigener Param-Builder + eigene Pagination). *Letzteres ist agent-4-Code → frei umbaubar.*
- `useEventSearch` zu generischem `useEvents` erweitern: `toQuery` + Fetch + Pagination (range/limit-Parameter) + `error` + Fixture-Fallback, **eine** Implementierung.
- Konsumenten: `LandingView`, `DashboardView`, `CalendarView`. CalendarViews `load()`-Schleife (`CalendarView.vue:30-56`) ersetzen.
- ⚠️ `useEventSearch.js` gehört Agent-1 → Erweiterung mit Master abstimmen; CalendarView-Anpassung ist agent-4.

### [ ] P0.4 ⚠️ DashboardView entschlacken — Issue #3
256-LOC-God-Component; schluckt Fehler still; toter `usingDemo`-Pfad.
- **Bug zuerst:** `usingDemo` (`DashboardView.vue:28,32`) existiert nicht in `useEventSearch` → `showDemoHint` permanent `false`. Auf `error` umstellen und Fehler im UI sichtbar machen (`:42-44,52-54` schlucken Exceptions).
- Redundantes `fetchMe()` (`:88`) + Profil-Redirect raus → Auth gehört allein dem Router-Guard.
- `MiniEventRow`-Komponente extrahieren (Markup `:185-188` ≈ `:194-197` byte-gleich).
- SearchMask-Binding auf `v-model` vereinheitlichen (wie Landing), `Object.assign`-Tanz (`:78-85`) entfernen.

---

## P1 — Strukturelle Schulden

### [ ] P1.1 ⚠️ Adapter-Registrierung explizit machen — Issue #6
Globaler mutierbarer Registry-State + reihenfolge-abhängiges Warm-up (`core.py:171-173`) +
Import-Zyklus `registry`↔`feed_loader` (lazy import `registry.py:46`).
- `get_adapters(session)` baut Code- + Config- + DB-Feeds **deterministisch in einem Call**.
- `_config_feeds_loaded`-Latch (`registry.py:44`) und das CLI-Warm-up (`__main__.py:128`) entfallen.

### [ ] P1.2 ⚠️ async/sync-Handler vereinheitlichen — Issue #7
`profile`/`auth` sind `async def` über **synchroner** `Session` → blockierendes IO auf dem Event-Loop.
Entweder konsequent `def` (wie events/bookmarks/feeds) oder echtes Async-DB. Pragmatisch: auf `def` vereinheitlichen, außer wo `await` nötig ist (`feeds.create_feed` bleibt async wg. `validate_feed`).

### [ ] P1.3 Backend-Logging + Fehler-Sichtbarkeit — Issue #9
- `geocode.py:19` schluckt alle Exceptions lautlos → schmaler Catch + Log.
- Named-Logger in der Web-Schicht einführen (Ingest hat es bereits vorbildlich).

### [ ] P1.4 ⚠️ Frontend-Display-Modul (TZ-sicher) — Teil Issue #8
Datum/Zeit/Monat/Ort-Formatierung in *ein* Modul auf der String-Slice-Basis aus
`calendarRange.js` (TZ-sicher). Entfernt 3× `MONTHS` (`calendarRange.js:14`, `EventCard.vue:20`,
`DashboardView.vue:57`), beide `new Date(iso)`-Formatter (`EventCard.vue:22`, `DashboardView.vue:58`)
und die 2 `place`-Varianten. ⚠️ `EventCard.vue` = Agent-3.

### [ ] P1.5 Auth-Redirect entdoppeln — Teil Issue #8
Redirect-Verantwortung allein in den Router-Guard (`router.js:23`); `ProfileView.vue:26` und
`DashboardView.vue:88` von Auth-Checks befreien.

---

## P2 — Quick Wins & Hygiene

- [ ] **Doku-Drift fixen:** `documentation/technical/README.md` API-Tabelle um `/api/events`, `/api/events/{id}`, `/api/feeds`, `/api/bookmarks` ergänzen; `last_verified` aktualisieren. *(agent-4-nah, unkritisch)*
- [ ] **`searchKit.js` löschen** (obsolete Re-Export-Indirektion) → Komponenten direkt importieren; split Import-Pfade vereinheitlichen.
- [ ] ⚠️ **CSS-Konsolidierung:** `.card`-Oberfläche (4×) + `.btn` (global + `EventCard.vue:166`) einmal in `style.css`; tote Variable `var(--txt)` (4 Stellen, nie definiert) entfernen.
- [ ] **`_utcnow()` entdoppeln** (`models.py:18`, `core.py:28`, inline `events.py:101`) → eine Quelle.
- [ ] **Datums-Helfer mergen:** `adapters/_dates.py` + `adapters/_normalize.py` (beide `BERLIN` + naive→Berlin) zusammenführen.
- [ ] **Dedup-while-fetch-Loop** (`meetup.py:98` ≡ `eventbrite_wue.py:137`) in eine Hilfsfunktion ziehen.
- [ ] **`/api/auth/me` `response_model`** geben (`auth.py:90` hand-gebautes Dict) → OpenAPI-Vertrag, kein stilles Drift.
- [ ] **Test-Hygiene:** doppelte `session`-Fixture (`conftest.py:39` vs `test_ingestion_smoke.py:44`) auflösen.
- [ ] **Packaging-Split:** Scraper-Deps (`playwright`/`bs4`/`icalendar`/`feedparser`) aus dem API-`requirements.txt` in `requirements-ingest.txt`.
- [ ] **Nav-Highlight-Bug:** `App.vue:29` markiert „Liste" aktiv auf `/profile` (Bedingung `route.name !== 'calendar'`).
- [ ] **Magic Numbers** in benannte Konstanten (Debounce 300, limit 20/100, radius 40, Page-Cap 10/1000).
- [ ] **Prod-Guard für Secrets:** Startup-Check, dass `session_secret`/Google-Creds nicht die Dev-Defaults sind (`config.py:17`).

---

## Reihenfolge-Empfehlung

1. **P0.4-Bug** (toter `usingDemo`/geschluckte Fehler) — kleinster Fix, sofort sichtbarer Effekt.
2. **P0.1** + **P0.2** (Backend-Konsolidierung) — unabhängig voneinander, gut parallelisierbar.
3. **P0.3** (Frontend-Events-Layer) — danach **P1.4/P1.5** (bauen darauf auf).
4. **P1.1** (Registry) — isoliert, jederzeit.
5. **P2** laufend als Mitnahme.

## Out of Scope
- Ingest-Pipeline-Architektur (types→base→adapters→registry→core→dedup) — bewusst **nicht** anfassen, ist das Vorbild. Nur die *Querschnitts-Helfer* darin konsolidieren (P0.1).
- Microservices-Aufspaltung — bei ~4.500 LOC Over-Engineering. Ingest ist die einzige spätere Service-Grenze.
- PostGIS-Geometriespalte / echter Radius-Query — eigenes Slice (3/4), nicht Teil dieses Refactors.

## Abschluss-Aktionen (bei Plan-Ende)
- Konsolidierte Module (`ingest/http.py`, `schemas.py`, `events_service.py`, Frontend-`useEvents` + Display-Modul) in `documentation/technical/README.md` aufnehmen.
- „Web-Schicht hat jetzt Service-Layer"-Pattern + „eine HTTP-/Datums-/Event-Form-Quelle" in die Active-Patterns-Sektion der Tech-Doku.
