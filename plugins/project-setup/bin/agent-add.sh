#!/usr/bin/env bash
# agent-add.sh — Add a parallel agent worktree to an already-onboarded project.
#
# Creates a sibling worktree of the master checkout on its own branch
# (agent/<name>), then runs the per-worktree setup pieces (tool symlinks,
# scrape buckets, settings.local.json with bypassPermissions, worktree-aware
# sudo-block) by reusing the existing onboarding scripts against the new
# worktree. Project-creation-once steps (project-init, agent-config-init,
# remote-setup, teardown) are intentionally NOT repeated.
#
# Run as agentuser (matching project-onboarding): agentuser already has write
# access to master/.git from the master onboarding, so `git worktree add` works.
# The only privileged step is the generated sudo-block, which is written to /tmp/
# and run by Lars in his terminal (relay pattern). Two modes:
#
#   Mode A — folder-derived (default, ergonomic):
#     Create an empty agent folder next to master/, cd into it, run with NO name.
#       mkdir ../agent1 && cd ../agent1
#       workflow run project-agent-add        # name = "agent1" (the folder)
#     The worktree is created in-place in the current folder.
#
#   Mode B — explicit name from a checkout (e.g. master/):
#       workflow run project-agent-add anna   # creates ../anna
#     Name via WORKFLOW_AGENT_NAME env (set by workflow-run) or $1.
#
# Idempotent: re-running re-applies the per-worktree setup and regenerates the
# sudo-block without recreating an existing worktree.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

slugify() { printf '%s' "$1" | sed -e 's#^agent/##' -e 's#^agent-##'; }

# --- 0/1. Determine mode, agent name, source root, target worktree --------
EXPLICIT_NAME="${WORKFLOW_AGENT_NAME:-${1:-}}"
CWD="$(pwd)"
CWD_GIT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"

if [ -n "$EXPLICIT_NAME" ]; then
    # Mode B — explicit name; must run from a checkout of the project.
    if [ -z "$CWD_GIT_ROOT" ]; then
        echo "❌ Mit explizitem Namen aus einem Git-Checkout aufrufen (z.B. master/)." >&2
        exit 1
    fi
    AGENT_NAME="$(slugify "$EXPLICIT_NAME")"
    SRC_ROOT="$CWD_GIT_ROOT"
    CONTAINER="$(dirname "$SRC_ROOT")"
    WORKTREE_PATH="$CONTAINER/$AGENT_NAME"
    MODE="explizit (Mode B)"
elif [ -z "$CWD_GIT_ROOT" ]; then
    # Mode A — current dir is not a repo: derive name from the folder name,
    # find the master sibling as git source, create the worktree in-place.
    AGENT_NAME="$(basename "$CWD")"
    CONTAINER="$(dirname "$CWD")"
    if [ -d "$CONTAINER/master/.git" ]; then
        SRC_ROOT="$CONTAINER/master"
    else
        echo "❌ Kein 'master/'-Checkout neben '$CWD' gefunden." >&2
        echo "   Modus A aus einem leeren Agent-Ordner direkt neben master/ aufrufen." >&2
        exit 1
    fi
    WORKTREE_PATH="$CWD"
    MODE="Ordnername (Mode A)"
else
    # In a checkout but no name → ambiguous (would try to re-add master itself).
    echo "❌ Kein Agent-Name angegeben und das aktuelle Verzeichnis ist bereits ein Git-Checkout." >&2
    echo "   Entweder: Name angeben      → workflow run project-agent-add <name>" >&2
    echo "   Oder:     aus leerem Ordner → mkdir ../<name> && cd ../<name> && workflow run project-agent-add" >&2
    exit 1
fi

# --- 1b. Validate name + precondition -------------------------------------
if ! printf '%s' "$AGENT_NAME" | grep -qE '^[a-z0-9][a-z0-9-]*$'; then
    echo "❌ Ungültiger Agent-Name '$AGENT_NAME' (erlaubt: Kleinbuchstaben, Ziffern, Bindestrich)." >&2
    echo "   Bei Modus A: den Ordner filesystem-freundlich benennen (z.B. 'agent1', 'agent-anna')." >&2
    exit 1
fi
if [ "$AGENT_NAME" = "master" ]; then
    echo "❌ 'master' ist der Haupt-Checkout, kein Agent-Worktree." >&2
    exit 1
fi
if [ ! -f "$SRC_ROOT/.agent/config.yaml" ]; then
    echo "❌ '$SRC_ROOT' ist nicht onboardet (.agent/config.yaml fehlt)." >&2
    echo "   Erst 'workflow run project-onboarding' im Master ausführen." >&2
    exit 1
fi

BRANCH="agent/$AGENT_NAME"
BASE_BRANCH="$(git -C "$SRC_ROOT" symbolic-ref --short HEAD 2>/dev/null || echo master)"

echo "=== Agent-Worktree anlegen ==="
echo "  Modus:        $MODE"
echo "  Agent:        $AGENT_NAME"
echo "  Worktree:     $WORKTREE_PATH"
echo "  Branch:       $BRANCH  (Basis: $BASE_BRANCH, Quelle: $SRC_ROOT)"
echo ""

# --- 2. Create worktree (idempotent) --------------------------------------
# git worktree add accepts a pre-existing EMPTY dir (Mode A), creates a new one
# (Mode B), and refuses a non-empty non-worktree dir on its own.
abs_target="$(cd "$WORKTREE_PATH" 2>/dev/null && pwd || echo "$WORKTREE_PATH")"
if git -C "$SRC_ROOT" worktree list --porcelain | grep -qxF "worktree $abs_target"; then
    echo "ℹ️  Worktree bereits registriert — überspringe 'git worktree add'."
elif git -C "$SRC_ROOT" show-ref --verify --quiet "refs/heads/$BRANCH"; then
    git -C "$SRC_ROOT" worktree add "$WORKTREE_PATH" "$BRANCH"
    echo "✅ Worktree angelegt auf bestehendem Branch $BRANCH."
else
    git -C "$SRC_ROOT" worktree add -b "$BRANCH" "$WORKTREE_PATH" "$BASE_BRANCH"
    echo "✅ Worktree + Branch $BRANCH angelegt (von $BASE_BRANCH)."
fi
echo ""

# --- 3. Per-worktree setup ------------------------------------------------
# Persistent helper scripts only (set-bypass-settings.sh, setup-symlinks.sh,
# setup-scrape-buckets.sh, gen-sudo-block.sh) — NOT run-agent-setup.sh, which the
# onboarding teardown removes. .gitignore is inherited from the committed branch,
# so no patching needed here. Sub-scripts derive their target from CWD.

# bypassPermissions zuerst: Settings hot-reloaden mitten in der Session, daher
# läuft der Rest des Workflows (z.B. Step 2 project-link) prompt-frei.
echo "=== settings.local.json (bypassPermissions) ==="
"$SCRIPT_DIR/set-bypass-settings.sh" "$WORKTREE_PATH"
echo ""

echo "=== Tool-Symlinks ==="
( cd "$WORKTREE_PATH" && "$SCRIPT_DIR/setup-symlinks.sh" )
echo ""

echo "=== Scrape-Buckets ==="
( cd "$WORKTREE_PATH" && "$SCRIPT_DIR/setup-scrape-buckets.sh" )
echo ""

echo "=== sudo-Block (worktree-aware) ==="
# WORKFLOW_INVOCATION_DIR unset → gen-sudo-block nimmt den git-root des Worktrees.
( cd "$WORKTREE_PATH" && env -u WORKFLOW_INVOCATION_DIR "$SCRIPT_DIR/gen-sudo-block.sh" )

echo ""
echo "=== Fertig (Skript-Phase) ==="
echo "  Worktree $WORKTREE_PATH ist eingerichtet."
echo "  Noch offen: das oben ausgegebene sudo-Setup-Script EINMAL als larskohlmorgen ausführen,"
echo "  damit agentuser Schreibzugriff auf die Worktree-Git-Innereien erhält."
