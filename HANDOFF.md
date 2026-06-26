---
type: handoff
vorhaben: 2026-hackathon
working_directory: /Users/larskohlmorgen/_clients/zdi/projects/coding/2026-hackathon/agent-2
created: 2026-06-25
last_updated: 2026-06-26-agent-2-p2-dedup
schema_version: "0.4"
status: done, ready-to-merge · P2-dedup-done · awaiting-brief
---

# Handoff — 2026-hackathon

> **Adressat:** nächste Session. Bootstrap: `current_task` → `read_first_critical`, dann loslegen.

## current_task

**AGENT-2 (Branch agent/agent-2) — P2 Refactor (Entdoppelung `_utcnow` + Fetch-Dedup) abgeschlossen & gepusht [b457c51].** Rebased auf origin/master (Master hat frühere agent-2-PRs gemergt — Secrets-Guard ist jetzt upstream). (1) Neuer util `app/_time.py` `utcnow()` → `models.py` + `ingest/core.py` importieren daraus (lokale `_utcnow`-Defs entfernt). (2) Neuer util `app/ingest/adapters/_fetch.py` `fetch_pages_deduped(urls, parse)` → `meetup.py` + `eventbrite_wue.py` nutzen ihn statt copy-pasteter dedup-while-fetch-Schleife. Verhalten unverändert. pytest 118 grün. Branch @ b457c51, Tree clean. **Nächster Schritt:** Auf den nächsten Brief von Master warten (`_scrape/inbox/`). Bei Session-Start ohne neuen Brief: Session parken und melden.

> **Scope-Notiz:** `events.py` hat kein inline `now()` (dünner Router) → unverändert. Weitere `_utcnow`-Kopien in `enrichment/attendance.py` + `events_service.py:51` sind Agent-3-Bereich (laut Brief out-of-scope) → bewusst gelassen; könnten in einem späteren Agent-3-Refactor ebenfalls auf `app/_time.utcnow` gezogen werden.
>
> Frühere agent-2-Arbeit (gemergt/gepusht): Visibility-Dedup, P0.4, P0.3, P1.2, P2 (auth UserOut + Secrets-Guard), Broad-Feed-Keyword-Tuning + 3 Feeds, P1.3 (Logging/Fehler-Sichtbarkeit).

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
- **2026-06-26** · agent-2 P2-backend-hygiene · auth UserOut response_model + Secrets-Prod-Guard (gemergt in master). pytest 85
- **2026-06-26** · agent-2 keyword-tuning · IT-Keyword-Gate erweitert + 3 Feeds (web_week/nerd2nerd/uni). pytest 101 · @ 547e9af
- **2026-06-26** · agent-2 P1.3-logging · geocode Netz-except verschmälert + Parse-except geloggt; main.py _configure_logging(). pytest 106 · @ 0b4a3bd
- **2026-06-26** · agent-2 P2-dedup · _utcnow → app/_time.utcnow (models+core); fetch-dedup → adapters/_fetch.fetch_pages_deduped (meetup+eventbrite). Verhalten unverändert. pytest 118 · @ b457c51 → Master-PR offen

## backlog

- documentation/features/event-radar-architecture.md schreiben (inkl. Ingestion/Connector-Sektion, ref Vault patterns/data-integration/connector-architecture.md)
- documentation/technical/README.md mit Nomenklatur + Dev-Env füllen
- uncommittete Änderungen (Logo/Rename/frontend/config/plans) committen sobald Git-Flow geklärt
## landmarks

*(keine)*

## inbox

*(leer)*
