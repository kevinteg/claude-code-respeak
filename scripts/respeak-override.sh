#!/bin/bash
# Session-scoped overrides for the respeak hooks. Source this, then call
#
#   respeak_override <hook> <session_id>      # hook: gate | stop | session-start
#
# It prints one line, "<word> <reason>", or nothing when no override applies:
#   off       this hook must do nothing for this session
#   gate-on   (gate only) run the gate as if gate.enabled were true
#
# Precedence, highest first:
#   1. a session marker written by /respeak:off or /respeak:on
#      (${RESPEAK_CACHE_DIR:-${XDG_CACHE_HOME:-$HOME/.cache}/respeak}/session/<session_id>)
#      holding exactly one word: off | gate-off | gate-on
#   2. environment: RESPEAK_HOOKS=off (every hook), RESPEAK_GATE=off|on (gate only)
#   3. nothing: the layered configuration decides (docs/config-layers.md)
#
# The manifest declares what the plugin CAN do; config and these overrides
# declare what it SHOULD do here and now. Markers older than 24 hours are
# removed on every call, so a crashed session never leaves a silent hook
# behind; a marker with unknown content is ignored; a session id is one path
# segment of [A-Za-z0-9_-]. bash 3.2 compatible.

respeak_session_dir() {
  printf '%s/session' "${RESPEAK_CACHE_DIR:-${XDG_CACHE_HOME:-$HOME/.cache}/respeak}"
}

respeak_sweep_markers() {
  [ -d "$1" ] || return 0
  find "$1" -type f -mmin +1440 -delete 2>/dev/null
  return 0
}

respeak_override() {
  local hook="$1" sid="${2:-}" dir word=""
  dir="$(respeak_session_dir)"
  respeak_sweep_markers "$dir"
  case "$sid" in ""|*[!A-Za-z0-9_-]*) sid="" ;; esac
  if [ -n "$sid" ] && [ -f "$dir/$sid" ]; then
    word="$(head -c 16 "$dir/$sid" 2>/dev/null | tr -d '[:space:]')"
    case "$word" in
      off)      echo "off session-marker"; return 0 ;;
      gate-off) [ "$hook" = gate ] && { echo "off session-marker"; return 0; } ;;
      gate-on)  [ "$hook" = gate ] && { echo "gate-on session-marker"; return 0; } ;;
    esac
  fi
  case "$(printf '%s' "${RESPEAK_HOOKS:-}" | tr '[:upper:]' '[:lower:]')" in
    off|0|false|no) echo "off RESPEAK_HOOKS=off"; return 0 ;;
  esac
  if [ "$hook" = gate ]; then
    case "$(printf '%s' "${RESPEAK_GATE:-}" | tr '[:upper:]' '[:lower:]')" in
      off|0|false|no) echo "off RESPEAK_GATE=off"; return 0 ;;
      on|1|true|yes)  echo "gate-on RESPEAK_GATE=on"; return 0 ;;
    esac
  fi
  return 0
}
