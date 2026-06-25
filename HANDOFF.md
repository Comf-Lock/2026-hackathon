---
type: handoff
vorhaben: 2026-hackathon
working_directory: /Users/larskohlmorgen/_clients/zdi/projects/coding/2026-hackathon/agent-1
created: 2026-06-25
last_updated: 2026-06-25-slice2-phaseB-dashboard
schema_version: "0.4"
status: architecture · slice2-phaseB · dashboard
---

# Handoff — 2026-hackathon

> **Adressat:** nächste Session. Bootstrap: `current_task` → `read_first_critical`, dann loslegen.

## current_task

Event Radar — Slice 2 (Ingestion-Fundament). Phase A (Event/EventSource-Modell + RawEventRecord-Adapter-Vertrag + GeoScope) und Phase B (SourceAdapter-Protokoll, Registry, zentrale Filter-Stufe Haversine+City+Keyword, idempotenter Upsert, run_ingestion mit Fehler-Isolation + IngestionReport + Saison-Toleranz) sind gebaut & smoke-verifiziert. Parallel: Frontend hat jetzt eine Login-Index-Seite (/) und ein auth-gegatetes Mainfranken-Dashboard (/dashboard, aus prototype/dashboard.html, vue-router-Guard), Backend redirectet nach Login auf /dashboard. PR #3 (Phase A) ist in master; PR #5 (Phase B + Dashboard) offen gegen master. Stack: Vue3+Vite / FastAPI+Postgres(PostGIS später) / lokal. **Nächster Schritt:** Slice 2 Phase C — die drei Live-Adapter bauen (thws_fiw static HTML, eventbrite_wue static Cards, meetup __NEXT_DATA__-JSON), die echte Events statt Demo-Daten liefern und sich in der Registry registrieren; dazu HTTP-Fetch + Parsing + Fixtures.

## active_plans

*(keine)*

## read_first_critical

1. *(diese Datei)*

## open_questions

- Google-OAuth-Client (Client-ID/Secret + Redirect-URIs) — von Lars anzulegen/autorisieren
- Testserver-Ziel für Slice-1-Deploy: x1pro? welche Domain/Subdomain?
- Mockup-Richtung: simpel (frontend/index.html) vs. dicht (frontend/dashboard.html) — Lars-Feedback offen

> **Kaltzone:** decisions_made, Iteration History, Backlog und Landmarks liegen unterhalb dieses Markers — per `Read` vollständig nachladen bei Bedarf.
<!-- /hot-context -->

## decisions_made

- **2026-06-25 · Slice-2-Doppelbau-Konsolidierung → agent-1-Linie + Rosinen (Lars bestätigt).**
  Befund: agent-1 (master + Phase-C-PR #8) und agent-2 (Branch, nicht gemergt) haben Slice-2-Ingestion
  parallel doppelt gebaut (agent-2 vor PR #5 abgezweigt). master gehört der agent-1-Linie; mein Phase C
  hat 3 Adapter (thws_fiw/eventbrite_wue/meetup) vs. agent-2 nur 1 (eventbrite via Playwright).
  **Entscheidung:** master + PR #8 bleiben Basis. Aus agent-2 nur die einzigartigen Rosinen cherry-picken:
  (1) `browser.py` Playwright-Harness, (2) Geo-Verfeinerung Radius 75km + `postal_prefixes` (97/63)-Fallback,
  (3) free-event price-fix. agent-2s Duplikat-Fundament (core/filter/eventbrite/cli/events) wird verworfen.
  Bewusst NICHT übernommen: agent-2s strikte „geo-blank = drop"-Philosophie (würde meine trusted
  THWS-Events mit city=None fälschlich verwerfen). Root-Cause: zwei Agents auf denselben Slice (Orchestrierung).

## Iteration History

- **2026-06-25** · event-radar-slice1 · Onboarding, Stack-Lock (vue-vite+fastapi-postgres), Event-Radar-Rebrand+Logo, Architektur+Connector-Vault-Doc, Slice-1-Plan
- **2026-06-25** · slice2-phaseB-dashboard · Slice-2 Phase A+B (Ingestion-Kern) gebaut, Roadmap+Quellenkatalog (28 Quellen) geschrieben, Login-Index + Mainfranken-Dashboard hinter Auth; PR #3 gemergt, PR #5 offen

## backlog

- Slice 2 Phase C: thws_fiw / eventbrite_wue / meetup Adapter (Live-HTTP + Parsing + Fixtures)
- Slice 2 Phase D: Worker-Container + Schedule + GET /api/events Verifikations-Endpoint
- Slice 2 Phase E: Adapter-Tests gegen Fixtures, Upsert-Idempotenz, Filter, Live-Smoke
## landmarks

*(keine)*

## inbox

*(leer)*
