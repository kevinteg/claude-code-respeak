#!/bin/bash
# Stop hook: when auto_narrative is enabled, nudge a one-paragraph narrative
# after substantive turns. Gated so it can never loop and never fails the turn.
set -u

# userConfig gate (exported by Claude Code as CLAUDE_PLUGIN_OPTION_<KEY>)
[ "${CLAUDE_PLUGIN_OPTION_AUTO_NARRATIVE:-false}" = "true" ] || exit 0

python3 - <<'PY' 2>/dev/null || exit 0
import json, os, sys
try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)
# Never fire on a continuation the hook itself caused.
if data.get("stop_hook_active"):
    sys.exit(0)
msg = data.get("last_assistant_message") or ""
# Milestone heuristic: substantive turns only — long output or explicit
# completion markers. Word-bounded so "abandoned" != "done" and
# "incomplete" != "complete".
import re
markers = re.compile(r"\b(done|completed?|fixed|merged|deployed|passing)\b")
substantive = len(msg) > 1500 or bool(markers.search(msg.lower()))
if not substantive:
    sys.exit(0)
mode = os.environ.get("CLAUDE_PLUGIN_OPTION_DEFAULT_MODE", "technical")
ctx = (f"Respeak auto-narrative is enabled (mode: {mode}). This turn crossed a "
       f"milestone. Append one short paragraph rendering the outcome for the "
       f"{mode} audience, following the respeak skill's mode contract.")
print(json.dumps({"hookSpecificOutput": {"hookEventName": "Stop", "additionalContext": ctx}}))
PY
exit 0
