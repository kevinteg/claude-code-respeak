#!/bin/bash
# CLI entry point for the layered-config resolver: picks a python3 that has
# PyYAML (scripts/respeak-python.sh) and runs scripts/respeak-config.py.
#
#   bash "${CLAUDE_PLUGIN_ROOT}/scripts/respeak-config.sh" explain [--for PATH]
#   bash "${CLAUDE_PLUGIN_ROOT}/scripts/respeak-config.sh" resolve --for docs/x.md --format yaml
#   bash "${CLAUDE_PLUGIN_ROOT}/scripts/respeak-config.sh" validate docs/.respeak.yaml
#
# `explain` ends with one extra line naming any session override in force
# (scripts/respeak-override.sh), so what it shows is what the hooks saw.
set -u
script_dir="$(cd "$(dirname "$0")" && pwd)"
. "$script_dir/respeak-python.sh"
if [ -z "$RESPEAK_PY" ]; then
  echo "respeak-config: no python3 with PyYAML found (tried python3, /usr/bin/python3, brew pythons); set RESPEAK_PYTHON=/path/to/python3 or install PyYAML" >&2
  exit 2
fi
if [ "${1:-}" != "explain" ]; then
  exec "$RESPEAK_PY" "$script_dir/respeak-config.py" "$@"
fi
"$RESPEAK_PY" "$script_dir/respeak-config.py" "$@"; rc=$?
if [ -f "$script_dir/respeak-override.sh" ]; then
  . "$script_dir/respeak-override.sh"
  sid="${CLAUDE_SESSION_ID:-}"
  g="$(respeak_override gate "$sid")"; h="$(respeak_override stop "$sid")"
  if [ -z "$g$h" ]; then
    if [ -n "$sid" ]; then echo "session overrides: none"; else echo "session overrides: none (no CLAUDE_SESSION_ID, so markers were not consulted)"; fi
  else
    hooks_state="config"; [ "${h%% *}" = off ] && hooks_state="off (${h#* })"
    gate_state="config"
    case "${g%% *}" in off) gate_state="off (${g#* })" ;; gate-on) gate_state="forced on (${g#* })" ;; esac
    echo "session overrides: hooks=$hooks_state gate=$gate_state"
  fi
fi
exit $rc
