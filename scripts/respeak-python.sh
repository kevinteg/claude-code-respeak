#!/bin/bash
# Source this to set RESPEAK_PY: the first python3 on this machine that can
# import PyYAML, which the config resolver and the measure/verify scripts
# need. A pyenv shim or a brew python often lacks it while /usr/bin/python3
# has it (or the reverse); a hard-coded `python3` then makes every hook a
# silent no-op. Override with RESPEAK_PYTHON=/path/to/python3.
#
#   . "$(dirname "$0")/respeak-python.sh"
#   [ -n "$RESPEAK_PY" ] || exit 0          # hooks fail open
#
# bash 3.2 compatible (macOS default).
respeak_find_python() {
  local cand
  for cand in "${RESPEAK_PYTHON:-}" python3 /usr/bin/python3 \
              /opt/homebrew/bin/python3 /usr/local/bin/python3 \
              python3.13 python3.12; do
    [ -n "$cand" ] || continue
    command -v "$cand" >/dev/null 2>&1 || continue
    "$cand" -c 'import yaml' >/dev/null 2>&1 || continue
    printf '%s\n' "$cand"
    return 0
  done
  return 1
}
RESPEAK_PY="$(respeak_find_python)" || RESPEAK_PY=""
