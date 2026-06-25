---
type: handoff
vorhaben: 2026-hackathon
working_directory: /Users/larskohlmorgen/_clients/zdi/projects/coding/2026-hackathon/master
created: 2026-06-25
last_updated: 2026-06-25-event-radar-slice1
schema_version: "0.4"
status: event-radar · slice-1 · architecture
---

# Handoff — 2026-hackathon

> **Adressat:** nächste Session. Bootstrap: `current_task` → `read_first_critical`, dann loslegen.

## current_task

Produkt 'Event Radar' (IT-Event-Aggregator für Mainfranken/ZDI). Onboarding + Stack-Lock + Mockups + Architektur stehen. Stack: Vue 3+Vite (frontend/, läuft auf localhost:5173) + FastAPI+PostgreSQL/PostGIS + Redis + Claude Haiku (Intent) + Docker→x1pro. Logo gebaut (frontend/logo.svg). Vertikaler Slice 1 ist definiert und geplant (plans/event-radar-slice-1.md), aber NOCH NICHT gebaut. **Nächster Schritt:** Prereqs mit Lars klären (Google-OAuth-Client + Testserver-Ziel), dann Slice 1 bauen: FastAPI-Backend (Google-OAuth-Login, User+Profile-Modell, /api/auth + /api/profile) + Vue-Überführung des Mockups mit Login-Button + Profilseite, deploy auf x1pro.

## active_plans

*(keine)*

## read_first_critical

1. *(diese Datei)*

## open_questions

- Google-OAuth-Client (Client-ID/Secret + Redirect-URIs) — von Lars anzulegen/autorisieren
- Testserver-Ziel für Slice-1-Deploy: x1pro? welche Domain/Subdomain?
- Git-Flow: Branch-Protection auf master lockern (B) oder über PRs bleiben (A)? PR #1 offen: https://github.com/Comf-Lock/2026-hackathon/pull/1
- Mockup-Richtung: simpel (frontend/index.html) vs. dicht (frontend/dashboard.html) — Lars-Feedback offen
- Veranstalter-Anmeldung als bewusstes Produktziel mit aufnehmen (vs. erst nur Aggregation)?

> **Kaltzone:** decisions_made, Iteration History, Backlog und Landmarks liegen unterhalb dieses Markers — per `Read` vollständig nachladen bei Bedarf.
<!-- /hot-context -->

## decisions_made

*(keine)*

## Iteration History

- **2026-06-25** · event-radar-slice1 · Onboarding, Stack-Lock (vue-vite+fastapi-postgres), Event-Radar-Rebrand+Logo, Architektur+Connector-Vault-Doc, Slice-1-Plan

## backlog

- documentation/features/event-radar-architecture.md schreiben (inkl. Ingestion/Connector-Sektion, ref Vault patterns/data-integration/connector-architecture.md)
- documentation/technical/README.md mit Nomenklatur + Dev-Env füllen
- uncommittete Änderungen (Logo/Rename/frontend/config/plans) committen sobald Git-Flow geklärt
## landmarks

*(keine)*

## inbox

*(leer)*
