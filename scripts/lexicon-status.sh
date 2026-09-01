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

python3 - "$lexicon" "${version:-0}" "$ratified" "$proposals" <<'PY' 2>/dev/null || exit 0
import json, sys
lexicon, version, ratified, proposals = sys.argv[1:5]
ctx = (f"The respeak shorthand lexicon (v{version}) is at {lexicon} with "
       f"{ratified} ratified terms; only ratified terms may be used as shorthand. "
       f"{proposals} proposals are pending human ratification.")
print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": ctx}}))
PY
exit 0
