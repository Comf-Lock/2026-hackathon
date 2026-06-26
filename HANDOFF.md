---
type: handoff
vorhaben: 2026-hackathon
working_directory: /Users/larskohlmorgen/_clients/zdi/projects/coding/2026-hackathon/agent-4
created: 2026-06-25
last_updated: 2026-06-26-agent-4-web-push-done
schema_version: "0.4"
status: master-orchestration · agent-4-web-push-done
---

# Handoff — 2026-hackathon

> **Adressat:** nächste Session. Bootstrap: `current_task` → `read_first_critical`, dann loslegen.

## current_task

agent/agent-4 (sole frontend agent). **Web-Push Subscribe-UI + SW-Push-Handler — FERTIG, committet, vite build grün (injectManifest-Modus).** (1) PWA-Strategie von `generateSW` → **`injectManifest`** umgestellt (vite.config: `strategies/srcDir:'src'/filename:'sw.js'`; `workbox`-Block → `injectManifest.globPatterns`). (2) Eigener **`frontend/src/sw.js`**: `precacheAndRoute(self.__WB_MANIFEST)` (Shell-Precache erhalten) + `NavigationRoute`-SPA-Fallback auf /index.html mit `/api`-Denylist (ersetzt altes navigateFallback); `skipWaiting`+`clients.claim` (autoUpdate-kompatibel); `push`-Listener → `showNotification(title,{body,icon,badge,data.url})`; `notificationclick` → vorhandenes Fenster fokussieren/navigieren oder `openWindow`. (3) **`composables/usePush.js`**: Feature-Detection (`serviceWorker`+`PushManager`+`Notification`), `Notification.requestPermission` (denied→graceful Hinweis), `GET /api/push/vapid-public-key` → `pushManager.subscribe({userVisibleOnly,applicationServerKey})` (urlBase64ToUint8Array) → `POST /api/push/subscription` (sub.toJSON()); Unsub: `sub.unsubscribe()` + `DELETE /api/push/subscription({endpoint})`; `refresh/toggle/busy/error/permission/subscribed`. (4) **ProfileView**: eigener „Benachrichtigungen"-Card mit Toggle-Button (aktiv/aus/blockiert), nicht unterstützt → Hinweis statt Crash. Build erzeugt `dist/sw.js` (push/notificationclick/showNotification verifiziert), Precache 15 Entries (Shell + Installierbarkeit intakt). Dateien: vite.config.js, src/sw.js (neu), composables/usePush.js (neu), views/ProfileView.vue. Brief → `_scrape/processed/`. **Kontext:** frühere agent-4-Arbeit in master gemergt (zuletzt PR #58); Branch nach Rebase == master, HANDOFF aus ORIG_HEAD restored (Rebase bricht `merge=ours`). **Nächster Schritt:** push agent/agent-4 → Master merged via PR. **HINWEIS:** (a) End-to-End-Push testet Master nach VAPID-Key-Setup im Backend (Agent-3-Endpoints müssen live sein); (b) **iOS Web-Push funktioniert NUR als zum Home-Bildschirm installierte PWA** (Safari im Browser-Tab unterstützt kein Push) — Feature-Detection greift dort und zeigt den Hinweis; (c) On-Device/PWA-Install braucht HTTPS (Master: Tailscale-serve/Cert).

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

- **2026-06-25** · slice1-deploy · Slice 1 gebaut + PR #2 + lokal deployed (SQLite, :8000/:5174); Roadmap + Feed-Recherche (event-feeds-verified.md: Meetup-ICS/ZDI/FRIZZ verifiziert); Boundary agent-1 mit Lars geklaert (so lassen)
- **2026-06-25** · master-orchestration · master ff→0cc9070 (PR#3/4/5); lokal ohne Docker deployed (:8000/:5173, SQLite); 3 Agenten-Briefs verteilt (scraper / index+searchmask / dashboard) mit fixem API-Contract; tmux-Dispatch braucht larskohlmorgen-Relaunch (Blocker)
- **2026-06-26** · agent-1 feed-input-channel · rebased auf master (49866a0); data-driven Feed-Registrierung gebaut: feeds.yaml + feed_loader (Phase 1, 5 Feeds migriert) + FeedSource-Model + /api/feeds (Phase 2). 49 pytest grün. agent/agent-1 gepusht → Master-PR offen
- **2026-06-26** · agent-4 calendar+map+sidelist+audit · /calendar (Woche/Monat/Jahr) + /map (Leaflet/OSM) mit Event-Seitenliste, click-to-fly, Profil-Filter über useEvents [fe1c441]; Architektur-Audit → Refactor-Plan [e0e2478], Info an Master-Inbox. agent/agent-4 gepusht → Master-PR(s)
- **2026-06-26** · agent-4-session · 5 Frontend-Tasks fertig+gepusht (Auth-Refactor P1.5, Kalender-Detail-Spalte, Logged-out-Layout+Tab Suche, PWA-Shell installierbar, Header-positionsstabil); PWA-Responsive (Phase 1b) Survey fertig, Edits offen (Plan im Journal 12:31). Wiederkehrend: Rebase bricht HANDOFF merge=ours → jedes Mal aus ORIG_HEAD restoren.

## backlog

- documentation/features/event-radar-architecture.md schreiben (inkl. Ingestion/Connector-Sektion, ref Vault patterns/data-integration/connector-architecture.md)
- documentation/technical/README.md mit Nomenklatur + Dev-Env füllen
- uncommittete Änderungen (Logo/Rename/frontend/config/plans) committen sobald Git-Flow geklärt
## landmarks

*(keine)*

## inbox

*(leer)*
