# Event Radar — Roadmap

**Produkt:** IT-Event-Aggregator für Mainfranken / ZDI. Aggregiert Events aus vielen
Quellen, matcht sie auf Nutzer-Interessen + Wohnort/Umkreis und zeigt sie als Liste und
auf der Karte. Strategisches Ziel: über reine Aggregation hinaus eigenes Angebot besitzen
(Veranstalter-Self-Service als Moat).

**Stack (gelockt):** Vue 3 + Vite (`frontend/`) · FastAPI + PostgreSQL/PostGIS
(`backend/`) · Redis (Queue + Cache) · Claude Haiku (Intent-Scoring) · Leaflet/OpenStreetMap
· Docker-Compose → x1pro.

**Leitprinzip Ingestion:** quell-agnostische Adapter → normalisiertes Schema → Dedup →
Enrichment → Moderation → Canonical Store. Jede Quelle ist nur ein Adapter mit
einheitlichem Vertrag — der Kern kennt die Quelle nie direkt.
Referenz: Vault `patterns/data-integration/connector-architecture.md`.

> **Reihenfolge-Entscheidung (bewusst, abweichend von der Taxonomie):** Die **erste
> Quelle ist ein Playwright-Scraper**, der eigenständig im definierten Umkreis nach
> Events sucht — nicht der taxonomisch „billigste" ICS/RSS-Input. Die Haus-Doktrin stuft
> Scraping als brüchigen Lückenfüller ein (Pflege, ToS-Risiko); hier ist der
> autonome Umkreis-Scraper bewusst das Fundament, weil er den eigentlichen
> Aggregations-USP für Mainfranken liefert. ICS/RSS und offene APIs kommen als
> robustere Quellen später dazu (Slice 5).

---

## Slices

### Slice 1 — Auth & Profil  ·  ✅ gebaut & gemergt
Fundament: Nutzer identifizieren und ihre Relevanz-Kriterien erfassen.

- Landing-Page (aus simplem Mockup `frontend/index.html` in Vue-App-Shell überführt)
- Google-OAuth (Authorization-Code-Flow, Authlib; httpOnly-Session-Cookie) — **live verdrahtet** (echte Google-Client-Creds in `backend/.env`, Redirect `…/api/auth/google/callback`)
- Datenmodell `User` + `Profile` (Interessen, Expertise, Wohnort/Geo, Suchumkreis)
- `vue-router`: `/` (Landing) + `/profile` + `/dashboard` (auth-only)
- **Scope:** lokal (Vite-Dev-Server :5173 + uvicorn :8000 + Postgres :5432). Kein x1pro.

→ Detailplan: `plans/event-radar-slice-1.md`
→ Stand: gebaut, gemergt, OAuth gegen echte Creds live.

### Slice 2 — Ingestion-Fundament  ·  ✅ gebaut & gemergt
Erste echte Daten im System — und das Pattern, auf dem alle weiteren Quellen aufsetzen.

- Kanonisches `Event`-Schema (Titel, Zeit, Ort/Geo, Beschreibung, Tags, URL)
- Adapter-Interface `fetch() -> Iterable[RawRecord]` (Kern kennt die Quelle nie direkt)
- Provenance pro Quell-Datensatz (`source_adapter, external_id, source_url, fetched_at,
  raw_payload, trust_tier`) + `origin_type` am kanonischen Objekt
- Idempotenter Upsert per `(source_adapter, external_id)` — Re-Runs duplizieren nie
- **Erste Quelle: Playwright-Umkreis-Scraper** — sucht eigenständig im definierten
  geografischen Umkreis (Mainfranken / Profil-Radius) nach IT-Events und mappt die
  Treffer auf das kanonische Schema:
  - Playwright (headless) als Adapter hinter demselben `fetch()`-Vertrag
  - Umkreis-/Suchlogik **konfigurierbar** (Ort + Radius, Keywords) — **Default fix auf
    Mainfranken**, aber als Config-Parameter angelegt, damit der Scope ohne Code-Änderung
    erweitert werden kann (Ziel: später global)
  - `origin_type = scrape`, niedriger `trust_tier` → später Moderationspflicht (Slice 6)
  - Robustheit: Retries, Rate-Limit, Fehler-Isolation als entkoppelter Worker

→ Detailplan: `plans/event-radar-slice-2.md`
→ Quellen + Zielschema: `documentation/features/event-sources-mainfranken.md`
→ Stand: gebaut & gemergt. **9 registrierte Adapter** live (eventbrite_wue, meetup + 4 Meetup-ICS, thws_fiw, frizz_wuerzburg/RSS, zdi_gruenderzentren/ICS), idempotenter Upsert, Keyword-/Geo-Filter. Echte Events in Postgres.

### Slice 3 — Event-Anzeige  ·  🔄 in Arbeit
Aus Daten wird ein sichtbares Produkt.

- ✅ Event-Such-API `GET /api/events` (q/city/tag/date/is_online, Pagination, „kommende zuerst")
- ✅ Event-Liste + Suchmaske (geteilt) — Public Index (logged-out) & Dashboard (logged-in), identische Item-Darstellung
- 🔄 **Rich Event Card** (Ground-News-Optik adaptiert, bestehende Mainfranken-Farben):
  - Tag-Chips + **Gewichtungs-Bar** (Tag-Spektrum; aktuell gleichmäßiger Split pro Tag, später LLM-gewichtet → Slice 4)
  - **Quellen-Abgleich**-Zeile: „gefunden auf N Quellen" mit Plattform-Chips + **Blindspot-Badge** (1 Quelle) — voll aussagekräftig mit Dedup (Slice 5)
  - **Rating-Bereich** (Slot vorbereitet, rendert nur falls Bewertungsdaten vorhanden)
  - Identische Breite/Höhe in logged-in & logged-out
- ⬜ Leaflet-Karte mit Event-Markern (OpenStreetMap)
- ⬜ PostGIS-Umkreis-Filter gegen Profil-Wohnort + Suchumkreis
- ✅ Filter nach Profil-Interessen / Tags (Dashboard-Vorbelegung aus Profil)

### Slice 4 — Enrichment & Personalisierung  ·  🔄 in Arbeit
Personalisierung, gespeicherte Events und saubere Geo-Daten.

- 🔄 **Merken / Bookmarks** — gespeicherte Events pro Nutzer (`Bookmark`-Model + `GET/POST/DELETE /api/bookmarks`, auth-gated; „Merken"-Button auf der Card). Speist die Rail-Box „Demnächst gespeichert".
- ⬜ Claude-Haiku **Intent-/Relevanz-Scoring**: Event ↔ Profil-Interessen → personalisiertes Ranking **und** treibt die **Gewichtungs-Bar** der Card (ersetzt den aktuellen gleichmäßigen Tag-Split durch echte LLM-Gewichte)
- ⬜ Geocoding (Nominatim) für Orte ohne Koordinaten — entkoppelt, per Hash gecacht
- ⬜ Enrichment nur für Neues, Ergebnis gecacht

### Slice 5 — Multi-Source & Dedup  ·  ⬜
Breite Abdeckung ohne Duplikate.

- Weitere, robustere Adapter: **ICS/RSS-Feeds** (billigster sauberer Input) und
  offene APIs (Meetup / Luma / Eventbrite) — ergänzen den Scraper aus Slice 2
- Dedup / Canonicalization als eigene Stufe (Fuzzy-/Embedding-Match + Zeit + Geo):
  N Quell-Rows → 1 kanonisches Event, „gefunden auf N Quellen"
  → macht die in Slice 3 gebaute **Quellen-Abgleich-UI** (Plattform-Chips + Blindspot-Badge)
  erst voll aussagekräftig: bis dahin ist fast jedes Event 1-Quelle (= Blindspot)
- Redis-Queue-Worker pro Quelle (Retries, Rate-Limit, Fehler-Isolation) —
  entkoppelt vom Hauptprozess

→ Verifizierte Feed-Quellen (ICS/RSS, live geprüft): `documentation/features/event-feeds-verified.md`

### Slice 6 — Supply & Moderation  ·  ⬜
Eigenes Angebot besitzen statt nur fremde Kopien — der eigentliche Moat.

- Veranstalter-Self-Service: Event-Einreichung über eigenes Portal
- Crowd-Einreichung als Cold-Start-Brücke
- Moderations-Queue (`pending → published`) für Scrape-/Crowd-/Self-Service-Quellen

### Slice 7 — Deploy & Notify  ·  ⬜
Live gehen und Nutzer halten.

- Docker-Compose (frontend + api + postgres + redis) → x1pro
  (Haus-Policy: commit → push → `git pull` + `docker compose up --build`, kein SCP)
- Google-Redirect-URIs um Testserver-Domain ergänzen, End-to-End-Smoke-Test
- „Bleib verbunden"-Benachrichtigungen (neue passende Events) für Retention

---

## Reihenfolge-Begründung
Erst ein Nutzer mit Relevanz-Kriterien (1), dann das Ingestion-Pattern mit dem
**Playwright-Umkreis-Scraper als erster Quelle** (2) — bewusst die fragilste, aber für
Mainfranken USP-tragende Quelle zuerst, statt dem taxonomisch billigsten ICS/RSS-Input.
Danach Sichtbarkeit (3) und Personalisierung (4). Robustere Quellen (ICS/RSS, APIs),
Breite und Dedup kommen, sobald das Fundament steht (5). Eigenes Supply (6) löst den
Cold-Start erst, nachdem Aggregation trägt. Deploy (7) am Ende des ersten tragfähigen
Produktkerns — Slice 1 bleibt bewusst lokal.
