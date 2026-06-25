# Plan: Event Radar — Vertikaler Slice 2 (Ingestion-Fundament)

**Ziel:** Erste echte Events automatisiert ins System holen — und dabei das **quell-agnostische
Adapter-Pattern** etablieren, auf dem alle weiteren Quellen aufsetzen. Erste Quelle ist der
**Playwright-Umkreis-Scraper** (ROADMAP-Entscheidung). Erprobt wird der Vertrag an drei
Adaptern unterschiedlicher Render-Klasse: static HTML, JSON-im-HTML, echte SPA.

**Stack (gelockt):** FastAPI + PostgreSQL/PostGIS (`backend/`) · Redis (Queue) · Playwright
(headless) · Claude Haiku (erst Slice 4). Aufbauend auf Slice 1 (User/Profile, docker-compose).

**Referenzen:**
- `documentation/features/event-sources-mainfranken.md` — Quellen-Katalog + `RawEventRecord`-Zielschema
- `documentation/ROADMAP.md` — Slice-2-Scope und Reihenfolge-Entscheidung
- Vault `patterns/data-integration/connector-architecture.md` — Adapter/Provenance/Dedup-Pattern

**Scope-Grenze:** Nur Ingestion bis in den kanonischen Store. **Kein** Frontend-Display (Slice 3),
**kein** Geocoding/LLM-Scoring (Slice 4), **keine** cross-source-Dedup (Slice 5). Default-Geo-Scope
fix auf Mainfranken, aber als Config-Parameter angelegt.

---

## Offene Design-Entscheidungen (vor/zu Beginn klären)

- [ ] **Scrape vs. Partner-Feed bei ZDI:** ZDI (Gründerzentren-Portal #1) ist Projekt-Eigner UND
  beste Quelle (ICS-Export). Empfehlung: ZDI **nicht** in Slice 2 scrapen, sondern als
  Feed/Partner in Slice 5 — Slice 2 bleibt reiner Scraper-Beweis an #4/#5/#7. (mit Lars bestätigen)
- [ ] **Worker-Trigger:** APScheduler im API-Prozess (einfach) vs. eigener Worker-Container +
  Redis-Queue (sauberer, Haus-Doktrin „entkoppelter Worker"). Empfehlung: eigener Worker-Container,
  Redis als Queue — passt zum gelockten Stack und zu Slice 5/7.
- [ ] **`external_id`-Strategie wenn Quelle keine stabile ID liefert:** `sha256(source_url|title|start)`
  als Fallback (im Katalog-Schema vorgesehen) — bestätigen.

---

## Phase A — Datenmodell & Schema (`backend/`)  ·  ✅ erledigt

- [x] `Event` (kanonisch) als SQLModel — Felder aus `RawEventRecord` (Titel, start/end mit TZ,
  Beschreibung, is_online, venue/address/city/postal_code, lat/lng, organizer, tags (JSON), url,
  image_url, price, language). **lat/lng als floats** (nicht PostGIS-`Geometry`) — siehe Abweichung.
- [x] `EventSource` (Provenance) — `source_adapter, external_id, source_url, fetched_at,
  raw_payload (JSON), origin_type, trust_tier`; FK auf `Event`
- [x] **Unique-Constraint** `(source_adapter, external_id)` → trägt idempotenten Upsert
- [x] Pydantic-DTO `RawEventRecord` (Adapter-Output, entkoppelt vom DB-Modell) + `stable_external_id()`
- [~] ~~Alembic-Migration~~ **auf Slice 3 verschoben** (zusammen mit PostGIS-Geometry; `create_all`
  bleibt für Slice 2). Grund: hält SQLite-Testpfad intakt, vermeidet doppelte Migration.

## Phase B — Adapter-Vertrag & Ingestion-Kern  ·  ✅ erledigt

- [x] `SourceAdapter`-Protokoll (`base.py`): `name`, `broad`, `async fetch(scope) -> Sequence[RawEventRecord]`
- [x] `GeoScope`-Config (`types.py`) + Scope aus Settings (`config.py`/`core.default_scope`):
  `center`, `radius_km`, `keywords[]`, `cities[]`, **Default = Mainfranken**, per `.env` überschreibbar
- [x] **Keyword-/Geo-Filter als Kern-Stufe** (`filters.py`, nicht pro Adapter): Haversine-Umkreis +
  City-Whitelist + (nur bei `broad`-Quellen) Titel/Tags-Keyword-Gate; Begründung pro Drop fürs Log
- [x] **Idempotenter Upsert** per `(source_adapter, external_id)` (`core.upsert_event`) — Re-Runs updaten in place
- [x] Ingestion-Run (`core.run_ingestion`): Registry → `fetch()` → Filter → Upsert; Fehler pro Quelle
  UND pro Record isoliert; strukturierter `IngestionReport` (found/kept/new/updated/error) + Logs
- [x] **Saison-Toleranz:** leere Quelle = Log-Info, kein Fehler
- [x] Smoke verifiziert: Geo-Drop, Keyword-Drop, Fehler-Isolation, Upsert-Idempotenz (Lauf 2 → 0 new / 2 updated)

## Phase C — Die drei Erst-Adapter (Render-Klassen erproben)

- [ ] **`thws_fiw`** (static HTML) — https://fiw.thws.de/termine/ · httpx + selectolax/BS4,
  Akkordeon-Blöcke parsen (Datum/Titel/Venue). Einfachster Fall, deckt Schweinfurt mit ab.
- [ ] **`eventbrite_wue`** (static Cards) — Science&Tech + KI-Listing · httpx, `?page=N`-Pagination,
  defensiv crawlen (ToS, moderate Frequenz, User-Agent). Event-Cards aus Markup.
- [ ] **`meetup`** (JSON-im-HTML) — Würzburg DATA&ANALYTICS + Analytics Pioneers ·
  `__NEXT_DATA__`-JSON aus initialem HTML parsen (kein Playwright nötig); Gruppen-Liste konfigurierbar
- [ ] **Playwright-Harness** als wiederverwendbare Basis für künftige echte SPA-Quellen
  (IHK/Sweap, AI Week, baiosphere — *nicht* in Slice 2 umgesetzt, nur Harness vorbereiten):
  headless Browser, realistischer UA, „auf Netzwerk-Response/Selector warten"-Helper

## Phase D — Worker, Schedule & Persistenz

- [ ] Worker-Container in `docker-compose.yml` (api + postgres/postgis + redis + **worker**)
- [ ] Periodischer Trigger (APScheduler oder Redis-Queue-Job) — konfigurierbares Intervall,
  niedrige Frequenz wg. Bot-Schutz (Meetup/Eventbrite)
- [ ] Manueller Trigger für Tests: `POST /api/admin/ingest` (auth-pflichtig) oder CLI
  `python -m app.ingest run [--source <name>]`
- [ ] `GET /api/events` (einfache Liste, ungefiltert/paginiert) — **nur als Verifikations-Endpoint**
  für Slice 2 (echtes Display/Filter kommt in Slice 3)

## Phase E — Tests & Verifikation

- [ ] Adapter-Unit-Tests gegen **gespeicherte HTML/JSON-Fixtures** (kein Live-Netz im CI) —
  je Adapter ein Fixture mit ≥1 echtem Event aus der Recherche
- [ ] Upsert-Idempotenz-Test: zweimaliger Lauf desselben Records → genau 1 Event-Row
- [ ] Filter-Test: Nicht-IT-/Nicht-Mainfranken-Record wird verworfen
- [ ] Smoke: realer Ingestion-Lauf gegen die 3 Live-Quellen → Events landen in Postgres,
  `GET /api/events` liefert sie (lokal, kein x1pro)

---

## Abschluss-Aktionen (bei Slice-2-Abschluss)

- In `documentation/technical/README.md` einfließen lassen: Adapter-Architektur (Protokoll,
  Registry, Filter-Stufe, Upsert-Key), Datenmodell `Event`/`EventSource`, Worker/Schedule-Setup,
  Dev-Befehle (Ingest-CLI, compose-Services).
- `documentation/features/event-sources-mainfranken.md` aktualisieren: Render-/Feed-Annahmen,
  die sich beim echten Scrape bestätigt/widerlegt haben (v.a. #14/#15 Render, #1 `genIcs`).
- Offene To-dos des Katalogs, die Slice 2 nicht löst (GRIBS-URL, IHK-Sweap-JSON, baiosphere),
  in den ROADMAP-/Slice-5-Kontext überführen.
- Diesen Plan löschen, Lessons in Tech-Doku/Vault übertragen.
