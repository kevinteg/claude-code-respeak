#!/bin/bash
# CLI entry point for the layered-config resolver: picks a python3 that has
# PyYAML (scripts/respeak-python.sh) and execs scripts/respeak-config.py.
#
#   bash "${CLAUDE_PLUGIN_ROOT}/scripts/respeak-config.sh" explain [--for PATH]
#   bash "${CLAUDE_PLUGIN_ROOT}/scripts/respeak-config.sh" resolve --for docs/x.md --format yaml
#   bash "${CLAUDE_PLUGIN_ROOT}/scripts/respeak-config.sh" validate docs/.respeak.yaml
set -u
script_dir="$(cd "$(dirname "$0")" && pwd)"
. "$script_dir/respeak-python.sh"
if [ -z "$RESPEAK_PY" ]; then
  echo "respeak-config: no python3 with PyYAML found (tried python3, /usr/bin/python3, brew pythons); set RESPEAK_PYTHON=/path/to/python3 or install PyYAML" >&2
  exit 2
fi
exec "$RESPEAK_PY" "$script_dir/respeak-config.py" "$@"
