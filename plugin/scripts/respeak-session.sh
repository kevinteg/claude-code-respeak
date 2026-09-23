#!/bin/bash
# The command behind /respeak:off and /respeak:on: write, replace, or remove
# this session's override marker (scripts/respeak-override.sh explains how
# the hooks read it).
#
#   respeak-session.sh off          every respeak hook stays quiet this session
#   respeak-session.sh off gate     only the style gate stays quiet
#   respeak-session.sh on           remove the marker; config decides again
#   respeak-session.sh on gate      run the gate this session even where
#                                   gate.enabled is false (a trial)
#   respeak-session.sh status       show the marker and any env override
#
# The session id comes from CLAUDE_CODE_SESSION_ID, which Claude Code exports to
# the Bash tool. Exit 0 on success, 2 on usage error or no session id.
# bash 3.2 compatible.
set -u
script_dir="$(cd "$(dirname "$0")" && pwd)"
. "$script_dir/respeak-override.sh"

verb="${1:-status}"; what="${2:-all}"
sid="${CLAUDE_CODE_SESSION_ID:-}"
case "$sid" in ""|*[!A-Za-z0-9_-]*) sid="" ;; esac

case "$verb" in
  off|on|status) ;;
  *) echo "usage: respeak-session.sh off [gate] | on [gate] | status" >&2; exit 2 ;;
esac
case "$what" in all|gate) ;; *) echo "respeak: the only scope is 'gate' (or none, meaning every hook)" >&2; exit 2 ;; esac

dir="$(respeak_session_dir)"
if [ "$verb" = status ]; then
  word=""; [ -n "$sid" ] && [ -f "$dir/$sid" ] && word="$(head -c 16 "$dir/$sid" 2>/dev/null | tr -d '[:space:]')"
  echo "session: ${sid:-unknown (CLAUDE_CODE_SESSION_ID unset)}"
  echo "marker: ${word:-none}"
  echo "env: RESPEAK_HOOKS=${RESPEAK_HOOKS:-unset} RESPEAK_GATE=${RESPEAK_GATE:-unset}"
  echo "gate hook sees: $(respeak_override gate "$sid")"
  echo "stop hook sees: $(respeak_override stop "$sid")"
  exit 0
fi

if [ -z "$sid" ]; then
  echo "respeak: no session id (CLAUDE_CODE_SESSION_ID is unset), so a per-session marker cannot be written." >&2
  echo "respeak: for one launch use the environment instead: RESPEAK_HOOKS=off claude   or   RESPEAK_GATE=off|on claude" >&2
  exit 2
fi

mkdir -p "$dir" 2>/dev/null && chmod 700 "$(dirname "$dir")" "$dir" 2>/dev/null || {
  echo "respeak: cannot create $dir" >&2; exit 2; }

if [ "$verb" = off ]; then
  if [ "$what" = gate ]; then
    printf 'gate-off\n' > "$dir/$sid"
    echo "respeak: the style gate is off for this session (the SessionStart and Stop hooks still follow config). /respeak:on gate or /respeak:on restores it."
  else
    printf 'off\n' > "$dir/$sid"
    echo "respeak: every respeak hook (session start, stop, style gate) is off for this session. /respeak:on restores them."
  fi
else
  if [ "$what" = gate ]; then
    printf 'gate-on\n' > "$dir/$sid"
    echo "respeak: the style gate runs for this session even where gate.enabled is false. /respeak:on clears it."
  else
    rm -f "$dir/$sid"
    echo "respeak: no session override; the layered configuration decides again (respeak-config.sh explain shows it)."
  fi
fi
[ -n "${RESPEAK_HOOKS:-}${RESPEAK_GATE:-}" ] && echo "respeak: note the environment also sets RESPEAK_HOOKS=${RESPEAK_HOOKS:-unset} RESPEAK_GATE=${RESPEAK_GATE:-unset}; a marker outranks it."
exit 0
