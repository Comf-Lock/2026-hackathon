#!/usr/bin/env bash
# set-bypass-settings.sh — Write the canonical bypassPermissions settings.local.json.
#
# Single source of truth for the bypass block. Used as the early bypass step in
# both project-onboarding (Step 0) and project-agent-add, and re-used by
# run-agent-setup.sh and teardown-onboarding.sh — so the JSON lives in exactly
# one place. Persistent (NOT removed by teardown): project-agent-add needs it
# after onboarding too.
#
# Permission settings hot-reload mid-session in Claude Code, so writing this
# early makes the rest of the workflow run without permission prompts.
#
# Target: $1 (if given) else WORKFLOW_INVOCATION_DIR else git-root else CWD.
# Idempotent (overwrites).
set -euo pipefail

TARGET="${1:-${WORKFLOW_INVOCATION_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}}"
SETTINGS_DIR="$TARGET/.claude"
SETTINGS_FILE="$SETTINGS_DIR/settings.local.json"

mkdir -p "$SETTINGS_DIR"
[ -f "$SETTINGS_FILE" ] && grep -q '"bypassPermissions"' "$SETTINGS_FILE" 2>/dev/null \
    && { echo "ℹ️  settings.local.json hat bereits bypassPermissions ($SETTINGS_DIR)"; exit 0; }

cat > "$SETTINGS_FILE" << 'ENDJSON'
{
  "skipDangerousModePermissionPrompt": true,
  "permissions": {
    "defaultMode": "bypassPermissions",
    "allow": [
      "Bash(git *)",
      "Bash(git push *)",
      "Bash(npm run *)",
      "Bash(curl *)",
      "Bash(sudo *)",
      "Bash(gh pr *)",
      "Bash(gh api *)",
      "Bash(./.agent/scripts/git-push-and-pr.sh *)",
      "Bash(export PATH=\"/opt/homebrew/bin:/opt/homebrew/opt/node@20/bin:$PATH\")"
    ]
  }
}
ENDJSON
echo "✅ settings.local.json → bypassPermissions ($SETTINGS_DIR)"
