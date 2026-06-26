---
type: handoff
vorhaben: 2026-hackathon
working_directory: /Users/larskohlmorgen/_clients/zdi/projects/coding/2026-hackathon/agent-1
created: 2026-06-25
last_updated: 2026-06-26-agent1-radius-search
schema_version: "0.4"
status: slice1-deployed · master-orchestration · agent1-radius-search-in-progress
---

# Handoff — 2026-hackathon

> **Adressat:** nächste Session. Bootstrap: `current_task` → `read_first_critical`, dann loslegen.

## current_task

agent/agent-1 · **Radius-Suche (Haversine) — Brief gelesen + auf origin/master @ 92ae5f3 rebased, Exploration fertig, Implementierung offen** (Rotation bei 248K vor Code-Start). Diese Session zuvor abgeschlossen & GEPUSHT (Master-PRs offen/teils gemergt): P1.1 Registry (gemergt), AI-Week-Adapter (gemergt PR#33), THWS uni-weiter Scraper (gepusht `79e43b5`; IHK = Playwright-Flag s. open_questions). FERTIGER PLAN für Radius (Details im Journal 2026-06-26 11:57): (1) neuer Helfer `backend/app/geo.py` mit `haversine_km(lat1,lng1,lat2,lng2)`; `ingest/filters.py` importiert ihn statt eigenem `_haversine_km` (keine 2. Distanz-Impl, Brief-Vorgabe). (2) `events_service.search_events`: optionale Params `lat/lng/radius_km` (nur zusammen aktiv) → Python-Postfilter wie der tag-Pfad (Events mit lat/lng ≤ radius behalten, Events OHNE Koordinaten AUSSCHLIESSEN, dann paginieren); ohne Radius unverändert. (3) `events.py`: Query-Params durchreichen. (4) Tests: in/out radius, no-coord ausgeschlossen, ohne Radius unverändert. (5) `SearchMask.vue`: Radius-Input (number 5–100, default 40) + dateFrom mit HEUTE vorausfüllen (dateTo leer). (6) `useEvents.js` toQuery: radius_km+lat/lng mitgeben; Zentrum eingeloggt=Profil home_lat/home_lng (/api/profile), sonst graceful (kein Zentrum→kein Radius-Filter). GRENZEN: nur events_service/events.py + geo.py + SearchMask.vue + useEvents.js — NICHT EventCard/eventDisplay (Agent-3), ProfileView/profile.py (Agent-3), feeds.yaml (Agent-5), andere Adapter. **Nächster Schritt:** Plan (1)–(6) umsetzen, `pytest` + `vite build` grün, committen (`feat: radius search (haversine) + searchmask radius input`), Journal, push origin agent/agent-1, Brief `task-radius-search.md` → `_scrape/processed/`, Master macht PR.

## active_plans

- name: event-radar-slice-1
  path: plans/event-radar-slice-1.md
  status: done
- name: event-radar-slice-2
  path: plans/event-radar-slice-2.md
  status: in_progress

> Hinweis: slice-1 deployed/gemergt (PR#3); Datei bewusst NICHT gelöscht (Agent-Branches referenzieren sie, aktive Parallelarbeit). slice-2 wird von Agent-3 (Ingest/Scraper) fortgeführt.

## read_first_critical

1. *(diese Datei)*

## open_questions

- Google-OAuth-Client (Client-ID/Secret + Redirect-URIs) — Lars legt ihn an, sobald Login lokal getestet werden soll (Code baut gegen .env-Platzhalter, nicht blockierend)
- Versioniertes Seed-Skript (backend/seed/) für Demo-Events? — offen, bei Bedarf anlegen
- Veranstalter-Anmeldung als bewusstes Produktziel mit aufnehmen (vs. erst nur Aggregation)?
- IHK Würzburg-Schweinfurt braucht Playwright (Master: playwright install). wuerzburg.ihk.de/veranstaltungen rendert Events client-seitig via sweap.io-SPA (data-account-id b7c34338-…, 0 Events im statischen HTML). sweap-API /api/webclient/v1/registration-pages braucht overview_ids die nicht aus account-id auflösbar waren. → ihk_wue-Adapter erst nach playwright install.

> **Kaltzone:** decisions_made, Iteration History, Backlog und Landmarks liegen unterhalb dieses Markers — per `Read` vollständig nachladen bei Bedarf.
<!-- /hot-context -->

## decisions_made

- **2026-06-25 · OAuth-Build-Strategie:** Slice 1 wird gegen `.env`-Platzhalter (`GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET`) gebaut. Lars legt den Google-OAuth-Client später in der Cloud Console an und trägt die echten Werte beim ersten Login-Test ein. Grund: entkoppelt den Build von der externen Google-Aktion, kein Blocker.
- **2026-06-25 · Deploy-Ziel Slice 1: nur lokal.** Slice 1 läuft ausschließlich lokal (localhost — Docker-Compose für postgres+api, Vite-Dev-Server für Frontend). Kein x1pro/Server-Deploy in diesem Slice; OAuth-Redirect-URIs nur auf localhost. x1pro-Deploy ist ein späterer, separater Schritt.
- **2026-06-25 · Git-Flow: Option A (Feature-Branch + PRs).** Slice 1 wird im agent-1-Worktree (Branch `agent/agent-1`) gebaut und per PR nach master gemergt; Mac arbeitet nicht direkt auf master (mac-worktree-Policy). PR #1 (`setup/stack-and-mockups` @ c1fb752) ist Vorfahre von master → inhaltlich enthalten, wird als redundant geschlossen (reopenbar).
- **2026-06-25 · Mockup-Richtung: simpel.** `frontend/index.html` (aufgeräumtes Landing) ist Basis der Vue-App-Shell, nicht die dichte `dashboard.html`-Variante.
- **2026-06-25 · Auth-Design (selbst entschieden, Plan-Empfehlung):** httpOnly-Session-Cookie nach OAuth-Callback (statt JWT im Frontend); Authorization-Code-Flow backend-seitig via Authlib; `vue-router` für `/` und `/profile`.
- **2026-06-25 · Multi-Agent-Verteilung (Lars bestätigt):** Event-Plattform-Arbeit auf 3 Worker-Agenten entlang Eigentums-Grenzen gesplittet — Agent-3=Backend (Scraper-CLI + `GET /api/events`), Agent-1=Index/logged-out + geteilte `SearchMask.vue` (Eigentümer), Agent-2=Dashboard/logged-in (konsumiert SearchMask). **Eine** geteilte SearchMask statt zweimal bauen (die User-Tasks „Suchmaske Index" + „logged-in" sind dieselbe Komponente). API-Contract + Komponenten-Interface in allen Briefs fixiert → parallele Arbeit ohne Warten. Briefs in je `<worktree>/_scrape/inbox/` (Details in HANDOFF.notes.md).

## Iteration History

- **2026-06-25** · event-radar-slice1 · Onboarding, Stack-Lock (vue-vite+fastapi-postgres), Event-Radar-Rebrand+Logo, Architektur+Connector-Vault-Doc, Slice-1-Plan
- **2026-06-25** · slice1-deploy · Slice 1 gebaut + PR #2 + lokal deployed (SQLite, :8000/:5174); Roadmap + Feed-Recherche (event-feeds-verified.md: Meetup-ICS/ZDI/FRIZZ verifiziert); Boundary agent-1 mit Lars geklaert (so lassen)
- **2026-06-25** · master-orchestration · master ff→0cc9070 (PR#3/4/5); lokal ohne Docker deployed (:8000/:5173, SQLite); 3 Agenten-Briefs verteilt (scraper / index+searchmask / dashboard) mit fixem API-Contract; tmux-Dispatch braucht larskohlmorgen-Relaunch (Blocker)
- **2026-06-26** · agent-1 feed-input-channel · rebased auf master (49866a0); data-driven Feed-Registrierung gebaut: feeds.yaml + feed_loader (Phase 1, 5 Feeds migriert) + FeedSource-Model + /api/feeds (Phase 2). 49 pytest grün. agent/agent-1 gepusht → Master-PR offen
- **2026-06-26** · agent1-adapters+radius · P1.1-Registry + AI-Week-Adapter + THWS-uni-Scraper gebaut/gepusht (IHK=Playwright-Flag); Radius-Suche-Brief rebased + Exploration+Plan fertig, Implementierung offen (Rotation bei 248K)

## backlog

- documentation/features/event-radar-architecture.md schreiben (inkl. Ingestion/Connector-Sektion, ref Vault patterns/data-integration/connector-architecture.md)
- documentation/technical/README.md mit Nomenklatur + Dev-Env füllen
- uncommittete Änderungen (Logo/Rename/frontend/config/plans) committen sobald Git-Flow geklärt
## landmarks

*(keine)*

## inbox

*(leer)*
