# Scraper-Quellen-Recherche — HTML-Eventquellen ohne RSS/ICS (Mainfranken)

> **Typ:** Design-/Recherche-Doc (kein Status-Tracking). · **Scope:** Region Würzburg / Schweinfurt / Mainfranken, Themen IT / Tech / KI / Startup.
> **Auftrag:** Agent-2, Brief `task-research-scrapers` (2026-06-26). Komplementär zu Agent-5 (RSS/ICS-Feed-Kanal).
> **Ergebnis dieser Recherche:** Quellen, die **kein nutzbares RSS/ICS** haben und daher einen dedizierten Scraper bräuchten — bewertet nach Wert, Aufwand und Playwright-Bedarf.

## Methode

Vier parallele Web-Recherchen (IHK/Gründer · Hochschulen · Coworking/Community · Stadt/Region/Institutionen). Jede Kandidatenseite wurde **tatsächlich abgerufen** und auf Feed-Vorhandensein, Static-vs-SPA, extrahierbare Felder und Event-Dichte geprüft. Befunde anschließend gegen den **vorhandenen Adapter-Bestand** abgeglichen (entscheidend — mehrere „Top-Treffer" der Recherche sind bereits gebaut).

---

## 0. Bereits abgedeckt — NICHT neu bauen (Abgleich mit Code-Bestand)

Diese Quellen tauchten in der Recherche als Kandidaten auf, sind aber **schon implementiert**. Jeder neue Scraper darauf wäre redundant:

| Quelle | URL | Abdeckung | Mechanik |
|--------|-----|-----------|----------|
| THWS (hochschulweit) | `thws.de/termine` | `adapters/thws.py` | statisches HTML, eigener Parser |
| THWS FIW (Fak. Informatik) | `fiw.thws.de/termine` | `adapters/thws_fiw.py` | statisches HTML, eigener Parser |
| AI Week Mainfranken | `ai-week.de/programm` | `adapters/aiweek.py` | **JSON-Export** `backend.timetable.ai-week.de/export/session.json` — **kein Playwright nötig** |
| Eventbrite Würzburg (Tech/KI) | `eventbrite.*/würzburg/{science-and-tech, künstliche-intelligenz}` | `adapters/eventbrite_wue.py` | `__SERVER_DATA__`-JSON, `broad` (Keyword-Gate) |
| ZDI + Gründerzentren Würzburg | `zdi-mainfranken.de/events`, `gruenderzentren-wuerzburg.de/.../veranstaltungen` | `adapters/ics.py → ZdiGenIcsAdapter` (`zdi_gruenderzentren`) | Listing-Discovery + per-Event-`genIcs`-Export |
| Meetup-Gruppen, FRIZZ, nerd2nerd, Uni-Würzburg-RSS | div. | `feeds.yaml` (RSS/ICS) | data-driven Feed-Registry |

> **Korrektur zur Recherche:** AI Week wurde von einem Rechercheur als „Playwright-pflichtige SPA" eingestuft — falsch: der bestehende Adapter nutzt einen sauberen JSON-Export. Würzburg Web Week (`wueww.de`) läuft 2026 unter AI Week und ist damit bereits abgedeckt.

---

## 1. Neue Scraper-Kandidaten — priorisiert

Alle folgenden Quellen haben **kein** RSS/ICS und sind **nicht** durch einen bestehenden Adapter abgedeckt.

| # | Quelle | URL | IT-Relevanz | Dichte | Struktur | Playwright? | Felder (T/D/U/O/B/L) | Wert | Aufwand | Prio |
|---|--------|-----|:-----------:|:------:|----------|:-----------:|----------------------|:----:|:-------:|:----:|
| 1 | **Institut für Informatik, Uni Würzburg** | `informatik.uni-wuerzburg.de/aktuelles/veranstaltungen-und-termine/` | hoch | mittel | statisch (TYPO3) | nein | T D U◐ O◐ B L | **hoch** | niedrig | **1** |
| 2 | **Startbahn27 (Schweinfurt)** | `startbahn27.de` (Monatsgrid `/YYYY/month/MM`) | hoch | hoch | statisch (TYPO3) | nein | T D U◐ O◐ —/Detail L | **hoch** | mittel | **2** |
| 3 | **KI-Regio Mainfranken** | `ki-regio.de/veranstaltungen/` | hoch | mittel | statisch (WordPress) | nein | T D U◐ O◐ B L | **hoch** | niedrig | **3** |
| 4 | **Gründen in Mainfranken (GIM)** | `gim-bayern.de` (`#aktuelles`) | mittel-hoch | hoch | statisch | nein | T D U O L | **hoch** | niedrig | **4** |
| 5 | **Uni Würzburg Career Centre** | `uni-wuerzburg.de/career/veranstaltungen/<semester>/` | mittel | sehr hoch | statisch | nein | T D U O◐ B L | mittel-hoch | mittel | **5** |
| 6 | **Region Mainfranken GmbH** | `mainfranken.odoo.com/event` | mittel | mittel | statisch (Odoo) | nein | T D —/Detail O —/Detail L | mittel | niedrig | 6 |
| 7 | VHS Würzburg (IT/Digital) | `vhs-wuerzburg.info/.../beruf-it-...` | mittel | mittel | statisch | nein | T D U O B L | mittel | niedrig | 7 |
| 8 | 360° BASE | `360gradbase.de/events/` | mittel | mittel | statisch (WP) | nein | T —/Detail L | mittel-niedrig | mittel | 8 |

*Felder-Legende: T=Titel D=Datum U=Uhrzeit O=Ort B=Beschreibung L=Detail-Link. ◐ = teils / nur auf Detailseite.*

### Kurzbewertung der Top-Empfehlungen

**1 — Institut für Informatik, Uni Würzburg** · *Beste Einzel-Lücke.* Läuft auf einer **eigenen** TYPO3-Instanz (`informatik.uni-wuerzburg.de`), die **nicht** im zentralen Uni-RSS (`id=197207`) erscheint — echte Abdeckungslücke bei der thematisch kernrelevantesten Quelle (Informatik-Kolloquien, Projektpräsentationen, HCI/Games). Statisch, geringer Aufwand. Hinweis: Uhrzeit/Ort einzelner Kolloquien liegen auf Detailseiten → zweite Crawl-Ebene optional.

**2 — Startbahn27 (Schweinfurt)** · *Schließt die Schweinfurt-Lücke.* Bisher ist die Region fast nur Würzburg-zentriert; Startbahn27 ist das Schweinfurter Startup-Ökosystem (KI-Lunch-Pitches, FLIGHT-Sessions, BayStartUP). Dichtes Monatsgrid, statisches TYPO3. Aufwand mittel wegen Monats-Routing (`/YYYY/month/MM`) + Detailseiten für Uhrzeit/Beschreibung.

**3 — KI-Regio Mainfranken** · *Sauberste KI-Quelle ohne Feed.* Durchgehend KI-Themen für KMU mit klarem Mainfranken-Bezug (Würzburg, Bad Kissingen, Bad Neustadt). Statisches WordPress, alle Events im Markup, geringer Aufwand.

**4 — Gründen in Mainfranken (GIM)** · *Dedup-Aggregator.* Bündelt die Gründer-/Startup-Events der ganzen Region (IGZ, TGZ, ZDI, HWK, IHK, GRIBS, THWS) auf einer statischen Seite. Überschneidet sich mit dem bereits abgedeckten `zdi_gruenderzentren` → **Cross-Source-Dedup nötig** (der vorhandene `dedup_key`-Mechanismus greift). Mehrwert: erfasst HWK/IHK/GRIBS, die sonst nirgends abgedeckt sind.

**5 — Uni Würzburg Career Centre** · *Höchste Dichte, aber gemischt.* >100 Events/Jahr (Vorträge, Workshops, Sommerprogramm), nur ein Teil IT/KI → `broad`-Quelle mit Keyword-Gate. Achtung: Übersichts-URL rotiert pro Semester (`/sommersemester-2026/`) → Semester-Slug zur Laufzeit auflösen.

---

## 2. Playwright-pflichtig (JS-gerendert) — derzeit geringer Wert

| Quelle | URL | Status | Empfehlung |
|--------|-----|--------|-----------|
| IT-Verband Mainfranken e.V. | `it-mainfranken.org/it-events/` | thematisch ideal (reiner IT-Verband), aber **aktuell leer**; Events laufen primär über LinkedIn | **warten** — erst bauen wenn die Seite gefüllt wird; dann Playwright |
| IGZ Würzburg | `igz.de/events/` | WordPress-AJAX-Kalender, aktuell „keine Veranstaltungen" | niedrig — Inhalte ohnehin via GIM/`zdi_gruenderzentren` |
| Würzburg Web Week | `timetable.wueww.de` | **dormant 2026** (AI Week übernimmt) | nicht bauen; 2027 beobachten |
| IHK Würzburg-Schweinfurt | `wuerzburg.ihk.de/veranstaltungen/` | JS-nachgeladen; geringe IT-Reinheit (v.a. allg. Wirtschaft/Weiterbildung) | niedrig — startup-relevante Teile laufen über GIM |

> **Fazit Playwright:** Kein einziger der *empfohlenen* (Tier-1-)Scraper braucht Playwright — alles statisches, serverseitig gerendertes HTML (TYPO3/WordPress/Odoo). Playwright wäre nur für nachrangige bzw. aktuell leere Quellen nötig. **Empfehlung: vorerst keine Playwright-Abhängigkeit ins Projekt ziehen.**

---

## 3. Geprüft und verworfen

| Quelle | Grund |
|--------|-------|
| **Coworking Würzburg (cowowue)** | **Tot** — Betrieb zum 31.01.2025 eingestellt, Gebäude abgerissen |
| Neuraum, Nomad Coworking | keine öffentlichen, datierten Event-Listen (reine Venue-/Coworking-Seiten) |
| THWS CAIRO News | News-Artikel, keine strukturierten Events (kein Datum/Ort als Event) |
| THWS Gründung / Career Service | sehr dünn + Überschneidung mit `thws.py` (zentrale Terminseite) |
| Uni SFT Gründungsförderung | keine datierten Einzeltermine (nur Programmbeschreibung) |
| transform.RMF | redundant zum Region-Mainfranken-Odoo-Kalender (#6) |
| Bayern Innovativ | bayernweit, kein Geo-Filter → sehr wenige Würzburg-Treffer, viel Rauschen |
| Fraunhofer SCS / ISC | außerhalb der Region (Nürnberg) bzw. kein IT-Bezug (Silikatforschung) |
| `gruenden.wuerzburg.de` | zu dünn, überwiegend Verweise nach extern (Eventbrite) |
| StartUp-Barcamp, AI-Camp/Bar-Code | je 1 Event/Jahr → manuell erfassbar, Scraper-Wert gering |
| FrankenJS, Würzburg Software Dev Meetup | laufen über Meetup → **ICS** vorhanden, gehört in `feeds.yaml` (Agent-5), nicht hierher |
| STADTWERKSTATT / makerspace-wuerzburg.de | Verein noch in Gründung, kein aktiver Kalender — später beobachten |

---

## 4. Empfehlung (klar)

**Zuerst bauen — statische Scraper, kein Playwright, in dieser Reihenfolge:**

1. **Institut für Informatik, Uni Würzburg** — kernrelevant, echte Feed-Lücke, geringster Aufwand.
2. **KI-Regio Mainfranken** — sauberste KI-Quelle, geringer Aufwand (vor Startbahn27 ziehbar, da einfacher).
3. **Startbahn27** — schließt die Schweinfurt-Lücke; etwas mehr Aufwand (Monats-Routing).
4. **GIM (gim-bayern.de)** — breiter Gründer-Aggregator; mit Cross-Source-Dedup gegen `zdi_gruenderzentren`.
5. *(optional)* **Uni Career Centre** und **Region Mainfranken Odoo** als `broad`-Quellen mit Keyword-Gate, wenn mehr Breite gewünscht ist.

**Playwright:** vorerst **nicht** einführen — alle Top-Ziele sind statisch. Erst neu bewerten, wenn der **IT-Verband Mainfranken** seine Eventseite füllt (dann einziger hochwertiger Playwright-Fall).

**Architektur-Hinweis für die Umsetzung (Agent-5/Folgeauftrag):** Die statischen Kandidaten passen ins bestehende Muster reiner-Parser-Adapter (`thws.py`/`thws_fiw.py` als Vorlage: `parse_*(html)` pure + `fetch()` via `_http`). GIM/Career/Odoo als `broad: true` führen (gemischte Kalender → Keyword-Gate). Cross-Source-Dedup über den vorhandenen `dedup_key`.

---

## Verwandte Docs

- `documentation/features/event-feeds-verified.md` — verifizierte RSS/ICS-Feeds (Agent-5-Kanal).
- `documentation/features/event-sources-mainfranken.md` — breitere Quellen-Landschaft.
- `backend/app/ingest/feeds.yaml` — aktive RSS/ICS-Registry.
- `backend/app/ingest/adapters/` — bestehende Code-Adapter (Abgleich-Basis für Abschnitt 0).
