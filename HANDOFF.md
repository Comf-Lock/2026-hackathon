---
type: handoff
vorhaben: 2026-hackathon
working_directory: /Users/larskohlmorgen/_clients/zdi/projects/coding/2026-hackathon/master
created: 2026-06-25
last_updated: 2026-06-25-master-orchestration
schema_version: "0.4"
status: architecture · slice1-deployed · master-orchestration
---

# Handoff — 2026-hackathon

> **Adressat:** nächste Session. Bootstrap: `current_task` → `read_first_critical`, dann loslegen.

## current_task

> **agent/agent-3 Stand 2026-06-26 (P1.4 Format-Refactor + Card-Fix):** **fertig + gepusht** — bereit für Master-PR. Commit `79a97af` auf rebased origin/master. (A) Neues TZ-sicheres Display-Modul `frontend/src/lib/eventFormat.js` (String-Slice-Basis): bündelt Datum/Zeit/Monat/Ort-Formatierung. Entfernt die 3× MONTHS (calendarRange, EventCard, MiniEventRow), die `new Date(iso)`-Formatter (EventCard+MiniEventRow — verschoben Tag/Zeit in Nicht-Berlin-TZ) und die doppelten place-Varianten (→ `formatPlace`/`formatPlaceShort`/`venueCity`). Konsumenten EventCard/MiniEventRow/CalendarEventDetail/MapEventList/MapView importieren das Modul; `calendarRange.js` behält nur Grid-Math und re-exportiert die geteilten Konstanten → CalendarView unverändert. SearchMask/useEvents (Agent-1) nicht angefasst. (B) „geschätzt"-Marker am Gewichtungsbalken entfernt (EventCard + CalendarEventDetail) — LLM schätzt immer, redundant. vite build grün.

> **agent/agent-1 Stand 2026-06-26:** Feed-Input-Kanal (data-driven RSS/ICS-Registrierung) **fertig + gepusht** — bereit für Master-PR nach master. 2 Commits auf rebased master (`feat(ingest): config-driven feed registry`, `feat(api): feed source registration`). 49 pytest grün. Phase 1: `backend/app/ingest/feeds.yaml` + `feed_loader.py` (5 Feeds aus Code migriert, generische ICS/RSS-Adapter), `python -m app.ingest list`. Phase 2: `FeedSource`-Model + auth-gated `GET/POST/DELETE /api/feeds`, run_ingestion zieht enabled DB-Feeds. Details siehe Journal 2026-06-26.

Event Radar (IT-Event-Aggregator Mainfranken/ZDI). **Master-Agent orchestriert jetzt 3 Worker-Agenten** (agent-1/2/3, je eigener Worktree/Branch). master @ 0cc9070 (PR#3/4/5 gemergt: slice-2 ingest core + login/dashboard frontend). Lokal deployed OHNE Docker: uvicorn :8000 + Vite :5173 (beide 0.0.0.0), SQLite-Fallback via `backend/.env` (`DATABASE_URL=sqlite:///./eventradar.db`). `DEV_BYPASS_AUTH`-Flag in `frontend/src/router.js` aktiv (dev-only, NICHT committed) damit /dashboard ohne Google-Login sichtbar. **Task-Verteilung** (Briefs je in `<worktree>/_scrape/inbox/`): Agent-3=Backend Scraper-CLI (ICS/RSS Mainfranken) + `GET /api/events`; Agent-1=Index/logged-out + geteilte `SearchMask.vue` (Eigentümer); Agent-2=Dashboard/logged-in (konsumiert SearchMask). API-Contract + Komponenten-Interface in allen Briefs fixiert. **BLOCKER:** Worker-tmux-Sessions laufen auf larskohlmorgen-Socket (UID 501); Master-Session ist agentuser → kann `send-keys` nicht abfeuern. **Nächster Schritt:** Lars startet Master-Session als larskohlmorgen neu, dann 3× `tmux send-keys` (exakte Befehle in HANDOFF.notes.md) abfeuern + Sessions beobachten; gemergte Worker-PRs nach master integrieren; Dev-Env am Laufen halten.

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

## backlog

- documentation/features/event-radar-architecture.md schreiben (inkl. Ingestion/Connector-Sektion, ref Vault patterns/data-integration/connector-architecture.md)
- documentation/technical/README.md mit Nomenklatur + Dev-Env füllen
- uncommittete Änderungen (Logo/Rename/frontend/config/plans) committen sobald Git-Flow geklärt
## landmarks

*(keine)*

## inbox

*(leer)*
