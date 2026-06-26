# Event Radar

**Der IT-Event-Aggregator für Mainfranken.** Event Radar sammelt Tech-, KI-, Startup- und
Developer-Veranstaltungen aus der Region Würzburg/Mainfranken automatisch aus vielen Quellen,
führt Dubletten zusammen und macht sie an **einer** Stelle durchsuchbar — statt sie über
Meetup, Eventbrite, Hochschul-Kalender, IHK und ein Dutzend RSS-Feeds verstreut zu lassen.

> Hackathon-Projekt 2026 für das Zukunftszentrum Digitalisierung (ZDI) / Mainfranken.

## Das Problem

IT-Veranstaltungen in der Region sind über viele Plattformen verteilt. Wer nichts verpassen
will, muss Meetup, Eventbrite, THWS-Kalender, ZDI, IHK und diverse Vereins-Feeds einzeln
abklappern. Dasselbe Event taucht oft mehrfach auf — und man sieht nie, wie gut ein Event
wirklich zu den eigenen Interessen passt.

## Die Lösung

Event Radar zieht alle Quellen automatisch zusammen, **dedupliziert quell-übergreifend** und
reichert jedes Event an: Geokodierung (Karte + Umkreissuche), LLM-gestützte thematische
Einordnung und ein Sichtbarkeits-Signal, das zeigt, ob ein Event nur an einer einzigen Stelle
gelistet ist. Eingeloggte Nutzer bekommen über ihr Profil (Interessen, Expertise, Wohnort,
Suchradius) personalisierte, verfeinerte Ergebnisse.

## Features

- **Aggregation aus vielen Quellen** — Meetup, Eventbrite, THWS (FIW + Hochschul-Kalender),
  ZDI/Gründerzentren, AI Week, nerd2nerd, Uni Würzburg u. a.; neue RSS/ICS-Feeds lassen sich
  zur Laufzeit über die API registrieren (data-driven, kein Code-Deploy nötig).
- **Cross-Source-Deduplizierung** — dasselbe Event aus mehreren Quellen wird zu einem
  zusammengeführt; die Herkunft („woher kam das") bleibt nachvollziehbar.
- **Reiche Event-Karte** — thematische Pills, ein LLM-gewichteter Themen-/Intent-Balken und
  ein **Sichtbarkeits-Signal** (z. B. „nur 1 Quelle").
- **Such-, Kalender- und Kartenansicht** — Liste/Suche, Wochen-/Monats-/Jahres-Kalender und
  eine Leaflet-Karte mit Event-Pins.
- **Echte Umkreissuche** — Filter nach Luftlinie (Haversine) um den Profil-Wohnort oder einen
  gesuchten Ort.
- **Vergangene & laufende Events** — nicht nur zukünftige; alles, was auf den Quellen noch
  gelistet ist.
- **Profil & Personalisierung** — Google-Login, Interessen/Expertise, Wohnort, Suchradius;
  Bookmarks zum Merken.
- **Installierbare PWA** — mobil-optimiert, „zum Homescreen hinzufügen".

## Tech-Stack

| Schicht | Technologie |
|---------|-------------|
| Frontend | Vue 3 + Vite, Leaflet (Karte), PWA (vite-plugin-pwa) |
| Backend | FastAPI, SQLModel |
| Datenbank | PostgreSQL |
| Anreicherung | Claude (LLM-Scoring), Nominatim/OpenStreetMap (Geocoding) |
| Auth | Google OAuth (signierter httpOnly-Session-Cookie) |

Architektur: quell-agnostische **Adapter** (`SourceAdapter`-Vertrag) liefern `RawEventRecord`s,
ein idempotenter Upsert auf `(source_adapter, external_id)` schreibt kanonische `Event`s mit
Provenance. Details: [`documentation/technical/README.md`](documentation/technical/README.md).

## Lokales Setup

**Voraussetzung:** PostgreSQL lokal erreichbar.

```bash
# Backend
cd backend
cp .env.example .env          # DATABASE_URL / OAuth / API-Keys eintragen
.venv/bin/uvicorn app.main:app --reload    # API auf http://localhost:8000  (Swagger: /docs)

# Events einlesen + anreichern (in einem zweiten Terminal)
python -m app.ingest run      # Quellen scrapen + dedupliziert speichern
python -m app.ingest geocode  # Adressen → Koordinaten
python -m app.ingest score    # LLM-Themengewichtung

# Frontend
cd frontend
npm install
npm run dev                   # http://localhost:5173 (proxyt /api → :8000)
```

Ports: Frontend `5173` · API `8000` · Postgres `5432`.

> **Secrets** gehören ausschließlich in `backend/.env` (gitignored). `.env.example` enthält nur
> Platzhalter — niemals echte Keys committen.

## Repo-Struktur

```
backend/        FastAPI-App, Ingest-Adapter, LLM-Scoring, Auth
frontend/       Vue-3-SPA (Liste/Kalender/Karte/Profil), PWA
documentation/  technische Doku + Feature-Specs
plans/          aktive Implementierungspläne
```

---

## AI Tool Setup (Mitwirkende)

Default-Branch: **`master`**. Nach dem Klonen einmalig im Chat aufrufen: `project setup` — der
`project-setup`-Skill (unter `skills/project-setup/`) legt lokal die nötigen Tool-Symlinks an
(idempotent).

### Bei Git-Worktrees

    2026-hackathon/
    ├── master/                ← Master-Checkout
    └── agent-<n>/             ← Worktree pro Agent

Jeder Worktree braucht einen eigenen `project setup`-Aufruf.
