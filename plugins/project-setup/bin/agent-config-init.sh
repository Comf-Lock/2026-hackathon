#!/usr/bin/env bash
# Legt .agent/config.yaml (Template) und .agent/personas/ an.
# Stack-Identifier wird vom Developer beim ersten Aktivieren vervollständigt.

set -e

# WORKFLOW_INVOCATION_DIR wird von workflow-run gesetzt und zeigt auf den Ziel-Projektordner.
PROJECT_ROOT="${WORKFLOW_INVOCATION_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
CONFIG_FILE="$PROJECT_ROOT/.agent/config.yaml"
PERSONAS_DIR="$PROJECT_ROOT/.agent/personas"

# Kunde aus dem _clients/<kunde>/-Pfadsegment ableiten (analog project-init).
# Wird als client: in die config.yaml geschrieben → claude-agent-spawn liest es in
# die Heartbeat-/Hub-Metadata, damit jeder Agent plattformeinheitlich seinen Kunden zeigt.
CLIENT=""
case "$PROJECT_ROOT" in
    */_clients/*) CLIENT="${PROJECT_ROOT#*/_clients/}"; CLIENT="${CLIENT%%/*}" ;;
esac

mkdir -p "$PERSONAS_DIR"

if [ -f "$CONFIG_FILE" ]; then
    echo "→ .agent/config.yaml existiert bereits — übersprungen"
else
    {
        if [ -n "$CLIENT" ]; then
            printf '# client: customer this project belongs to — read by claude-agent-spawn into the\n'
            printf '# agent metadata (heartbeat + hub register), so every platform shows the same name.\n'
            printf 'client: %s\n\n' "$CLIENT"
        fi
        cat << 'EOF'
# .agent/config.yaml — Projekt-Konfiguration für Persona-System
#
# stack: Pflicht für Developer/QM-Personas mit Stack-Verfeinerung.
# Wird vom Developer beim ersten Aktivieren vervollständigt (Stack-Discovery-Flow).
#
# Naming-Konvention: <primary-framework>[-<secondary>][-<db-layer>]
# Referenz: ~/knowledge/shared/personas/stacks/README.md
#
# Beispiele:
#   stack: vue-alpine
#   stack: express-drizzle
#   stack: vue-alpine-express-drizzle
#   stack: nextjs-prisma
#
# Hybrid-Projekte (separates Frontend/Backend):
#   stacks:
#     frontend: vue-alpine
#     backend: express-drizzle

stack:  # SETZEN — Developer vervollständigt beim ersten Aktivieren

# plugins: Opt-in Plugin-Registry — Plugins aus agent-core/plugins/ die in diesem Projekt aktiv sind.
# Verfügbare Plugins: project-setup, wiki-engineer
# Beispiel: plugins: [project-setup]
plugins: []
EOF
    } > "$CONFIG_FILE"
    echo "→ .agent/config.yaml angelegt${CLIENT:+ (client=$CLIENT)} (Stack noch zu setzen — Developer aktivieren)"
fi

echo "→ .agent/personas/ bereit"
