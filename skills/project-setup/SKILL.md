---
name: project-setup
description: AI-Tool-Symlinks in einem Projekt einrichten. Triggert bei "project setup", "setup ai tools", "ai symlinks einrichten" oder nach einem frischen git clone.
---

# Project Setup

Richtet die AI-Tool-Integration für dieses Projekt ein. Legt Symlinks in den tool-spezifischen Ordnern an, die auf den gemeinsamen `skills/`-Ordner des Projekts zeigen.

## Zweck

In diesem Projekt liegen Projekt-Skills unter `<git-root>/skills/`. AI-Tools wie Claude Code und Antigravity erwarten Skills aber an tool-spezifischen Pfaden (`.claude/skills/`, `.agents/skills/` etc.). Dieser Skill legt die dafür nötigen Symlinks an — einmalig pro Rechner pro Worktree, idempotent bei wiederholtem Aufruf.

## Hinweis zu Worktrees

Dieser Skill funktioniert **sowohl im Master-Checkout als auch in Git-Worktrees**. Jeder Worktree braucht seine eigenen Tool-Symlinks, weil diese lokal pro Checkout angelegt werden (und nicht ins Git committed werden).

Typische Projekt-Struktur:

```
<projekt-container>/
├── master/              ← Master-Checkout (Git-Root)
│   ├── skills/          ← echte Skill-Dateien, im Git
│   ├── .claude/skills   ← Symlink, lokal pro Worktree
│   └── .agents/skills   ← Symlink, lokal pro Worktree
├── agent-lars/          ← Worktree
│   ├── skills/          ← identisch via Git
│   ├── .claude/skills   ← eigener Symlink
│   └── .agents/skills   ← eigener Symlink
└── agent-anna/
    └── ...
```

Führe diesen Skill in **jedem** Worktree einzeln aus, in dem du arbeitest.

## Vorgehen

### 1. Projekt-Root bestimmen

Suche vom aktuellen Verzeichnis aufwärts den nächsten Ordner, der **beides** erfüllt:
- Enthält einen Unterordner `skills/`
- Enthält einen `.git`-Eintrag (Ordner *oder* File — bei Worktrees ist `.git` eine Datei, die auf den Shared-Git-Storage zeigt)

Falls nichts gefunden wird, melde klar:
> "Kein Projekt-Root gefunden. Dieser Skill muss innerhalb eines Git-Projekts (oder Git-Worktrees) aufgerufen werden, das einen skills/-Ordner enthält."

### 2. Tool-Erkennung

Erkenne, welche AI-Tools auf dem System installiert sind. Prüfe die Existenz folgender Verzeichnisse:

| Tool | Konfig-Verzeichnis (User) | Projekt-Symlink-Ziel |
|---|---|---|
| Claude Code | `~/.claude/` | `<projekt>/.claude/skills` |
| Antigravity | `~/.gemini/antigravity/` | `<projekt>/.agents/skills` |
| Gemini CLI | `~/.gemini/` (ohne antigravity) | `<projekt>/.gemini/skills` |
| Cursor | `~/.cursor/` | `<projekt>/.cursor/skills` |
| Cline | `~/.cline/` oder VS Code Extension-Pfad | (keine Standard-Konvention, überspringen) |

Nur Tools berücksichtigen, deren User-Konfig-Verzeichnis existiert. Tools ohne standardisiertes Skill-Verzeichnis werden übersprungen.

### 3. Plattform-Erkennung

Erkenne das Betriebssystem:
- **macOS oder Linux:** Symlinks funktionieren nativ, fortfahren
- **Windows (nativ, nicht WSL):** Warnung ausgeben, Symlinks trotzdem versuchen
- **WSL:** Verhält sich wie Linux

Bei Windows-nativ folgende Warnung vorab ausgeben:

> ⚠️  Windows erkannt. Symlinks erfordern entweder Entwicklermodus (Windows 10+) oder administrative Rechte. Falls das Anlegen fehlschlägt, aktiviere den Entwicklermodus in den Windows-Einstellungen oder starte das Terminal als Administrator.

### 4. Symlinks anlegen

Plugin-Root bestimmen:
```bash
git rev-parse --show-toplevel
```
→ `<git-root>/plugins/project-setup/bin/` ist der Script-Pfad.

```bash
<git-root>/plugins/project-setup/bin/setup-symlinks.sh
```

Erkennt installierte Tools, legt relative Symlinks idempotent an. Gibt pro Tool eine Statuszeile aus (`✓ / ↻ / ⊘ / ⚠️`). Bei echtem Ordner statt Symlink: Warnung, kein Überschreiben.

### 4b. Workspace-Buckets anlegen

```bash
<git-root>/plugins/project-setup/bin/setup-scrape-buckets.sh
```

Legt `_scrape/{inbox,captured,processed,work,out,promote}/` mit `.gitkeep` und `_media/`-Subfolder an (Lifecycle-Schema v2). Idempotent.

Status in der Abschluss-Zusammenfassung als `✓ _scrape/-Buckets` anzeigen.

### 5. Verifikation

Nach dem Anlegen jedes Symlinks prüfen:
- Zeigt der Symlink tatsächlich auf den `skills/`-Ordner im Projekt?
- Ist der `skills/`-Ordner über den Symlink lesbar?

Gib pro Tool eine Statuszeile aus:
```
✓ Claude Code     .claude/skills → ../skills
✓ Antigravity     .agents/skills → ../skills
⊘ Gemini CLI      nicht installiert (übersprungen)
```

### 6. Worktree-Kontext anzeigen

Erkenne, ob der aktuelle Arbeitsort ein Worktree oder der Master-Checkout ist:

- Wenn `.git` eine Datei ist (statt Ordner) → Worktree
- Wenn `.git` ein Ordner ist → Master-Checkout

Gib den Kontext in der Abschluss-Zusammenfassung aus, damit klar ist, wo die Symlinks angelegt wurden.

### 7. Abschluss-Zusammenfassung

Strukturierte Übersicht:

```
Project Setup abgeschlossen.

Projekt-Root: /Users/lars/Projekte/webzite-de/webshop/master
Kontext:      Master-Checkout (oder: Worktree 'agent-lars')
Skills-Quelle: skills/ (N Skills gefunden)

Tool-Integrationen:
  ✓ Claude Code
  ✓ Antigravity
  ⊘ Cursor (nicht installiert)

✓ _scrape/-Buckets angelegt

Hinweis: Bei mehreren Worktrees muss dieser Skill in jedem
einzeln ausgeführt werden (Symlinks sind pro Checkout lokal).
```

### 8. Remote Git-Konfiguration (opt-in)

Remote-URL, SSH-Key-Auswahl und `git config user.*` gehören nicht zum Basis-Setup.
Bei Bedarf explizit ansprechen — der `git-workflow`-Skill übernimmt diese Schritte.

## Idempotenz

Der Skill kann jederzeit neu ausgeführt werden, ohne Schaden anzurichten:
- Bestehende korrekte Symlinks werden nicht verändert
- Fehlende Symlinks werden ergänzt
- Falsch zeigende Symlinks werden korrigiert
- Echte Ordner werden **nie** überschrieben (immer Warnung statt Aktion)

## Fehlerbehandlung

### Kein `skills/`-Ordner im Projekt

Wenn der Projekt-Root gefunden ist, aber keinen `skills/`-Ordner hat:

> "Dieses Projekt hat keinen skills/-Ordner. Möchtest du einen leeren anlegen? (Ein leerer skills/-Ordner signalisiert, dass noch keine Projekt-Skills vorhanden sind, aber die Infrastruktur bereit ist.)"

Bei Zustimmung: `mkdir skills && touch skills/.gitkeep`.

### Symlink-Anlage schlägt fehl (Windows ohne Rechte)

Klare Meldung mit Handlungsanweisung:

> "Symlink-Anlage fehlgeschlagen. Auf Windows benötigt dies entweder:
> 1. Aktivierung des Entwicklermodus (Einstellungen → Update und Sicherheit → Für Entwickler)
> 2. Oder Ausführung des Terminals als Administrator
>
> Nach Aktivierung diesen Skill erneut ausführen."

### Skill in falschem Kontext aufgerufen

Wenn der Skill außerhalb eines Git-Projekts oder in einem Projekt ohne `skills/`-Ordner läuft (und kein leerer angelegt werden soll):

> "Dieser Skill ist für Projekt-Setups gedacht. Für globale Skill-Einrichtung siehe README in deinem Vault."

### Skill im äußeren Projekt-Container aufgerufen

Wenn das aktuelle Verzeichnis Unterordner wie `master/`, `agent-*/` etc. enthält, aber selbst kein Git-Repo ist, deutet das auf den äußeren Projekt-Container hin. Meldung:

> "Du scheinst im äußeren Projekt-Container zu sein (enthält master/ und/oder agent-*/). Wechsle in einen der Code-Ordner (z.B. `cd master/`) und rufe project-setup dort erneut auf."

## Wichtig für Team-Mitglieder

Dieser Skill **lebt im Projekt-Git** und ist committed. Das bedeutet:

- Jedes Team-Mitglied hat ihn nach `git clone` automatisch verfügbar
- Kein persönlicher Vault nötig
- Einfach in Claude Code oder Antigravity aufrufen: "project setup"

Die durch den Skill angelegten Symlinks werden **nicht committed** — sie sind pro Rechner pro Worktree individuell.

## Verwandte Skills

- `project-init` (global im Vault): Initialisiert ein neues Projekt komplett, inklusive Kopieren dieses `project-setup`-Skills aus dem Vault. Nur für den Projekt-Starter relevant.
- `project-link` (global im Vault, persönlich): Verknüpft das Projekt mit dem persönlichen Knowledge-Vault. Nur für Vault-Besitzer relevant.
- `project-knowledge-audit` (global im Vault): Audit existierender Projekte zur Wissens-Konsolidierung.
