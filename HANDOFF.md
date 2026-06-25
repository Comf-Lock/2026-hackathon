---
type: handoff
vorhaben: 2026-hackathon
working_directory: /Users/larskohlmorgen/_clients/zdi/projects/coding/2026-hackathon/master
created: 2026-06-25
last_updated: 2026-06-25-agent3-ingest-events-api
schema_version: "0.4"
status: event-radar · agent-3 · ingest-adapters + events-API DONE (awaiting master merge)
---

# Handoff — 2026-hackathon

> **Adressat:** nächste Session. Bootstrap: `current_task` → `read_first_critical`, dann loslegen.

## current_task

**Agent-3-Auftrag (Branch `agent/agent-3`): Daten-Fundament — ICS/RSS-Adapter + Events-Such-API — ABGESCHLOSSEN.**
Auftrag war `_scrape/processed/task-scraper-events-api.md`. Gebaut & getestet (15 pytest grün, live verifiziert):
- Adapter-Paket `backend/app/ingest/adapters/` (self-registern): 4 Meetup-ICS, ZDI genIcs (ID-Discovery + per-Event-ICS), FRIZZ-RSS. Helper `_normalize.py`.
- CLI `python -m app.ingest` (`--source/--dry-run/--radius-km/--center`), idempotenter Upsert verifiziert (8 new → 8 updated bei Re-Run).
- Events-Such-API `backend/app/events.py` nach FIX-Contract: `GET /api/events` ({total, items}, 18 EventOut-Felder, Filter q/city/tag/date_from/date_to/is_online, sort=start asc, upcoming-default, limit≤100/offset) + `GET /api/events/{id}`. In `main.py` eingehängt.
- `requirements.txt` += icalendar, feedparser.

**Nächster Schritt (Master-Agent):** Branch `agent/agent-3` nach `master` mergen (wie PR-Flow der Vorgänger-Agenten). Danach optional: weitere Quellen (Startbahn27/Region Mainfranken), Geo-Enrichment (Slice 4), Cross-Source-Dedup (Slice 5).

## active_plans

*(keine)*

## read_first_critical

1. *(diese Datei)*
2. `_scrape/processed/task-scraper-events-api.md` — der erfüllte Auftrag inkl. FIX-Contract
3. `backend/app/events.py` + `backend/app/ingest/adapters/` — die Deliverables

## open_questions

- Push/Merge: `agent/agent-3` ist lokal committet; Push nach origin + Merge nach master liegt beim Master-Agent (Branch-Protection-Flow A/PRs wie bisher).
- ZDI-Partnerfeed (Gesamtkalender statt per-Event-genIcs) früh mit ZDI klären — schlägt das ID-Discovery-Scraping.
- Google-OAuth-Client (Client-ID/Secret + Redirect-URIs) — von Lars anzulegen (slice-1 offen, nicht agent-3).

> **Kaltzone:** decisions_made, Iteration History, Backlog und Landmarks liegen unterhalb dieses Markers — per `Read` vollständig nachladen bei Bedarf.
<!-- /hot-context -->

## decisions_made

- **FRIZZ liest Event-Datum aus dem Item-Titel (`DD.MM.YYYY [HH:MM]`), nicht aus RSS-pubDate.** pubDate ist die Publikationszeit (oft jahrealt) → Events fielen sonst durch den upcoming-Filter (`start >= heute`). `parse_de_datetime()` + `prefer_title_date=True` (nur FRIZZ). pubDate bleibt Fallback.
- **FRIZZ nur via RSS, nicht zusätzlich via ICS.** Cross-Source-Dedup ist Slice 5; beide Feeds gleichzeitig zu ingesten gäbe doppelte Event-Rows derselben Veranstaltung (verschiedene `source_adapter` → verschiedene Events).
- **`--dry-run` läuft gegen eine In-Memory-SQLite** statt nur zu fetchen: voller Pipeline-Lauf (fetch→filter→upsert) → realistischer Report (found/kept/new), echte DB unangetastet.
- **Tag-Filter im Events-Endpoint Python-seitig** (nicht SQL): `Event.tags` ist JSON-Array, Membership ist nicht portabel über SQLite↔Postgres; bei regionalem Volumen ist Laden+Schneiden korrekt und billig.
- **Meetup `broad=False`, FRIZZ `broad=True`** (Keyword-Gate greift nur bei breiten Stadtkalendern). ZDI/Gründerzentren `trust_tier=1` (Institutions-Feed), Meetup 2, FRIZZ 3.

## Iteration History

- **2026-06-25** · event-radar-slice1 · Onboarding, Stack-Lock (vue-vite+fastapi-postgres), Event-Radar-Rebrand+Logo, Architektur+Connector-Vault-Doc, Slice-1-Plan
- **2026-06-25** · agent3-ingest-events-api · ICS/RSS-Adapter (Meetup×4, ZDI genIcs, FRIZZ) + CLI `python -m app.ingest` + Events-Such-API `GET /api/events` nach FIX-Contract + 15 pytest; live verifiziert (ZDI+FRIZZ liefern echte Events, Upsert idempotent). Commits ae681cc→0adeb6a auf `agent/agent-3`.

## backlog

- documentation/features/event-radar-architecture.md schreiben (inkl. Ingestion/Connector-Sektion, ref Vault patterns/data-integration/connector-architecture.md)
- documentation/technical/README.md mit Nomenklatur + Dev-Env füllen
- uncommittete Änderungen (Logo/Rename/frontend/config/plans) committen sobald Git-Flow geklärt
## landmarks

- `backend/app/ingest/adapters/ics.py` — `parse_ics()` (pure), `ICSFeedAdapter`, `ZdiGenIcsAdapter`, `_extract_genics_ids()`
- `backend/app/ingest/adapters/rss.py` — `parse_rss()` (pure), `RSSFeedAdapter` (FRIZZ, `prefer_title_date`)
- `backend/app/ingest/adapters/_normalize.py` — `to_aware`, `parse_de_datetime`, `detect_online`, `pick_city`, `extract_postal`
- `backend/app/ingest/__main__.py` — CLI (`python -m app.ingest`)
- `backend/app/events.py` — `GET /api/events` (+ `/{id}`), `EventOut`/`EventSearchResponse`
- `backend/tests/` — `test_adapters.py`, `test_events_api.py`, `conftest.py` (in-memory SQLite, StaticPool)
- Dev-Lauf: `DATABASE_URL="sqlite:///./eventradar_dev.db" python -m app.ingest` · Tests: `pytest` (aus `backend/`, venv `.venv`)

## inbox

*(leer)*
