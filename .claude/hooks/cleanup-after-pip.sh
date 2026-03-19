#!/bin/bash
# PostToolUse hook: clean Python build artifacts after pip install.
# Removes __pycache__, *.pyc, *.egg-info from the repo tree.

set -uo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=/dev/null
source "$SCRIPT_DIR/common.sh"

INPUT=$(cat)
REPO_ROOT=$(resolve_repo_root)
HOOK_PYTHON=$(resolve_hook_python "$REPO_ROOT" || true)
COMMAND=$(json_tool_input_value "$HOOK_PYTHON" "$INPUT" command || true)

# Trigger on pip install or uv pip install commands
[[ "$COMMAND" =~ (^|[[:space:]])(pip|uv[[:space:]]+pip)[[:space:]]+install($|[[:space:]]) ]] || exit 0

find "$REPO_ROOT" -type d -name '__pycache__' -not -path '*/.git/*' -exec rm -rf {} + 2>/dev/null || true
find "$REPO_ROOT" -type d -name '*.egg-info' -not -path '*/.git/*' -exec rm -rf {} + 2>/dev/null || true
find "$REPO_ROOT" -name '*.pyc' -not -path '*/.git/*' -delete 2>/dev/null || true

exit 0
