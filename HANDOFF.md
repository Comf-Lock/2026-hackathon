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

> **Stand 2026-06-26 (master @ b601b79+):** Event Radar (IT-Event-Aggregator Mainfranken/ZDI). Master-Agent orchestriert **5 Worker-Agenten** (agent-1..5, je eigener Worktree/Branch + tmux `claude-[zdi-]2026-hackathon-agent-N`; agent-1/-4 tragen das `zdi-`-Präfix). Integration **nur via `gh pr`** (branch protection). Bei jedem Merge master-eigene Dateien schützen: `git checkout origin/master -- HANDOFF.md README.md backend/.gitignore .gitignore`. Neuer Adapter → additive Importzeile in `adapters/__init__.py` (Union-Merge-Punkt). **Achtung Branch-Anlegen:** `git checkout -B` resettet den Working-Tree → uncommittete Edits gehen verloren; immer ZUERST Branch, DANN editieren.

**Deploy (localhost, OHNE Docker):** uvicorn `:8000` **mit --reload** + Vite `:5173`, beide larskohlmorgen-owned → Neustart via Relay (`/tmp/restart-eventradar-api.sh` / `-vite.sh`); `.env`-Änderungen brauchen API-**Neustart** (--reload reicht nicht). **Postgres** (`postgresql+psycopg://eventradar:eventradar@localhost:5432/eventradar`); neue Spalten = manuelles ALTER, neue Tabellen legt `create_all` an. Scoring = **Sonnet** (.env). `.env` permission-blockiert → Secrets nur via Relay-Skript, nie in den Chat. **Tailscale Serve:** `https://macbook-pro-von-lars.tail7629bb.ts.net/` (443, **ohne Port** — nur diese URL setzt `X-Forwarded-Host`, von dem OAuth/Login abhängt; direkter `:5173`-Port NICHT → Login scheitert dort).

**Geliefert & live:** Umkreissuche (Haversine, Suche+Karte, „Umkreis berücksichtigen"-Häkchen + Profil-Radius), Karten-Filter Online/Vor-Ort, Infinite-Scroll, Responsive + PWA-Shell (vite-plugin-pwa **injectManifest**, custom `src/sw.js`), 3 Scraper (ki_regio/startbahn27/informatik_uni_wue → 136 Events), iPhone-Login via Tailscale (host-abh. OAuth in `auth.py`: `_derive_redirect_uri`/`_derive_frontend_base` aus `X-Forwarded-Host`), tag-Suche=Freitext, **V3-Logo** (BrandLogo.vue **+** logo.svg-Favicon — zwei Stellen!), **Web-Push komplett gebaut** (Backend `push.py`: `/api/push/subscription|test|vapid-public-key` + `gen-vapid` CLI; Frontend `usePush.js` + Subscribe-Toggle im Profil + SW-Push-Handler).

**OFFEN / nächste Schritte:** (1) **Web-Push scharf schalten:** Lars führt `/tmp/set-vapid-and-restart.sh` aus (gen-vapid-Keys → .env + API-Neustart), dann End-to-End-Test via Profil-Toggle + `POST /api/push/test`. (2) **agent-4 in Arbeit:** Karten-Tab mobil (`MapView`/`MapEventList` Media-Queries + Leaflet-Höhe/`invalidateSize`). (3) PWA-**Install** am Handy braucht Prod-Build hinter HTTPS (Dev-SW aus). (4) Mögliches Pitch-Gap: Veranstalter-**Event-Formular** (nur Feed-Registrierung `POST /api/feeds` existiert, kein Einzel-Event-Submit). (5) weitere Scraper (Recherche-Rang 4–8 in `documentation/features/scraper-sources-research.md`), Refactoring-Restposten.

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
