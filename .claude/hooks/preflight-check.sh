#!/bin/bash
# PreToolUse hook: run release_preflight.py before git commit.
# Blocks the commit (exit 2) if preflight fails.

set -uo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=/dev/null
source "$SCRIPT_DIR/common.sh"

INPUT=$(cat)
REPO_ROOT=$(resolve_repo_root)
HOOK_PYTHON=$(resolve_hook_python "$REPO_ROOT" || true)
COMMAND=$(json_tool_input_value "$HOOK_PYTHON" "$INPUT" command || true)

# Only trigger on git commit commands
[[ "$COMMAND" =~ (^|[[:space:]])git[[:space:]]+commit($|[[:space:]]) ]] || exit 0

# Locate Python from canonical external local state or fall back to python3/python
PYTHON="$HOOK_PYTHON"
[[ -n "$PYTHON" ]] || exit 0

# Run preflight
OUTPUT=$("$PYTHON" "$REPO_ROOT/tools/release_preflight.py" --strict 2>&1) || {
  echo "Release preflight FAILED - commit blocked:" >&2
  echo "$OUTPUT" >&2
  exit 2
}

# Hint about potential documentation drift (informational only)
if [[ -f "$REPO_ROOT/tools/context_drift.py" ]]; then
    DRIFT=$("$PYTHON" "$REPO_ROOT/tools/context_drift.py" --brief 2>/dev/null || true)
    if [[ -n "$DRIFT" ]]; then
        echo "hint: $DRIFT" >&2
        echo "hint: Run /sync-context to review." >&2
    fi
fi

exit 0
