# Event-Quellen Mainfranken — Scraping-Katalog (Slice 2)

**Stand:** 2026-06-25 · Recherche per WebSearch + WebFetch (alle URLs live verifiziert, sofern
nicht als *unverifiziert* markiert). Region: Unterfranken/Mainfranken (Würzburg, Schweinfurt,
Aschaffenburg, Kitzingen, Bad Kissingen, Main-Spessart, Haßberge, Rhön-Grabfeld, Miltenberg).

Zweck: Input für den **Playwright-Umkreis-Scraper** (Slice 2 der ROADMAP). Jede Quelle ist ein
Adapter hinter `fetch() -> Iterable[RawRecord]`; der Scraper läuft periodisch und füttert das
kanonische Event-Schema (unten). Default-Scope fix auf Mainfranken, per Config erweiterbar.

---

## Priorisierter Quellen-Katalog

Legende Prio: **1** = sofort, **2** = später/periodisch, **3** = eher nicht / erst verifizieren.
Render: `static` = HTML server-seitig (HTTP-Fetch reicht) · `spa` = JS-gerendert (Playwright nötig).

| # | Quelle | Listing-URL | Typ | IT | Feed | Render | Freq | Prio |
|---|--------|-------------|-----|----|----|--------|------|------|
| 1 | **Gründerzentren Würzburg** (ZDI/IGZ/TGZ gebündelt) | https://www.gruenderzentren-wuerzburg.de/gruenderzentren/veranstaltungen/index.html | organizer | hoch | **ICS/Event** (`genIcs`) | static | wöch. | **1** |
| 2 | ZDI Mainfranken — Events (Teaser) | https://www.zdi-mainfranken.de/events/ | organizer | hoch | – | static | lfd. | 1¹ |
| 3 | THWS — Gründung: News & Events | https://www.thws.de/forschung/gruendung/news-und-events/alle-termine-und-veranstaltungen/ | institution | hoch | – | static | mittel | **1** |
| 4 | THWS — Fak. Informatik & Wirtschaftsinformatik | https://fiw.thws.de/termine/ | institution | hoch | – | static | mittel | **1** |
| 5 | Eventbrite — Würzburg Science & Tech | https://www.eventbrite.com/b/germany--w%C3%BCrzburg/science-and-tech/ | aggregator | hoch | – | static | mittel-hoch | **1** |
| 6 | Eventbrite — Würzburg Künstliche Intelligenz | https://www.eventbrite.de/d/germany--w%C3%BCrzburg/k%C3%BCnstliche-intelligenz/ | aggregator | hoch | – | static | mittel | **1** |
| 7 | Meetup — Würzburg DATA & ANALYTICS | https://www.meetup.com/wurzburg-data-analytics-meetup/ | community | hoch | – | spa² | monatl. | **1** |
| 8 | Meetup — Analytics Pioneers Würzburg | https://www.meetup.com/analytics-pioneers-wurzburg/ | community | hoch | – | spa² | wöch. | **1** |
| 9 | Region Mainfranken GmbH (Odoo) | https://mainfranken.odoo.com/event | network | mittel | ICS/Event³ | static | lfd. | **1** |
| 10 | FRIZZ Würzburg — Veranstaltungskalender | https://frizz-wuerzburg.de/search/event/veranstaltungskalender/ | media | niedrig-mittel | **RSS + ICS** | static | tägl. | **1**⁴ |
| 11 | IHK Würzburg-Schweinfurt — Veranstaltungen | https://www.wuerzburg.ihk.de/veranstaltungen/ | institution | mittel-hoch | – | spa (Sweap.io) | hoch | 2 |
| 12 | THWS — Termine (Hochschule gesamt) | https://www.thws.de/termine/ | institution | mittel | – | static | mittel | 2 |
| 13 | BayStartUP — Termine | https://www.baystartup.de/termine | organizer | hoch | – | static⁵ | hoch | 2 |
| 14 | TH Aschaffenburg — Veranstaltungen | https://www.th-ab.de/hochschule/aktuelles/veranstaltungen | institution | mittel | – | static? | mittel | 2 |
| 15 | Uni Würzburg (JMU) — Veranstaltungen | https://www.uni-wuerzburg.de/aktuelles/veranstaltungskalender/ | institution | mittel | – | static (URL-Pagination) | hoch | 2 |
| 16 | FabLab Würzburg — Events | https://fablab-wuerzburg.de/events | organizer | mittel | **ownCloud-Cal + RSS** | static | niedrig | 2⁴ |
| 17 | AI Week Mainfranken — Programm | https://www.ai-week.de/programm.php | festival | hoch | – | spa (Hash-Router) | **jährl.** | 2⁶ |
| 18 | baiosphere — KI-Events Bayern | https://baiosphere.org/events/ | network | hoch | – | spa | lfd. | 2⁷ |
| 19 | Stadt Würzburg — Veranstaltungen | https://www.wuerzburg.de/events-termine/516668.Veranstaltungen.html | media | niedrig | – | static (Kat.-Filter) | hoch | 2⁴ |
| 20 | Meetup — Deep Learning Würzburg | https://www.meetup.com/wurzburg-deep-learning-meetup/ | community | hoch | – | spa² | niedrig | 2 |
| 21 | Meetup — WUE.tech | https://www.meetup.com/de-DE/wue-tech/ | community | hoch | – | spa² | niedrig | 2 |
| 22 | Meetup — FrankenJS Würzburg | https://www.meetup.com/front-end-wuerzburg/ | usergroup | hoch | – | spa² | niedrig⁸ | 2 |
| 23 | Meetup — Modern Software Dev Würzburg | https://www.meetup.com/de-de/wuerzburg-software-development/ | usergroup | hoch | – | spa² | niedrig | 2 |
| 24 | Meetup — Web Development Aschaffenburg | https://www.meetup.com/de-de/web-development-aschaffenburg/ | usergroup | hoch | – | spa² | niedrig | 2 |
| 25 | Bar-Code / AI Camp Würzburg | https://www.ai-barcamp.de/ · https://www.bar-code.io/ | community | hoch | – | static | **jährl.** | 3⁶ |
| 26 | StartUp & Innovations Barcamp Würzburg | https://www.startup-barcamp.tech/ | community | mittel-hoch | – | static | **jährl.** | 3⁶ |
| 27 | Handwerkskammer Unterfranken — Veranstaltungen | https://www.hwk-ufr.de/artikel/aktuelle-veranstaltungen-webinare-und-workshops-78,0,6052.html | institution | niedrig-mittel | – | static? | mittel | 3 |
| 28 | GRIBS / Startbahn27 Schweinfurt | https://startbahn27.de/ | organizer | mittel | ? | ? | ? | 3⁹ |

**Fußnoten**
1. ¹ Inhaltlich von #1 abgedeckt (selber Träger) — nicht doppelt scrapen, #1 ist die Datenquelle; #2 nur als Sicht-/Highlight-Check.
2. ² Meetup ist Next.js-SPA, aber Events liegen strukturiert im `__NEXT_DATA__`-JSON des initialen HTML → oft HTTP+JSON-Parse statt Playwright möglich. Cloudflare-Bot-Schutz → niedrige Frequenz, echter Browser-Fingerprint.
3. ³ Odoo liefert ICS i.d.R. pro Event (`/event/<id>/ics`); globaler `/event/ics` war 404.
4. ⁴ **Breiter Kalender ohne IT-Kategorie** → Keyword-Filter auf Titel zwingend (KI/AI, Hackathon, Web, Daten, Digital, Cyber, Dev, Startup).
5. ⁵ Liste server-gerendert (~40 Events), Filter per JS; **Geo-Filter zwingend** (viel München/Nürnberg/online).
6. ⁶ **Jährliches Festival/Einzelevent** — Scraper muss tolerieren, dass die Liste die meiste Zeit leer/historisch ist (kein Fehler). Hohe IT-Relevanz im Saisonfenster.
7. ⁷ Bayernweit → Region-Filter Mainfranken zwingend. Listing rendert client-seitig („Loading…"), JSON-Backend-Call suchen.
8. ⁸ Mehrere Würzburger Meetup-Gruppen aktuell pausiert (letzte Events 2024) — Wert nur bei periodischer Abfrage, daher gelistet statt verworfen.
9. ⁹ Event-Listing-URL nicht bestätigt — wichtig für **Schweinfurt-Abdeckung**, zuerst URL verifizieren, dann hochstufen.

---

## Ausgeschlossen (bewusst)

- **LinkedIn Events** · **Facebook Events** · **XING/New Work** — harte Login-Wand + ToS-Verbot für Scraping. Nicht scrapen (deckt sich mit Haus-Doktrin, vgl. Vault `linkedin-session-management`).
- **heise events/conferences** — bundesweit/München, kein Mainfranken-Bezug → außerhalb Scope.
- **Luma (lu.ma)** — kein region-gefiltertes Mainfranken-Listing auffindbar; in DACH-Provinz kaum genutzt.
- **wuerzblog.de** — Bot-Block (HTTP 403) + unstrukturierte Blog-Posts statt Kalender.

## Geografische Lücken

Bad Kissingen, Rhön-Grabfeld, Haßberge, Main-Spessart, Miltenberg, Kitzingen haben **keine
dedizierten IT-Listings**. Diese Orte erscheinen nur, wenn Events dort über die regionalen
Aggregatoren (#5/#6/#9/#17) eingestellt werden. Echte Abdeckung → später lokale Quellen
oder Veranstalter-Self-Service (ROADMAP Slice 6).

---

## Ziel-Datenschema (Scraper-Result)

Jeder Adapter liefert pro Event einen **`RawEventRecord`** (normalisiert + Provenance). Der Kern
kennt nur dieses Schema, nie die Quelle direkt. Felder ohne Wert bleiben `null` (Enrichment in
Slice 4 füllt Geo nach).

```python
# Result-Vertrag des Scrapers (ein Record pro gefundenem Event)
class RawEventRecord:
    # --- Provenance (Connector-Pflicht) ---
    source_adapter: str          # z.B. "eventbrite_wue_tech", "meetup", "thws_fiw"
    external_id: str             # stabile ID der Quelle; Fallback: sha256(source_url|title|start)
    source_url: str              # kanonische Event-Detail-URL (Beleg + Dedup-Anker)
    fetched_at: datetime         # UTC, Zeitpunkt des Scrapes
    raw_payload: dict            # Original-Rohfelder der Quelle (Debug/Re-Parse)
    origin_type: str = "scrape"  # scrape | feed | api | organizer | crowd
    trust_tier: int              # 1=hoch (Institution/Feed) … 3=niedrig (offener Scrape)

    # --- Kanonische Event-Felder ---
    title: str                   # Pflicht
    description: str | None
    start: datetime              # mit Zeitzone (Europe/Berlin); Pflicht
    end: datetime | None
    is_online: bool = False

    # Ort
    venue_name: str | None       # z.B. "ZDI Cube"
    address: str | None
    city: str | None             # z.B. "Würzburg"
    postal_code: str | None
    lat: float | None            # falls Quelle liefert, sonst Slice-4-Geocoding
    lng: float | None

    # Klassifikation
    organizer: str | None
    tags: list[str]              # Roh-Kategorien/Keywords der Quelle
    url: str | None              # Anmelde-/Ticket-URL (falls != source_url)
    image_url: str | None
    price: str | None            # Freitext ("kostenlos", "ab 49 €")
    language: str | None         # "de" | "en"
```

**Verarbeitungs-Regeln (im Kern, nicht im Adapter):**
- **Idempotenter Upsert** per `(source_adapter, external_id)` — Re-Runs duplizieren nie.
- **Dedup/Canonicalization** (Slice 5) über Quellen hinweg: Fuzzy-Titel + `start` + Geo → 1
  kanonisches Event, `seen_on = [source_adapter, …]` („gefunden auf N Quellen").
- **Moderation** (Slice 6): `origin_type=scrape` mit niedrigem `trust_tier` → `pending` bis
  freigegeben (besonders bei breiten Kalendern #10/#19 nach Keyword-Filter).
- **Geo-Enrichment** (Slice 4): fehlende `lat/lng` aus `address`/`city`/`venue_name` via
  Nominatim, per Hash gecacht.

---

## Empfehlungen für die Slice-2-Umsetzung

1. **Erste 3 Adapter** (höchster Ertrag / geringster Aufwand): **#4 THWS-FIW** (static, deckt
   Schweinfurt mit ab), **#5/#6 Eventbrite** (static Cards, klar IT), **#7/#8 Meetup**
   (`__NEXT_DATA__`-JSON, aktivste Gruppen). Damit ist der Adapter-Vertrag an statisch + JSON +
   SPA-Light erprobt, bevor echte SPA-/Festival-Quellen (#11/#17/#18) drankommen.
2. **Feed-First, wo vorhanden** — auch wenn die erste Quelle bewusst ein Scraper ist: #1 (ICS),
   #10 (RSS+ICS), #16 (ownCloud-Cal), #9 (Odoo per-Event-ICS) sind robuster und gehören als
   Feed-Adapter in Slice 5. Bei #1 (ZDI = Projekt-Eigner) ist ein **Partner-Feed** realistisch
   und schlägt Scraping — früh mit ZDI klären.
3. **Keyword- + Geo-Filter** als gemeinsame Kern-Stufe, nicht pro Adapter — sonst Kultur-/
   Nicht-Mainfranken-Flut bei #10/#13/#15/#19.
4. **Saison-Toleranz** für #17/#25/#26 (jährliche Festivals): leere/historische Liste ist kein
   Scrape-Fehler.

## Offene To-dos aus der Recherche
- GRIBS/Startbahn27 (#28) Event-Listing-URL verifizieren (Schweinfurt-Lücke).
- IHK-Sweap-Portal (#11) mit Playwright auf JSON-Backend-Endpoints inspizieren (Sweap.io hat oft JSON-APIs).
- `genIcs`-Endpoint von #1 live abgreifen (direkter Termin-Pull ohne HTML-Parse).
- Render-Verhalten von #14 (TH-AB) und #15 (Uni WÜ) am Live-Scrape verifizieren (Best-Guess static).
