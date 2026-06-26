---
type: handoff
vorhaben: 2026-hackathon
working_directory: /Users/larskohlmorgen/_clients/zdi/projects/coding/2026-hackathon/agent-4
created: 2026-06-25
last_updated: 2026-06-26-agent-4-calendar-detail
schema_version: "0.4"
status: slice1-deployed · master-orchestration · agent-4-calendar-detail-column
---

# Handoff — 2026-hackathon

> **Adressat:** nächste Session. Bootstrap: `current_task` → `read_first_critical`, dann loslegen.

## current_task

agent/agent-4: Kalender-Detail-Spalte **fertig + gepusht** [1367c43, auf rebased origin/master]. `/calendar` ist jetzt zweispaltig: Klick auf ein Event im Raster (Woche/Monat) → neue schmale Detail-Spalte rechts zeigt dieselben Infos wie die Such-/Listen-Items (Titel+Link, Datum, Ort, Tags, Beschreibungs-Auszug mit Mehr/Weniger, Themen-Gewichtung+Intent, Quellen-Sichtbarkeit+Tier), vertikal/kompakt für die schmale Spalte. Neue **presentational** Komponente `frontend/src/calendar/CalendarEventDetail.vue` — nutzt die geteilten `lib/eventDisplay`-Helfer (cleanDescription/distinctSources/weightBar/intentMix/visibilityTier) + `calendarRange.formatDateLabel`, **nicht** EventCard.vue/eventDisplay.js umgebaut (Agent-3). Default: nächstes anstehendes Event auto-selektiert (Badge „Nächstes Event"); responsiv (Spalte stapelt unter dem Raster <980px, sticky darüber). Raster-Events sind jetzt Buttons (Klick=Select statt Direkt-Link; „Zum Event"-Link lebt in der Spalte), aktives Event hervorgehoben. Nur `CalendarView.vue` (geändert) + neue Komponente; vite build grün (63 modules). Brief → `_scrape/processed/`.
> Vorherige Arbeit (bleibt PR-ready): Refactor P1.5 Auth-Redirect [f80c74d]; drei View-Tabs /calendar [2ad1d5d], /map [1bbf33b] inkl. MapEventList [fe1c441]; Architektur-Audit `plans/refactor-architecture-audit.md` [e0e2478].
> **Hinweis HANDOFF-Drift (wiederkehrend):** `git rebase` honoriert `HANDOFF.md merge=ours` NICHT → jeder Rebase ersetzt die agent-4-HANDOFF durch master's Fassung; danach aus `ORIG_HEAD` wieder branch-lokal herstellen (`git checkout ORIG_HEAD -- HANDOFF.md`, working_directory muss .../agent-4 sein). Bei jedem künftigen Rebase beachten.
> **Nächster Schritt:** Master merged agent/agent-4 via PR (GitHub ignoriert merge=ours → master-HANDOFF beim Merge manuell auf master-Fassung auflösen, wie bei PR#8). Agent-4 wartet danach auf neuen Brief.

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
- **2026-06-26** · agent-4 calendar+map+sidelist+audit · /calendar (Woche/Monat/Jahr) + /map (Leaflet/OSM) mit Event-Seitenliste, click-to-fly, Profil-Filter über useEvents [fe1c441]; Architektur-Audit → Refactor-Plan [e0e2478], Info an Master-Inbox. agent/agent-4 gepusht → Master-PR(s)

## backlog

- documentation/features/event-radar-architecture.md schreiben (inkl. Ingestion/Connector-Sektion, ref Vault patterns/data-integration/connector-architecture.md)
- documentation/technical/README.md mit Nomenklatur + Dev-Env füllen
- uncommittete Änderungen (Logo/Rename/frontend/config/plans) committen sobald Git-Flow geklärt
## landmarks

*(keine)*

## inbox

*(leer)*
