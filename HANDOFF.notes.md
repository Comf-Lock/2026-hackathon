# Notes — 2026-hackathon (2026-06-25 · master-orchestration)

Master-Agent-Session: Pull/Deploy + Verteilung der Event-Plattform-Arbeit auf 3 Worker-Agenten.

## Task-Verteilung (Briefs liegen je in `<worktree>/_scrape/inbox/`)

| Agent | Worktree / Branch | Brief | Track |
|-------|-------------------|-------|-------|
| Agent-3 | agent-3 / `agent/agent-3` | `task-scraper-events-api.md` | Backend: Scraper-CLI (ICS/RSS-Adapter Mainfranken) + `GET /api/events` |
| Agent-1 | agent-1 / `agent/agent-1` | `task-index-searchmask.md` | Frontend: Index/logged-out + geteilte `SearchMask.vue` (Eigentümer) |
| Agent-2 | agent-2 / `agent/agent-2` | `task-dashboard-loggedin.md` | Frontend: Dashboard/logged-in, konsumiert SearchMask, Profil-Personalisierung |

## Fixierte Contracts (in allen Briefs identisch — Single Source of Truth)

**API:** `GET /api/events?q=&city=&tag=&date_from=&date_to=&is_online=&limit=20&offset=0`
→ `{ "total": int, "items": [EventOut, …] }`, EventOut = alle Event-Felder (models.py).
Agent-3 implementiert; Agent-1/2 bauen gegen Mock bis live.

**Komponente:** `SearchMask.vue` (v-model `{q,city,tag,dateFrom,dateTo,isOnline}`, emits `update:modelValue`+`search`),
`EventList.vue` (props `events,loading,total`), `useEventSearch()`. Agent-1 baut, Agent-2 importiert (nicht neu bauen).

## Entscheidungen

- **Eine geteilte SearchMask** statt zweimal bauen (Lars bestätigt via Frage). Tasks „Suchmaske Index" + „Suchmaske logged-in" = dieselbe Komponente, zweimal eingebunden.
- **3-Wege-Split** entlang Eigentums-Grenzen minimiert Datei-Kollisionen: Backend-Domain (Agent-3) / geteilte Such-Komponenten+Index (Agent-1) / Dashboard (Agent-2).
- **DEV_BYPASS_AUTH** in `frontend/src/router.js` = dev-only, NICHT nach master committen (würde Auth-Gate global aushebeln).

## BLOCKER — tmux-Dispatch braucht larskohlmorgen-Relaunch

Worker-tmux-Sessions laufen auf **larskohlmorgen-Socket (UID 501)**; Master-Session ist **agentuser (503)** → `/tmp/tmux-501/` ist Permission denied. Inbox-Dateien konnte agentuser schreiben (group=staff, setgid), aber `send-keys` nicht abfeuern.

**Nächster Schritt:** Lars startet Master-Session als larskohlmorgen neu, dann diese 3 Befehle abfeuern (Session-Namen aus `ps` verifiziert):

```
tmux send-keys -t claude-zdi-2026-hackathon-agent-1 'Lies _scrape/inbox/task-index-searchmask.md und arbeite den Auftrag auf Branch agent/agent-1 ab. Fuehre dein Journal via rolling-journal-append.' Enter
tmux send-keys -t claude-2026-hackathon-agent-2 'Lies _scrape/inbox/task-dashboard-loggedin.md und arbeite den Auftrag auf Branch agent/agent-2 ab. Fuehre dein Journal via rolling-journal-append.' Enter
tmux send-keys -t claude-2026-hackathon-agent-3 'Lies _scrape/inbox/task-scraper-events-api.md und arbeite den Auftrag auf Branch agent/agent-3 ab. Fuehre dein Journal via rolling-journal-append.' Enter
```

## Dev-Env (läuft im Hintergrund)
- Backend: `backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000` (SQLite via `backend/.env` → `DATABASE_URL=sqlite:///./eventradar.db`)
- Frontend: `npm run dev -- --host 0.0.0.0` in `frontend/` → :5173
- Echter Google-Login weiterhin offen (OAuth-Platzhalter); Postgres/PostGIS braucht Docker (aus).
