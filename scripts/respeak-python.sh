#!/bin/bash
# Source this to set two interpreter variables:
#   RESPEAK_PY      the first python3 that can import PyYAML — needed by the
#                   config resolver and the measure/verify scripts
#   RESPEAK_PY_STD  the first python3 that runs at all (stdlib only) — enough
#                   to parse a hook's JSON payload
# A pyenv shim with no version selected exits 127 and a brew python often
# lacks PyYAML, so a hard-coded `python3` made every hook a silent no-op.
# Override the first with RESPEAK_PYTHON=/path/to/python3 (bypasses the cache).
#
# Probing is the expensive part (a pyenv shim costs ~70 ms per launch), so
# the answer is cached per PATH and re-validated with one launch on use.
# The cache is trust-bounded: it lives in a directory only this user can
# write (${RESPEAK_CACHE_DIR:-${XDG_CACHE_HOME:-$HOME/.cache}/respeak},
# created 0700 and required to be owned by the caller and not a symlink),
# the file must be a regular owner-owned file, and the cached name is
# honoured only if it is one of the fixed candidates below — so a tampered
# or pre-seeded file can at worst pick a different known interpreter, never
# run an arbitrary path. No usable cache directory means no cache.
#
#   . "$(dirname "$0")/respeak-python.sh"
#   [ -n "$RESPEAK_PY" ] || exit 0          # hooks fail open
#
# bash 3.2 compatible (macOS default).
RESPEAK_PY_CANDIDATES="python3 /usr/bin/python3 /opt/homebrew/bin/python3 /usr/local/bin/python3 python3.13 python3.12"

respeak_find_python() {
  # $1 = python snippet the candidate must run cleanly
  local cand
  for cand in $RESPEAK_PY_CANDIDATES; do
    command -v "$cand" >/dev/null 2>&1 || continue
    "$cand" -c "$1" >/dev/null 2>&1 || continue
    printf '%s\n' "$cand"
    return 0
  done
  return 1
}

respeak_is_candidate() {
  local cand
  for cand in $RESPEAK_PY_CANDIDATES; do
    [ "$1" = "$cand" ] && return 0
  done
  return 1
}

respeak_cache_dir() {
  # prints a usable cache directory, or nothing
  local d="${RESPEAK_CACHE_DIR:-}"
  if [ -z "$d" ]; then
    if [ -n "${XDG_CACHE_HOME:-}" ]; then d="$XDG_CACHE_HOME/respeak"
    elif [ -n "${HOME:-}" ]; then d="$HOME/.cache/respeak"
    else return 1; fi
  fi
  if [ ! -d "$d" ]; then
    (umask 077 && mkdir -p "$d") 2>/dev/null || return 1
  fi
  [ ! -L "$d" ] && [ -d "$d" ] && [ -O "$d" ] && [ -w "$d" ] || return 1
  printf '%s\n' "$d"
}

RESPEAK_PY=""; RESPEAK_PY_STD=""
if [ -n "${RESPEAK_PYTHON:-}" ] && "$RESPEAK_PYTHON" -c 'import yaml' >/dev/null 2>&1; then
  RESPEAK_PY="$RESPEAK_PYTHON"
else
  _respeak_dir="$(respeak_cache_dir)" || _respeak_dir=""
  _respeak_cache=""
  [ -n "$_respeak_dir" ] && _respeak_cache="$_respeak_dir/python"
  if [ -n "$_respeak_cache" ] && [ -f "$_respeak_cache" ] && [ ! -L "$_respeak_cache" ] && [ -O "$_respeak_cache" ]; then
    # line 1: the PATH the answer was found under; line 2: the candidate name
    _respeak_cached_path="$(sed -n '1p' "$_respeak_cache" 2>/dev/null)"
    _respeak_cached_py="$(sed -n '2p' "$_respeak_cache" 2>/dev/null)"
    if [ "$_respeak_cached_path" = "$PATH" ] && respeak_is_candidate "$_respeak_cached_py" \
       && "$_respeak_cached_py" -c 'import yaml' >/dev/null 2>&1; then
      RESPEAK_PY="$_respeak_cached_py"
    fi
  fi
  if [ -z "$RESPEAK_PY" ]; then
    RESPEAK_PY="$(respeak_find_python 'import yaml')" || RESPEAK_PY=""
    if [ -n "$RESPEAK_PY" ] && [ -n "$_respeak_cache" ]; then
      _respeak_tmp="$(mktemp "$_respeak_dir/python.XXXXXX" 2>/dev/null)" || _respeak_tmp=""
      if [ -n "$_respeak_tmp" ]; then
        { printf '%s\n%s\n' "$PATH" "$RESPEAK_PY" > "$_respeak_tmp" && mv -f "$_respeak_tmp" "$_respeak_cache"; } 2>/dev/null \
          || rm -f "$_respeak_tmp" 2>/dev/null
      fi
    fi
  fi
fi
# A PyYAML-capable python is stdlib-capable: no second search when we have one.
if [ -n "$RESPEAK_PY" ]; then
  RESPEAK_PY_STD="$RESPEAK_PY"
else
  RESPEAK_PY_STD="$(respeak_find_python 'import json')" || RESPEAK_PY_STD=""
fi
