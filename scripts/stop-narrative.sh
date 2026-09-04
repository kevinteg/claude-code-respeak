#!/bin/bash
# Stop hook: when narrative.auto_narrative resolves true for the session's
# working directory, nudge a one-paragraph narrative after substantive turns.
# Gated so it can never loop and never fails the turn.
#
# The switch and the mode come from the layered config
# (docs/config-layers.md), resolved for the hook's cwd: the install-time
# userConfig (CLAUDE_PLUGIN_OPTION_AUTO_NARRATIVE), ~/.claude/respeak/
# config.yaml, the project's .claude/respeak/config.yaml, or a .respeak.yaml
# in the cwd's folder chain can each turn it on; nearest wins. If no
# PyYAML-capable python exists, only the userConfig env vars are consulted.
set -u

HOOK_JSON="$(cat)"

script_dir="$(cd "$(dirname "$0")" && pwd)"
RESPEAK_PY=""
[ -f "$script_dir/respeak-python.sh" ] && . "$script_dir/respeak-python.sh"

cwd="$(printf '%s' "$HOOK_JSON" | python3 -c '
import json, sys
try:
    print(json.load(sys.stdin).get("cwd") or "")
except Exception:
    print("")
' 2>/dev/null)"
project="${CLAUDE_PROJECT_DIR:-${cwd:-$(pwd)}}"

cfg_json=""
if [ -n "$RESPEAK_PY" ] && [ -f "$script_dir/respeak-config.py" ]; then
  cfg_json="$("$RESPEAK_PY" "$script_dir/respeak-config.py" resolve \
              --project "$project" --for "${cwd:-$project}" --format json 2>/dev/null)" || cfg_json=""
fi

# The program goes in via -c, never via stdin: `python3 - <<'PY'` would
# consume stdin for the script itself and leave json.load(sys.stdin) at EOF,
# which is exactly why the v0.3 hook never fired.
PY_SCRIPT=$(cat <<'PY'
import json, os, re, sys
try:
    hook = json.load(sys.stdin)
except Exception:
    sys.exit(0)
try:
    cfg = json.loads(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].strip() else {}
except Exception:
    cfg = {}
narrative = cfg.get("narrative") or {}
enabled = narrative.get("auto_narrative")
if enabled is None:  # no resolved config: the userConfig env var alone decides
    enabled = os.environ.get("CLAUDE_PLUGIN_OPTION_AUTO_NARRATIVE", "false") == "true"
if not enabled:
    sys.exit(0)
# Never fire on a continuation the hook itself caused.
if hook.get("stop_hook_active"):
    sys.exit(0)
msg = hook.get("last_assistant_message") or ""
# Milestone heuristic: substantive turns only — long output or explicit
# completion markers. Word-bounded so "abandoned" != "done" and
# "incomplete" != "complete".
markers = re.compile(r"\b(done|completed?|fixed|merged|deployed|passing)\b")
if not (len(msg) > 1500 or markers.search(msg.lower())):
    sys.exit(0)
mode = narrative.get("default_mode") or os.environ.get("CLAUDE_PLUGIN_OPTION_DEFAULT_MODE", "technical")
profile = narrative.get("profile")
tech = narrative.get("tech_level")
audience = "%s audience" % mode
if profile or tech is not None:
    audience += " (profile %s, tech_level %s)" % (profile or "-", tech if tech is not None else "-")
ctx = ("Respeak auto-narrative is enabled (mode: %s). This turn crossed a "
       "milestone. Append one short paragraph rendering the outcome for the "
       "%s, following the respeak skill's mode contract." % (mode, audience))
print(json.dumps({"hookSpecificOutput": {"hookEventName": "Stop", "additionalContext": ctx}}))
PY
)
printf '%s' "$HOOK_JSON" | python3 -c "$PY_SCRIPT" "$cfg_json" 2>/dev/null || exit 0
exit 0
