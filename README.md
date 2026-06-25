# 2026-hackathon

## AI Tool Setup

Nach dem Klonen einmalig im Chat aufrufen: `project setup`

Der `project-setup`-Skill (unter `skills/project-setup/`) legt lokal
die nötigen Tool-Symlinks an. Idempotent.

### Default-Branch

Dieses Projekt nutzt **`master`** als Default-Branch.

### Bei Git-Worktrees

Empfohlene Struktur:

    2026-hackathon/
    ├── master/                ← Master-Checkout
    └── agent-<n>/             ← Worktree pro Agent

Jeder Worktree braucht einen eigenen `project setup`-Aufruf.
