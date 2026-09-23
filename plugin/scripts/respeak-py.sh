#!/bin/bash
# Run one of this plugin's python scripts with a PyYAML-capable interpreter
# (scripts/respeak-python.sh picks it; RESPEAK_PYTHON overrides).
#
#   bash "${CLAUDE_PLUGIN_ROOT}/scripts/respeak-py.sh" respeak-measure.py doc.md --fail-on error
#   bash "${CLAUDE_PLUGIN_ROOT}/scripts/respeak-py.sh" respeak-verify-edit.py before.md after.md
set -u
script_dir="$(cd "$(dirname "$0")" && pwd)"
. "$script_dir/respeak-python.sh"
if [ -z "$RESPEAK_PY" ]; then
  echo "respeak-py: no python3 with PyYAML found; set RESPEAK_PYTHON=/path/to/python3 or install PyYAML" >&2
  exit 2
fi
[ $# -ge 1 ] || { echo "usage: respeak-py.sh <script.py> [args...]" >&2; exit 2; }
script="$1"; shift
case "$script" in
  /*) ;;
  *) script="$script_dir/$script" ;;
esac
[ -f "$script" ] || { echo "respeak-py: no such script: $script" >&2; exit 2; }
exec "$RESPEAK_PY" "$script" "$@"
