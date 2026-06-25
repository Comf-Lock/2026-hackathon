---
type: handoff
vorhaben: 2026-hackathon
working_directory: /Users/larskohlmorgen/_clients/zdi/projects/coding/2026-hackathon/master
created: 2026-06-25
last_updated: 2026-06-25-agent-2-dashboard-done
schema_version: "0.4"
status: agent-2 · dashboard logged-in · ready-to-merge
---

# Handoff — 2026-hackathon

> **Adressat:** nächste Session. Bootstrap: `current_task` → `read_first_critical`, dann loslegen.

## current_task

**AGENT-2 (Branch `agent/agent-2`) — Dashboard logged-in: FERTIG, bereit für Master-Merge.** Auftrag (war `_scrape/processed/task-dashboard-loggedin.md`): personalisierter Logged-in-Bereich, der die GETEILTEN Such-Komponenten (Agent-1s Eigentum) konsumiert statt sie neu zu bauen.

Umgesetzt: `frontend/src/views/DashboardView.vue` neu gebaut + neuer eigener Namespace `frontend/src/dashboard/` mit (a) `searchKit.js` = einzige Indirektion/Swap-Punkt, (b) Stubs `SearchMaskStub.vue` / `EventListStub.vue` / `useEventSearchStub.js` gegen das FIXIERTE Interface (SearchMask v-model {q,city,tag,dateFrom,dateTo,isOnline}+'search'; EventList {events,loading,total}; useEventSearch()->{filters,events,total,loading,error,search}). useEventSearchStub trifft den `GET /api/events`-Contract und fällt auf In-Memory-EventOut-Demo zurück solange Agent-3s Endpoint fehlt. Personalisierung: Begrüßung mit User-Name (useAuth), Filter-Vorbelegung aus Profil (`/api/profile`: home_label->city, interests[0]->tag), interessenbasierte „Für dich"-Sektion, Profil-Strip + Rationale-Rail; sauberer Fallback bei 401/kein Profil/kein Endpoint. Vite-Build grün (44 Module). Commits: c88da00 (feature) + swap-safe fix.

**Eigentums-Disziplin eingehalten:** SearchMask/EventList/LandingView NICHT angefasst; Stubs liegen unter eigenem Namespace; Router NICHT geändert.

**Nächster Schritt (Master/Folge):** (1) agent/agent-2 nach master mergen. (2) Visuelle Browser-Prüfung von /dashboard (hier headless nicht möglich wegen Auth-Gate). (3) Sobald Agent-1s echte `SearchMask.vue`/`EventList.vue`/`composables/useEventSearch.js` in master sind: die 3 Re-Export-Zeilen in `frontend/src/dashboard/searchKit.js` auf die echten Imports umstellen (DashboardView bleibt unverändert) und die Stub-Dateien löschen.

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
- **2026-06-25** · agent-2-dashboard · Logged-in DashboardView neu gebaut, konsumiert geteiltes Such-Kit via searchKit.js-Indirektion (lokale Stubs gegen fixiertes Interface, 1-Zeilen-Swap später); Personalisierung (Begrüßung, Profil-Filter-Vorbelegung, „Für dich") + Demo-Fallback; Build grün; bereit für Merge

## backlog

- documentation/features/event-radar-architecture.md schreiben (inkl. Ingestion/Connector-Sektion, ref Vault patterns/data-integration/connector-architecture.md)
- documentation/technical/README.md mit Nomenklatur + Dev-Env füllen
- uncommittete Änderungen (Logo/Rename/frontend/config/plans) committen sobald Git-Flow geklärt
## landmarks

*(keine)*

## inbox

*(leer)*
