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

agent/agent-1 · **Radius-Suche (Haversine) — FERTIG, committet [bcf522e], gepusht zu origin/agent/agent-1. Master macht PR.** Geliefert: backend/app/geo.py (geteilter `haversine_km`, ingest/filters.py importiert ihn — keine 2. Distanz-Impl); `GET /api/events` optionale `lat/lng/radius_km` (nur zusammen aktiv), Python-Postfilter (events ohne Koordinaten bei Radius ausgeschlossen, ohne Radius unverändert), 4 neue Tests; Frontend SearchMask Radius-Slider 5–100 (default 40) + 'In meiner Nähe' (geolocation), gated auf neue `geo`-Prop; useEvents `geo`-Option resolved Zentrum (Profil `home_lat/home_lng` eingeloggt, sonst `navigator.geolocation`), toQuery sendet lat/lng/radius_km nur bei Zentrum+Radius, graceful ohne; LandingView geo:true + dateFrom=heute. 130 pytest grün, vite build grün. **Hinweis für Master/Agent-2:** logged-in Profil-Zentrum funktioniert sobald ein logged-in SearchMask-Host (DashboardView, Agent-2) `useEvents({ geo: true })` setzt + `:geo/:locating/:has-center` + `@locate` durchreicht — bewusst nicht editiert (Eigentums-Grenze). Nebenbei: `leaflet` war in package.json deklariert aber nicht installiert (stale node_modules) → `npm install` ausgeführt (kein Repo-Change). **Nächster Schritt:** kein offener Code-Task auf agent-1; Master merged Radius-PR.

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
- **2026-06-26** · agent1-radius-search · Radius-Suche (Haversine) fertig [bcf522e]: geteilter geo.haversine_km, GET /api/events lat/lng/radius_km + Postfilter + 4 Tests, SearchMask Slider + geolocation, useEvents geo-Option/Zentrum-Resolution, LandingView geo:true; 130 pytest + vite build grün; gepusht → Master-PR

## backlog

- documentation/features/event-radar-architecture.md schreiben (inkl. Ingestion/Connector-Sektion, ref Vault patterns/data-integration/connector-architecture.md)
- documentation/technical/README.md mit Nomenklatur + Dev-Env füllen
- uncommittete Änderungen (Logo/Rename/frontend/config/plans) committen sobald Git-Flow geklärt
## landmarks

*(keine)*

## inbox

*(leer)*
