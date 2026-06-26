---
type: handoff
vorhaben: 2026-hackathon
working_directory: /Users/larskohlmorgen/_clients/zdi/projects/coding/2026-hackathon/agent-3
created: 2026-06-25
last_updated: 2026-06-26-agent3-enrichment-modules
schema_version: "0.4"
status: slice1-deployed · master-orchestration · agent3-llm-weighting
---

# Handoff — 2026-hackathon

> **Adressat:** nächste Session. Bootstrap: `current_task` → `read_first_critical`, dann loslegen.

## current_task

Agent-3 (Branch agent/agent-3): LLM-Gewichtung der Events (Hybrid Taxonomie+Intent) per Claude Haiku. Implementierung LÄUFT. Fertig: backend/app/enrichment/taxonomy.py (12 Topic-Felder web_frontend/backend_cloud/data_ai/devops_platform/security/mobile/embedded_iot/product_ux/career_recruiting/community_networking/business_startup/research_academia + 4 Intent-Achsen deep_tech/recruiting/vendor_sales/networking als Slug->Label dicts + SLUGS-Tupel) und backend/app/enrichment/score.py (_call_llm getrennt von pure _normalize; _call_llm nutzt anthropic.Anthropic + settings.score_model + output_config json_schema mit enum-constrained topics[]/intents[]-Listen + confidence/evidence; _normalize droppt off-taxonomy + NEAR_ZERO<2, renormalisiert je Achse auf Summe 100, confidence clamp 0..1; is_enabled()=bool(anthropic_api_key) graceful, THIN_TEXT_MIN=120, text_hash sha256, build_text). DATEI-EIGENTUMS-GRENZE: Agent-2 arbeitet parallel am Quellen-/Sichtbarkeits-Badge in denselben Frontend-Dateien — ich fasse NUR weightBar/tagWeights/PLACEHOLDER_WEIGHTS in eventDisplay.js + .intent-Block/bar-Computed in EventCard.vue + Backend-Enrichment an; NICHT distinctSources/sourceMeta/Quellen-Badge/Rail-Boxen. **Nächster Schritt:** score.py um score_event(session,event)-Orchestrierung erweitern (THIN_TEXT_MIN-Guard, scored_text_hash-Cache-Vergleich -> skip wenn unverändert, _normalize-Ergebnis auf Event persistieren) + enrichment/__init__.py; dann models.py Event += topic_weights/intent_weights JSON + score_confidence float + score_model str + scored_text_hash str; config.py += anthropic_api_key='' + score_model='claude-haiku-4-5'; events.py EventOut += topic_weights/intent_weights/score_confidence (test_events_api EVENT_OUT_FIELDS anpassen); CLI score-Subcommand in ingest/__main__.py; requirements.txt += anthropic; dann pytest (LLM via _call_llm gemockt, KEIN echter Call; _normalize-Summe; hash-idempotenz; EventOut-Form); dann Frontend (eventDisplay.js Taxonomie-Farbkarte + weightBar echte topic_weights sonst Tag sonst PLACEHOLDER behalten + intentMix; EventCard.vue .intent echte Verteilung + geschätzt-Marker bei niedriger confidence); dann vite build. Häufig committen, push agent/agent-3, Master merged via PR.

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
- ANTHROPIC_API_KEY muss in backend/.env gesetzt werden, damit echtes Scoring läuft (von Lars/Master) — ohne Key degradet Enrichment graceful, Frontend zeigt Platzhalter-Balken
- HANDOFF-Frage offen: master-Version behalten oder frische agent-3-lokale HANDOFF? (durch diese Rolling-Konsolidierung jetzt agent-3-lokal, working_directory self-healed)

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
- **2026-06-26** · agent3-llm-weighting · Rebase auf origin/master, sync+venv-Fix (bs4), Auftrag LLM-Gewichtung gelesen, vollständiges Implementierungs-Design festgelegt (noch kein Code)
- **2026-06-26** · agent3-enrichment-modules · enrichment/{taxonomy,score}.py gebaut (12 Topics + 4 Intents, _call_llm/_normalize getrennt, Haiku structured output); NOTES-Triage erledigt; Rotation bei 282K

## backlog

- documentation/features/event-radar-architecture.md schreiben (inkl. Ingestion/Connector-Sektion, ref Vault patterns/data-integration/connector-architecture.md)
- documentation/technical/README.md mit Nomenklatur + Dev-Env füllen
- uncommittete Änderungen (Logo/Rename/frontend/config/plans) committen sobald Git-Flow geklärt
## landmarks

*(keine)*

## inbox

*(leer)*
