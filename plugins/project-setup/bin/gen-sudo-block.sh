#!/usr/bin/env bash
# gen-sudo-block.sh — Write sudo setup script to /tmp/ and print run instruction.
# Based on agent-fs-permissions policy (Variante A).
# Run from inside the target project/worktree.
set -euo pipefail

# WORKFLOW_INVOCATION_DIR wird von workflow-run gesetzt und zeigt auf den Ziel-Projektordner.
PROJECT_ROOT="${WORKFLOW_INVOCATION_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
AGENTUSER="${AGENTUSER:-agentuser}"
# Eindeutiger /tmp-Name pro Projekt-PFAD, nicht nur pro Worktree-Blattname.
# basename allein ("agent-1") kollidiert über Projektgrenzen: zwei Projekte mit je
# einem 'agent-1'-Worktree schrieben beide /tmp/agent-setup-agent-1.sh — der letzte
# parallele agent-add-Lauf gewann (Vorfall 2026-06-21: mail-ops vs agent-core).
# Lesbarer Slug (Container-Projekt + Worktree) + CRC des Absolutpfads als Garantie.
PROJECT_SLUG="$(basename "$(dirname "$PROJECT_ROOT")")-$(basename "$PROJECT_ROOT")"
PROJECT_SLUG="$(printf '%s' "$PROJECT_SLUG" | tr -c 'A-Za-z0-9._-' '-')"
PROJECT_HASH="$(printf '%s' "$PROJECT_ROOT" | cksum | cut -d' ' -f1)"
SCRIPT_PATH="/tmp/agent-setup-${PROJECT_SLUG}-${PROJECT_HASH}.sh"

# Detect worktree vs master checkout (nur für Git-Repos)
GIT_DIR_FILE="$PROJECT_ROOT/.git"
HAS_GIT=false
IS_WORKTREE=false
MAIN_GIT_DIR="$PROJECT_ROOT/.git"
WORKTREE_NAME=""

if [ -d "$GIT_DIR_FILE" ] || [ -f "$GIT_DIR_FILE" ]; then
    HAS_GIT=true
    if [ -f "$GIT_DIR_FILE" ]; then
        IS_WORKTREE=true
        WORKTREES_PATH="$(grep "^gitdir:" "$GIT_DIR_FILE" | sed 's/gitdir: //')"
        MAIN_GIT_DIR="$(echo "$WORKTREES_PATH" | sed 's|/worktrees/.*||')"
        WORKTREE_NAME="$(basename "$WORKTREES_PATH")"
    fi
fi

# Write setup script to /tmp/
cat > "$SCRIPT_PATH" << SETUP_SCRIPT
#!/usr/bin/env bash
set -euo pipefail
PROJECT="$PROJECT_ROOT"
AGENTUSER="$AGENTUSER"

echo "Block A: \$AGENTUSER-Schreibzugriff (ACL + .git-Innereien)..."
sudo chmod -R +a "\$AGENTUSER allow read,write,delete,add_file,add_subdirectory,file_inherit,directory_inherit" "\$PROJECT/"
sudo find "\$PROJECT" -type d -exec chmod +a "\$AGENTUSER allow delete_child" {} +
SETUP_SCRIPT

if [ "$IS_WORKTREE" = "true" ]; then
    cat >> "$SCRIPT_PATH" << SETUP_SCRIPT
sudo chown -R $AGENTUSER:staff $MAIN_GIT_DIR/worktrees/$WORKTREE_NAME/
sudo chmod g+w $MAIN_GIT_DIR/worktrees/$WORKTREE_NAME/
SETUP_SCRIPT
fi

if [ "$HAS_GIT" = "true" ]; then
cat >> "$SCRIPT_PATH" << SETUP_SCRIPT
sudo chmod -R g+w "$MAIN_GIT_DIR/"
sudo find "$MAIN_GIT_DIR" -type d -exec chmod g+s {} +
SETUP_SCRIPT
fi

cat >> "$SCRIPT_PATH" << SETUP_SCRIPT
sudo grep -q '^umask 002' /Users/$AGENTUSER/.zshenv 2>/dev/null || echo 'umask 002' | sudo tee -a /Users/$AGENTUSER/.zshenv > /dev/null

echo "Block B: Hauptuser-Lesezugriff auf agent-erzeugte Files..."
sudo chgrp -R staff "$PROJECT_ROOT/"
sudo find "$PROJECT_ROOT" -type d -exec chmod g+s {} +
sudo chmod -R g+rw "$PROJECT_ROOT/"
sudo xattr -cr "$PROJECT_ROOT/" 2>/dev/null || true
SETUP_SCRIPT

if [ "$HAS_GIT" = "true" ]; then
cat >> "$SCRIPT_PATH" << SETUP_SCRIPT

echo "Block C: safe.directory fuer $AGENTUSER..."
sudo -u $AGENTUSER HOME=/Users/$AGENTUSER git config --global --add safe.directory "$PROJECT_ROOT"
SETUP_SCRIPT
fi

cat >> "$SCRIPT_PATH" << SETUP_SCRIPT

echo "Done."
touch "$PROJECT_ROOT/.claude/sudo-done"
SETUP_SCRIPT

chmod +x "$SCRIPT_PATH"

echo "→ Setup-Script geschrieben: $SCRIPT_PATH"
echo "  Projekt: $PROJECT_ROOT"
if [ "$IS_WORKTREE" = "true" ]; then
    echo "  Worktree: $WORKTREE_NAME"
fi
echo ""
echo "Einmalig als larskohlmorgen im eigenen Terminal ausführen"
echo "(nicht mit ! — sudo braucht interaktive Passworteingabe):"
echo ""
echo '```bash'
echo "sudo sh $SCRIPT_PATH"
echo '```'
