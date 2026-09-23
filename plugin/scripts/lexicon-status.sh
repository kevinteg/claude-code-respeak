#!/bin/bash
# SessionStart hook: inject factual lexicon status as additionalContext.
# Speaks only in a project that uses respeak (it has a .claude/respeak/
# directory, which /respeak:init creates); every other session gets nothing,
# so the plugin costs a repo that never asked for it zero context.
# RESPEAK_HOOKS=off or a /respeak:off marker silences it too
# (scripts/respeak-override.sh). Never fails the session — any error exits 0
# with no output. bash 3.2 compatible.
set -u

HOOK_JSON="$(cat 2>/dev/null || true)"
script_dir="$(cd "$(dirname "$0")" && pwd)"
RESPEAK_PY=""; RESPEAK_PY_STD=""
[ -f "$script_dir/respeak-python.sh" ] && . "$script_dir/respeak-python.sh"
[ -f "$script_dir/respeak-override.sh" ] && . "$script_dir/respeak-override.sh"
pyj="${RESPEAK_PY:-$RESPEAK_PY_STD}"
[ -n "$pyj" ] || exit 0

session_id="$(printf '%s' "$HOOK_JSON" | "$pyj" -c '
import json, sys
try:
    print(str(json.load(sys.stdin).get("session_id") or ""))
except Exception:
    print("")
' 2>/dev/null)"
if command -v respeak_override >/dev/null 2>&1; then
  ov="$(respeak_override session-start "$session_id")"
  case "${ov%% *}" in off) exit 0 ;; esac
fi

[ -d ".claude/respeak" ] || exit 0

PROJECT_LEXICON=".claude/respeak/lexicon.yaml"
PLUGIN_LEXICON="${CLAUDE_PLUGIN_ROOT:-}/corpus/lexicon.yaml"
lexicon=""
if [ -f "$PROJECT_LEXICON" ]; then
  lexicon="$PROJECT_LEXICON"
elif [ -n "${CLAUDE_PLUGIN_ROOT:-}" ] && [ -f "$PLUGIN_LEXICON" ]; then
  lexicon="$PLUGIN_LEXICON"
fi
[ -z "$lexicon" ] && exit 0

ratified="$(grep -c 'status: ratified' "$lexicon" 2>/dev/null)"; ratified="${ratified:-0}"
case "$ratified" in ''|*[!0-9]*) ratified=0 ;; esac
proposals=0
[ -d ".claude/respeak/proposals" ] && proposals="$(find .claude/respeak/proposals -name '*.yaml' 2>/dev/null | wc -l | tr -d ' ')"
version="$(grep -m1 '^version:' "$lexicon" 2>/dev/null | awk '{print $2}')"

# Claude Code's Bash permission matcher cannot pre-approve a script whose
# path contains a space, so under such a plugin root the /respeak:respeak
# preamble aborts its invocation (docs/config-layers.md, "Upgrading"). Say
# so once, at session start, instead of letting the skill fail silently.
space_note=""
case "${CLAUDE_PLUGIN_ROOT:-}" in
  *" "*) space_note=" NOTE: the respeak plugin root contains a space, so /respeak:respeak will fail its permission check and abort under default permissions; reinstall the plugin under a path without spaces (the hooks still work)." ;;
esac

"$pyj" - "$lexicon" "${version:-0}" "$ratified" "${proposals:-0}" "$space_note" <<'PY' 2>/dev/null || exit 0
import json, sys
lexicon, version, ratified, proposals, space_note = sys.argv[1:6]
ctx = (f"The respeak shorthand lexicon (v{version}) is at {lexicon} with "
       f"{ratified} ratified terms; only ratified terms may be used as shorthand. "
       f"{proposals} proposals are pending human ratification. Session overrides: "
       f"/respeak:off silences the respeak hooks for this session, /respeak:on restores them.{space_note}")
print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": ctx}}))
PY
exit 0
