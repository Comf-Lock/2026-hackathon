---
type: handoff
vorhaben: 2026-hackathon
working_directory: /Users/larskohlmorgen/_clients/zdi/projects/coding/2026-hackathon/agent-2
created: 2026-06-25
last_updated: 2026-06-26-agent-2-visibility-dedup-plan
schema_version: "0.4"
status: agent-2 · visibility-dedup · planned
---

# Handoff — 2026-hackathon

> **Adressat:** nächste Session. Bootstrap: `current_task` → `read_first_critical`, dann loslegen.

## current_task

**AGENT-2 (Branch agent/agent-2) — Sichtbarkeit: Cross-Source-Dedup + Reframe.** Auftrag: _scrape/inbox/task-visibility-dedup.md. agent/agent-2 wurde auf origin/master rebased (master hat jetzt Rich-Card, Bookmarks, Feed-Kanal, lib/eventDisplay.js; searchKit.js zeigt auf Agent-1s ECHTE Komponenten). Vollständiger, präziser Umsetzungsplan liegt im Journal _scrape/.session/journal-2026-06-26.md (Eintrag 09:26). Umsetzung NOCH NICHT begonnen (Rotation an Lese/Plan-Grenze). **Nächster Schritt:** Plan abarbeiten — TEIL A Backend: NEU backend/app/ingest/dedup.py (reine Funktionen normalize_title/normalize_location/event_fingerprint/record_fingerprint; lowercase+Akzente-strip+Füllwörter-raus, fp=sha256(normtitle|start.date|location)); Event.dedup_key-Spalte (indexed); core.upsert_event um Fingerprint-Merge erweitern ((source,extid)-Check bleibt erste Idempotenz-Linie; danach per dedup_key bestehendes Event suchen -> neue EventSource anhängen + fehlende Felder füllen, sonst neues Event); NEU tests/test_dedup.py (2 Quellen gleicher fp -> 1 Event/2 Sources, Re-Run idempotent, anderes Datum -> getrennt); pytest grün; commit 'feat(ingest): cross-source dedup'. TEIL B Frontend: eventDisplay.visibilityTier(count); EventCard Stufen-Badge (1=Exklusiv gelistet, 2-3=Mehrfach gelistet·N, 4+=Hohe Sichtbarkeit·N) statt Blindspot, amber+⚡ raus, Header 'Sichtbarkeit · N Quellen'; DashboardView blindspotEvents->exclusiveEvents + Rail positiv; vite build grün; commit 'feat(ui): visibility tiers'. Dann push agent/agent-2 + HANDOFF + Brief nach _scrape/processed/. Master merged via PR (master protected). Verifikation: 'PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests' + 'npm run build --prefix frontend'.

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
- **2026-06-26** · agent-2 visibility-dedup-plan · auf origin/master rebased, Brief + relevanten Code analysiert, präzisen Umsetzungsplan (Cross-Source-Dedup Backend + Sichtbarkeits-Reframe Frontend) im Journal fixiert; Umsetzung folgt

## backlog

- documentation/features/event-radar-architecture.md schreiben (inkl. Ingestion/Connector-Sektion, ref Vault patterns/data-integration/connector-architecture.md)
- documentation/technical/README.md mit Nomenklatur + Dev-Env füllen
- uncommittete Änderungen (Logo/Rename/frontend/config/plans) committen sobald Git-Flow geklärt
## landmarks

*(keine)*

## inbox

*(leer)*
