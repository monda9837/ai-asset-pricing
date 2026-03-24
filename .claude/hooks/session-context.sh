#!/bin/bash
# SessionStart hook: inject recent activity and drift warnings.
# stdout → injected into Claude's context.

set -uo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=/dev/null
source "$SCRIPT_DIR/common.sh"

# SessionStart stdin has {session_id, source, model} — NOT tool_input.
# We don't need to parse it for this hook.
cat > /dev/null

REPO_ROOT=$(resolve_repo_root)
HOOK_PYTHON=$(resolve_hook_python "$REPO_ROOT" || true)

# Skip gracefully if Python unavailable
[[ -n "$HOOK_PYTHON" ]] || exit 0

# --- Recent commits (last 48h) ---
RECENT=$(git -C "$REPO_ROOT" log --since="48 hours" --oneline --no-merges 2>/dev/null | head -10)
if [[ -n "$RECENT" ]]; then
    echo "## Recent Activity (last 48h)"
    echo '```'
    echo "$RECENT"
    echo '```'
    echo ""
fi

# --- Drift warnings ---
if [[ -f "$REPO_ROOT/tools/context_drift.py" ]]; then
    DRIFT=$("$HOOK_PYTHON" "$REPO_ROOT/tools/context_drift.py" --brief 2>/dev/null || true)
    if [[ -n "$DRIFT" ]]; then
        echo "## Context Drift"
        echo "$DRIFT"
        echo ""
        echo "_Run \`/sync-context\` to review and update stale documentation._"
        echo ""
    fi
fi

exit 0
