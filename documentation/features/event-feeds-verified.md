# Event-Feeds Mainfranken — verifizierte ICS/RSS-Schicht

**Stand:** 2026-06-25 · 4 parallele Recherche-Agenten (WebSearch + WebFetch, Feed-URLs live angefasst).
**Verhältnis zum Scraping-Katalog:** Ergänzt [`event-sources-mainfranken.md`](./event-sources-mainfranken.md).
Jener Katalog ist scraping-zentriert (Playwright, Slice 2); dieses Dokument isoliert die **maschinen-
lesbaren Feeds** — die robuste, ToS-saubere, billige Adapter-Schicht (ROADMAP **Slice 5**, teils schon
in Slice 2 als Seed nutzbar, um den `fetch()`-Adaptervertrag mit echten Daten zu beweisen).

> **Kernkorrektur zum Scraping-Katalog:** Meetup ist dort als SPA-Scrape (`__NEXT_DATA__`) gelistet.
> Tatsächlich hat **jede Meetup-Gruppe einen funktionierenden ICS-Endpunkt** (`/<slug>/events/ical/`,
> liefert `text/calendar`). Diese Gruppen gehören als **Feed-Adapter**, nicht als Scraper.

---

## A · Verifiziert funktionierend (sofort nutzbar)

| Quelle | Feed-Typ | Feed-URL (live geprüft) | IT/KI | Notiz |
|--------|----------|--------------------------|-------|-------|
| **Meetup — Würzburg Data & Analytics** | ICS | `https://www.meetup.com/wurzburg-data-analytics-meetup/events/ical/` | hoch | **Aktiv, aktuell mit Live-Event** (AI Week). Bester Live-Feed. ~633 Mitglieder. |
| **Meetup — Modern Software Development Würzburg** | ICS | `https://www.meetup.com/wuerzburg-software-development/events/ical/` | hoch | Sehr aktiv (letztes Event 03/2026, AI-Coding-Themen). ICS füllt sich vor Events. |
| **Meetup — Deep Learning Würzburg** | ICS | `https://www.meetup.com/Wurzburg-Deep-Learning-Meetup/events/ical/` | hoch | Größte KI-Gruppe (~1.066). Aktuell leer (letztes Event 02/2025). |
| **Meetup — FrankenJS / Front-End Würzburg** | ICS | `https://www.meetup.com/front-end-wuerzburg/events/ical/` | hoch | ~276 Mitglieder, evtl. einschlafend. ICS aktuell leer. |
| **ZDI / Gründerzentren Würzburg** (IGZ/TGZ/ZDI) | ICS (pro Event) | `…/veranstaltungen/index.html?_func=genIcs&_eopb=1&_id=<ID>` | hoch | TYPO3 `cal`. Per-Event-ICS verifiziert (ID 1913806 → valides VCALENDAR). **Feed des Kunden** → ZDI nach Gesamtkalender-/Partner-Feed fragen. |
| **FRIZZ Würzburg** (Stadtkalender) | RSS **+** ICS | RSS `https://frizz-wuerzburg.de/search/event/veranstaltungskalender/index.rss` · ICS `…/calendar.ics` | niedrig | Beide valide (RSS ~28 Items, ICS ~60 VEVENTs). **Kein IT-Filter** → Keyword-Filter zwingend. Randquelle. |

**Meetup-ICS-Mechanik:** Muster `https://www.meetup.com/<slug>/events/ical/`. Ist kein Event geplant, ist
die ICS **valide aber leer** (kein `VEVENT`) — normal, kein Defekt; sie befüllt sich automatisch vor dem
nächsten Event. Also dauerhaft abonnierbar.

## B · Wahrscheinlich Feed — 1 Verifikations-Klick fehlt

| Quelle | System | Vermuteter Endpunkt | IT/KI | Warum lohnend |
|--------|--------|---------------------|-------|---------------|
| **Startbahn27 Schweinfurt** | TYPO3 `sf_event_mgt` | `…?tx_sfeventmgt[action]=ics&[event]=<id>` (pro Event) | **hoch** | Stark KI-lastig („Top KI-Hacks", „AI Ecosystem Bayern"). **Füllt die Schweinfurt-Lücke** des Scraping-Katalogs. sf_event_mgt bringt ICS-Export standardmäßig mit. |
| **Region Mainfranken GmbH** | Odoo | `/event/<numerische-id>/ics` | mittel | Odoo exponiert i.d.R. ICS pro Event. Globaler `/event/ics` war 404. Am echten Event-Link testen. |

## C · Feed vorhanden, aber leer / tot (nicht drauf verlassen)

- **ZDI Mainfranken** (WordPress) `https://www.zdi-mainfranken.de/feed/` — valides RSS 2.0, **0 Event-Items** (Events liegen extern: pretix/hackation, Gründerzentren-Portal). → echte ZDI-Events über Quelle in Abschnitt A ziehen.
- **DevOps Würzburg Mainfranken** (Meetup) — **aufgelöst** (404, nur noch in Suchmaschinen-Cache).
- **Xing Events / New Work** — Geschäft **31.03.2023 eingestellt**, API tot.
- **Meetup Regions-Such-RSS** via `openrss.org`-Proxy — im Test **leer/unzuverlässig**. Nur Pro-Gruppe-ICS (Abschnitt A) ist verlässlich.

## D · Bestätigt feed-los → bleibt Scraper-Job (siehe Scraping-Katalog)

Inhaltlich die **wertvollsten** Quellen haben **keinen** Feed:
- **CAIDAS „AI Talks @JMU"** — wöchentlich (Di 16:15), höchste KI-Dichte der Region. Nur HTML.
- **THWS FIW / CAIRO**, **AI Week Mainfranken** (42 Events), **Bar-Code / AI Camp** (pretix), **IHK Würzburg-Schweinfurt**, **HWK Unterfranken**.
- **Eventbrite** — offizielle Such-API **seit 20.02.2020 abgeschaltet**; nur eigene Org-Events per API. Inoffizieller `eb-to-ical`-Workaround pro Organisator-ID existiert (ToS-Grauzone, instabil). → Scraping der Stadt-/Kategorie-Seiten.
- **Bitkom** (UI-PLZ-Filter, kein Feed), **heise/golem** (News-RSS ja, Event-Feed nein, kaum Regionalbezug).

---

## Empfehlung

1. **Seed-Schicht für Slice 2/5:** Die 4 Meetup-ICS (Abschnitt A) + ZDI/Gründerzentren-ICS sind near-free
   Feed-Adapter — ideal, um den `fetch() -> RawRecord`-Vertrag mit **echten** Daten zu beweisen, bevor der
   Playwright-Scraper die feed-losen Premium-Quellen (Abschnitt D) erschließt.
2. **ZDI-Partnerfeed früh klären** — als Projekt-Eigner ist ein offizieller Gesamtkalender-Feed realistisch
   und schlägt jedes Scraping.
3. **Startbahn27 verifizieren** (Abschnitt B) — billigster Weg zur Schweinfurt-Abdeckung.
4. **Feed vor Scrape**, wo eine Quelle in *beiden* Listen steht (Meetup, ZDI, Region Mainfranken): den
   Feed-Adapter nehmen, nicht den HTML-Scraper.

> Ehrlichkeits-Hinweis: Abschnitt B ist plausibel aus dem CMS-Typ abgeleitet, aber nicht endgültig per
> erfolgreichem ICS-Download bestätigt (Detailseiten gaben in der Tooling-Umgebung 404 — möglicher
> UA-/Redirect-Artefakt). Inoffizielle Workarounds (Eventbrite, Meetup-Proxy) können jederzeit brechen.
