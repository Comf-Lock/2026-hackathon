# Notes — 2026-hackathon (2026-06-27)

## Logo-Kontrast-Varianten — Proposals, warten auf Lars' Wahl

**Problem:** `frontend/public/logo.svg` zeigt die Radar-Ringe dunkel auf dunkel (`#38414f`-Ringe auf `#1d2530`-Quadrat) → kaum erkennbar. Lars mag den Kontrast nicht.

**Geliefert (reine Proposals, untracked in `_scrape/logo-variants/`, KEIN Commit, KEIN PR — so vom Brief verlangt):**

- **`logo-current.svg`** — Kopie des Ist-Zustands zum Vergleich.
- **`logo-v1.svg` — Hellere Ringe:** dunkles Quadrat beibehalten, Ringe in aufgehelltem Kühl-Grau `#8b9bb3` (Deckkraft nach außen abnehmend 1→0.65), Fadenkreuz `#586679`, Stroke 1.6. Behutsamste Änderung, Look bleibt nah am Original.
- **`logo-v2.svg` — Invertiertes Quadrat:** helles Tile `#eef1f6` mit dunklen Ringen `#33404f` → maximaler Kontrast, Ringe sofort lesbar. Blip auf Dunkelteal `#138a6d` gezogen, damit er auf hell hält.
- **`logo-v3.svg` — Leuchtende Brand-Ringe:** Brand-Teal `#36c5a0` mit weichem Glow-Filter auf fast schwarzem Quadrat `#16201d`, Sweep+Blip ebenfalls Teal, Zentrum bleibt Rosé `#b8324f` (Zwei-Farben-Identität). Der Radar „leuchtet".
- **`index.html`** — Vergleichsseite: alle 4 nebeneinander, je auf hellem + dunklem Hintergrund + in klein (Favicon-Maßstab), beschriftet.

Alle behalten `viewBox 0 0 240 64` und die Gesamt-Komposition (Mark + Wortmarke). Visuell via `qlmanage`-Render geprüft: Ringe in allen 3 Varianten klar sichtbar (vs. quasi unsichtbar im Ist).

**Preview:** wurde über `python3 -m http.server 8092 --directory _scrape/logo-variants` serviert; Server auf Lars' Wunsch wieder **gestoppt** (Port frei). Zum erneuten Vergleich Server neu starten und `http://localhost:8092/index.html` öffnen.

**Folgeauftrag (offen):** Lars wählt V1/V2/V3 → gewählte Variante wird ins getrackte `frontend/public/logo.svg` übernommen (dann committen + PR). Bis dahin nichts am getrackten Logo geändert.
