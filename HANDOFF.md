---
type: handoff
vorhaben: 2026-hackathon
working_directory: /Users/larskohlmorgen/_clients/zdi/projects/coding/2026-hackathon/agent-5
created: 2026-06-25
last_updated: 2026-06-27-agent-5-logo-proposals
schema_version: "0.4"
status: PR#40+#50 merged · informatik-scraper-merged · logo-variants-proposed
---

# Handoff — 2026-hackathon

> **Adressat:** nächste Session. Bootstrap: `current_task` → `read_first_critical`, dann loslegen.

## current_task

agent/agent-5 (Mac-Feature-Worktree) liefert isolierte Aufgaben, je als eigener PR nach master. Zuletzt gemergt: Scraper `informatik_uni_wue` (Institut für Informatik Uni Würzburg, schema.org-Microdata, PR#53 → master via bc28110). Danach: **Logo-Kontrast-Varianten** als reine Proposals geliefert (V1 hellere Ringe / V2 invertiertes helles Tile / V3 leuchtende Teal-Brand-Ringe) — in `_scrape/logo-variants/` (untracked), KEIN Commit/PR (so vom Brief verlangt). Details + Töne + Folgeauftrag in HANDOFF.notes.md. Disziplin pro Auftrag: `git fetch && git rebase origin/master` → Arbeit → Journal → Code-Commit als Branch-Tip force-pushen (HANDOFF branch-lokal, NICHT gepusht — merge=ours greift bei GitHub-Merges nicht) → PR → Brief nach `_scrape/processed/`. **Nächster Schritt:** auf Lars' Logo-Wahl (V1/V2/V3 → Folgeauftrag setzt sie ins getrackte `frontend/public/logo.svg`) bzw. nächsten Brief aus `_scrape/inbox/` warten (aktuell leer).

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
- Logo-Variante wählen: V1 (hellere Ringe) / V2 (invertiertes helles Tile, max Kontrast) / V3 (leuchtende Teal-Brand-Ringe)? — Vergleich via http.server :8092 auf _scrape/logo-variants/index.html; Folgeauftrag übernimmt die Wahl ins getrackte frontend/public/logo.svg

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

- **2026-06-26** · agent-5 wueww-feed · feeds.yaml: kaputten `wuerzburg_web_week`-Eintrag (404 Meetup-Slug, keine öffentliche Feed-Quelle) entfernt + Kommentar (AI-Week-Adapter deckt WueWW ab); andere 7 Feeds auf 200 verifiziert. app.ingest list sauber, pytest 118 passed → PR#36 (gemergt via PR#38)
- **2026-06-26** · agent-5 req-split · Scraper-Deps (playwright/beautifulsoup4/icalendar/feedparser) aus requirements.txt → neue requirements-ingest.txt (`-r requirements.txt` + 4 Deps); requirements.txt = API-Runtime. Nur requirements-Dateien, kein Code. pytest 126 passed. Caveat dokumentiert: API importiert icalendar/feedparser/bs4 noch transitiv via feeds.py→feed_loader (Follow-up: lazy import)
- **2026-06-26** · agent-5-rolling · 4 Aufträge geliefert (P2 docs/nav/test PR#31✓, WueWW-feed-fix PR#38✓, requirements ingest-split PR#40, +meetup_frankenjs Feed PR#50); Branch-Recovery nach master-Advance mitten in der Session; Mainfranken als feed-arm dokumentiert (nur 1 neuer valider Feed verifizierbar).
- **2026-06-26** · agent-5 informatik-uni-wue · Neuer statischer Scraper `informatik_uni_wue` [8d6f65a] für Institut für Informatik Uni Würzburg (eigene TYPO3, nicht im Uni-RSS → Abdeckungslücke). Parst schema.org-Microdata im event-list Block (startDate/endDate meta + name span), urljoin für relative/Geschwister-Domain-Links, broad=False, trust_tier=1; Vorlage thws_fiw; Fixture + 4 Tests; live found=5/kept=5/new=5; Suite 140 grün (pywebpush in venv nachinstalliert, fehlte lokal). → PR#53 offen.
- **2026-06-27** · agent-5-logo-proposals · informatik_uni_wue Scraper gemergt (PR#53→master); 3 hellere Logo-Kontrast-Varianten (V1/V2/V3) + index.html-Vergleichsseite als untracked Proposals in _scrape/logo-variants/ gebaut, visuell verifiziert, Preview-Server gestartet+gestoppt; kein Commit/PR (Proposals). Details in HANDOFF.notes.md.

## backlog

- documentation/features/event-radar-architecture.md schreiben (inkl. Ingestion/Connector-Sektion, ref Vault patterns/data-integration/connector-architecture.md)
- documentation/technical/README.md mit Nomenklatur + Dev-Env füllen
- uncommittete Änderungen (Logo/Rename/frontend/config/plans) committen sobald Git-Flow geklärt
- API-only-Boot entkoppeln: `app/feeds.py` soll `feed_loader` lazy importieren (und `adapters/__init__` nicht eager), damit `requirements.txt` allein die API startet — aktuell zieht der `/api/feeds`-Router icalendar/feedparser/bs4 transitiv (siehe requirements-ingest.txt-Header).
- HTML-Event-Scraper (eigene Adapter) für feed-lose Mainfranken-Quellen: ki-regio.de/veranstaltungen, TGZ Würzburg, IHK Würzburg, ZDI Mainfranken, Region Mainfranken (mainfranken.odoo.com), Landkreis Würzburg, gruenderzentren-wuerzburg.de — alle HTML-only (kein RSS/ICS).
## landmarks

*(keine)*

## inbox

*(leer)*
