---
type: handoff
vorhaben: 2026-hackathon
working_directory: /Users/larskohlmorgen/_clients/zdi/projects/coding/2026-hackathon/agent-4
created: 2026-06-25
last_updated: 2026-06-27-handoff-save
schema_version: "0.4"
status: master-orchestration · agent-4-map-mobile-done · handoff-save
---

# Handoff — 2026-hackathon

> **Adressat:** nächste Session. Bootstrap: `current_task` → `read_first_critical`, dann loslegen.

## current_task

agent/agent-4 (sole frontend agent). **Kein offener Auftrag.** Alle agent-4-Tasks (Responsive, Map-Online-Filter, Geo-Radius, Infinite-Scroll, Web-Push, Map-Mobil) sind in master gemergt; Branch == master, clean. Karten-Tab mobil zuletzt fertig [04d03bc]. Diese Session: handoff-save — Plan-Audit registrierte 2 bisher unregistrierte Pläne in active_plans (refactor-architecture-audit=planned, agent-4-integration-real-events=done/superseded); bewusst nichts gelöscht (Multi-Agent-Repo, fremde Branch-Referenzen). **Nächster Schritt:** Kein aktiver Plan auf agent/agent-4 — auf neuen Master-Brief in _scrape/inbox/ oder Lars-Input warten. HINWEISE: Web-Push braucht VAPID-Key-Setup im Backend (Agent-3) + iOS-Push nur als installierte PWA; PWA-Install braucht HTTPS (Master: Tailscale-serve/Cert).

## active_plans

- name: event-radar-slice-1
  path: plans/event-radar-slice-1.md
  status: done
- name: event-radar-slice-2
  path: plans/event-radar-slice-2.md
  status: in_progress
- name: refactor-architecture-audit
  path: plans/refactor-architecture-audit.md
  status: planned
- name: agent-4-integration-real-events
  path: plans/agent-4-integration-real-events.md
  status: done

> Hinweis: slice-1 deployed/gemergt (PR#3); Datei bewusst NICHT gelöscht (Agent-Branches referenzieren sie, aktive Parallelarbeit). slice-2 wird von Agent-3 (Ingest/Scraper) fortgeführt.
> refactor-architecture-audit: projektweiter Konsolidierungs-Plan (12 offen), Befunde teils in fremdem Agenten-Eigentum — nicht agent-4-exklusiv, nicht löschen.
> agent-4-integration-real-events: Phase 1 verifiziert/committet [9f01735], Phase 2 von Master-Integration übernommen → superseded; analog slice-1 bewusst behalten statt gelöscht.

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

- **2026-06-26** · agent-1 feed-input-channel · rebased auf master (49866a0); data-driven Feed-Registrierung gebaut: feeds.yaml + feed_loader (Phase 1, 5 Feeds migriert) + FeedSource-Model + /api/feeds (Phase 2). 49 pytest grün. agent/agent-1 gepusht → Master-PR offen
- **2026-06-26** · agent-4 calendar+map+sidelist+audit · /calendar (Woche/Monat/Jahr) + /map (Leaflet/OSM) mit Event-Seitenliste, click-to-fly, Profil-Filter über useEvents [fe1c441]; Architektur-Audit → Refactor-Plan [e0e2478], Info an Master-Inbox. agent/agent-4 gepusht → Master-PR(s)
- **2026-06-26** · agent-4-session · 5 Frontend-Tasks fertig+gepusht (Auth-Refactor P1.5, Kalender-Detail-Spalte, Logged-out-Layout+Tab Suche, PWA-Shell installierbar, Header-positionsstabil); PWA-Responsive (Phase 1b) Survey fertig, Edits offen (Plan im Journal 12:31). Wiederkehrend: Rebase bricht HANDOFF merge=ours → jedes Mal aus ORIG_HEAD restoren.
- **2026-06-26** · agent-4-frontend-sweep · PWA-Responsive + Map-Online/Vor-Ort-Filter + Geo-Radius-Toggle (useRadius, Profil-Radius-Default, Radius auf Karte) + Infinite-Scroll (loadMore/hasMore + IntersectionObserver) + Web-Push (injectManifest-SW + usePush + Profil-UI) + Karten-Tab-Mobil (invalidateSize, MapEventList-Media-Queries). Alle via PR nach master gemergt.
- **2026-06-27** · handoff-save · Plan-Audit: refactor-architecture-audit (planned) + agent-4-integration-real-events (done/superseded) in active_plans registriert, nichts gelöscht; kein Code-Change.

## backlog

- documentation/features/event-radar-architecture.md schreiben (inkl. Ingestion/Connector-Sektion, ref Vault patterns/data-integration/connector-architecture.md)
- documentation/technical/README.md mit Nomenklatur + Dev-Env füllen
- uncommittete Änderungen (Logo/Rename/frontend/config/plans) committen sobald Git-Flow geklärt
## landmarks

*(keine)*

## inbox

*(leer)*
