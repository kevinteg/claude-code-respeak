#!/bin/bash
# SessionStart hook: inject factual lexicon status as additionalContext.
# Never fails the session — any error exits 0 with no output.
set -u

PROJECT_LEXICON=".claude/respeak/lexicon.yaml"
PLUGIN_LEXICON="${CLAUDE_PLUGIN_ROOT:-}/corpus/lexicon.yaml"

lexicon=""
if [ -f "$PROJECT_LEXICON" ]; then
  lexicon="$PROJECT_LEXICON"
elif [ -n "${CLAUDE_PLUGIN_ROOT:-}" ] && [ -f "$PLUGIN_LEXICON" ]; then
  lexicon="$PLUGIN_LEXICON"
fi
[ -z "$lexicon" ] && exit 0

ratified=$(grep -c 'status: ratified' "$lexicon" 2>/dev/null || echo 0)
proposals=0
[ -d ".claude/respeak/proposals" ] && proposals=$(find .claude/respeak/proposals -name '*.yaml' 2>/dev/null | wc -l)
version=$(grep -m1 '^version:' "$lexicon" 2>/dev/null | awk '{print $2}')

# Claude Code's Bash permission matcher cannot pre-approve a script whose
# path contains a space, so under such a plugin root the /respeak:respeak
# preamble aborts its invocation (docs/config-layers.md, "Upgrading"). Say
# so once, at session start, instead of letting the skill fail silently.
space_note=""
case "${CLAUDE_PLUGIN_ROOT:-}" in
  *" "*) space_note=" NOTE: the respeak plugin root contains a space, so /respeak:respeak will fail its permission check and abort under default permissions; reinstall the plugin under a path without spaces (the hooks still work)." ;;
esac

python3 - "$lexicon" "${version:-0}" "$ratified" "$proposals" "$space_note" <<'PY' 2>/dev/null || exit 0
import json, sys
lexicon, version, ratified, proposals, space_note = sys.argv[1:6]
ctx = (f"The respeak shorthand lexicon (v{version}) is at {lexicon} with "
       f"{ratified} ratified terms; only ratified terms may be used as shorthand. "
       f"{proposals} proposals are pending human ratification.{space_note}")
print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": ctx}}))
PY
exit 0
