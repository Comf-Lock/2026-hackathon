---
type: handoff
vorhaben: 2026-hackathon
working_directory: /Users/larskohlmorgen/_clients/zdi/projects/coding/2026-hackathon/agent-2
created: 2026-06-25
last_updated: 2026-06-26-agent-2-keyword-tuning
schema_version: "0.4"
status: done, ready-to-merge · broad-feed-keyword-tuning-done · awaiting-brief
---

# Handoff — 2026-hackathon

> **Adressat:** nächste Session. Bootstrap: `current_task` → `read_first_critical`, dann loslegen.

## current_task

**AGENT-2 (Branch agent/agent-2) — Broad-Feed Keyword-Tuning + 3 Feed-Registrierungen abgeschlossen & gepusht [547e9af].** Rebased auf origin/master. (1) IT-Keyword-Gate (`backend/app/ingest/types.py` `GeoScope.keywords`) mit hochpräzisen deutschen Begriffen erweitert (programmier, informatik, robotik/roboter, gründer, maker/fablab/hacker(space), open source, linux, blockchain, krypto, iot/llm/edv, 3d-druck, neuronale, deep learning) — bewusst KEINE generischen Wörter (Workshop/Meetup/Vortrag/Innovation) gegen Flood. (2) 3 verifizierte Feeds in `feeds.yaml`: `wuerzburg_web_week` (ics, broad=false), `nerd2nerd` (rss, broad=true, Hackerspace), `uni_wuerzburg` (rss, broad=true). `filters.py` selbst unverändert. **Verifiziert via Dry-Run-Ingest:** uni_wuerzburg **1/86** kept (der eine Informatik-Talk „Programmierstilistik" — gefangen vom neuen `programmier`-Keyword, alte Liste hätte ihn verpasst); nerd2nerd **15/15** (über kuratierte Feed-Tags); frizz **0/30** (heute alle Nicht-IT → präzise, kein Flood). pytest 101 grün. Branch @ 547e9af, Tree clean. **Nächster Schritt:** Auf den nächsten Brief von Master warten (`_scrape/inbox/`). Bei Session-Start ohne neuen Brief: Session parken und melden. Offen nur Master-seitig: PRs (P2 + Keyword-Tuning) nach master mergen.

> **Beobachtung (Master-Entscheidung):** `nerd2nerd` ist broad=true, aber seine kuratierten Feed-Tags (hackerspace/maker/digital) erfüllen das Keyword-Gate für **alle** 15 Items — d.h. der Gate ist dort effektiv ein No-op. Vertretbar für einen reinen Hackerspace; falls echte Title-Filterung gewünscht → broad=false setzen oder IT-Default-Tags entfernen.
>
> Frühere agent-2-Arbeit (alle gemergt/gepusht): Visibility-Dedup, P0.4 (DashboardView-Slim), P0.3 (useEvents-Layer), P1.2 (async→def), P2 (auth UserOut response_model + Secrets-Prod-Guard) [53ad016].

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
- **2026-06-26** · agent-2 P2-backend-hygiene · /api/auth/me → UserOut response_model; Startup-Secrets-Guard (warn dev / fail-fast prod) in main.py + config.py. Nur auth/config/main. pytest 85 grün. agent/agent-2 @ 53ad016 → Master-PR offen
- **2026-06-26** · agent-2 broad-feed-keyword-tuning · IT-Keyword-Gate (types.py) hochpräzise erweitert (programmier/informatik/robotik/gründer/maker/linux/… kein Workshop/Meetup-Flood) + 3 Feeds (wuerzburg_web_week, nerd2nerd, uni_wuerzburg). Dry-Run: uni 1/86, nerd2nerd 15/15, frizz 0/30. pytest 101 grün. agent/agent-2 @ 547e9af → Master-PR offen

## backlog

- documentation/features/event-radar-architecture.md schreiben (inkl. Ingestion/Connector-Sektion, ref Vault patterns/data-integration/connector-architecture.md)
- documentation/technical/README.md mit Nomenklatur + Dev-Env füllen
- uncommittete Änderungen (Logo/Rename/frontend/config/plans) committen sobald Git-Flow geklärt
## landmarks

*(keine)*

## inbox

*(leer)*
