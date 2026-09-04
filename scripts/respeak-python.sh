#!/bin/bash
# Source this to set two interpreter variables:
#   RESPEAK_PY      the first python3 that can import PyYAML — needed by the
#                   config resolver and the measure/verify scripts
#   RESPEAK_PY_STD  the first python3 that runs at all (stdlib only) — enough
#                   to parse a hook's JSON payload
# A pyenv shim with no version selected exits 127 and a brew python often
# lacks PyYAML, so a hard-coded `python3` made every hook a silent no-op.
# Override the first with RESPEAK_PYTHON=/path/to/python3.
#
# Probing is the expensive part (a pyenv shim costs ~70 ms per launch), so
# the answer is cached per PATH in ${TMPDIR:-/tmp}/respeak-python.$UID and
# re-validated with one cheap launch on every use; a changed PATH or a
# candidate that stops working triggers a fresh search. RESPEAK_PYTHON
# bypasses the cache.
#
#   . "$(dirname "$0")/respeak-python.sh"
#   [ -n "$RESPEAK_PY" ] || exit 0          # hooks fail open
#
# bash 3.2 compatible (macOS default).
respeak_find_python() {
  # $1 = python snippet the candidate must run cleanly
  local cand
  for cand in python3 /usr/bin/python3 /opt/homebrew/bin/python3 /usr/local/bin/python3 \
              python3.13 python3.12; do
    command -v "$cand" >/dev/null 2>&1 || continue
    "$cand" -c "$1" >/dev/null 2>&1 || continue
    printf '%s\n' "$cand"
    return 0
  done
  return 1
}

RESPEAK_PY=""; RESPEAK_PY_STD=""
if [ -n "${RESPEAK_PYTHON:-}" ] && "$RESPEAK_PYTHON" -c 'import yaml' >/dev/null 2>&1; then
  RESPEAK_PY="$RESPEAK_PYTHON"
else
  _respeak_cache="${TMPDIR:-/tmp}/respeak-python.${UID:-$(id -u)}"
  if [ -r "$_respeak_cache" ]; then
    # line 1: the PATH the answer was found under; line 2: the interpreter
    _respeak_cached_path="$(sed -n '1p' "$_respeak_cache" 2>/dev/null)"
    _respeak_cached_py="$(sed -n '2p' "$_respeak_cache" 2>/dev/null)"
    if [ "$_respeak_cached_path" = "$PATH" ] && [ -n "$_respeak_cached_py" ] \
       && "$_respeak_cached_py" -c 'import yaml' >/dev/null 2>&1; then
      RESPEAK_PY="$_respeak_cached_py"
    fi
  fi
  if [ -z "$RESPEAK_PY" ]; then
    RESPEAK_PY="$(respeak_find_python 'import yaml')" || RESPEAK_PY=""
    if [ -n "$RESPEAK_PY" ]; then
      { printf '%s\n%s\n' "$PATH" "$RESPEAK_PY" > "$_respeak_cache.$$" && mv -f "$_respeak_cache.$$" "$_respeak_cache"; } 2>/dev/null
    fi
  fi
fi
# A PyYAML-capable python is stdlib-capable: no second search when we have one.
if [ -n "$RESPEAK_PY" ]; then
  RESPEAK_PY_STD="$RESPEAK_PY"
else
  RESPEAK_PY_STD="$(respeak_find_python 'import json')" || RESPEAK_PY_STD=""
fi
