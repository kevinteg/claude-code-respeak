#!/bin/bash
# PostToolUse hook (matcher: Write|Edit). Runs respeak-measure.py against a
# just-written/edited Markdown file and blocks the tool result on a failing
# style-gate report.
#
# Opt-in per project, deliberately: this hook does nothing unless
# <project>/.claude/respeak/config.yaml exists AND sets `gate.enabled: true`.
# The corpus false-positived on literal networking prose ("spine switches")
# before the exceptions: mechanism existed, so gating every project silently
# by default was judged too risky — a human turns this on once a project
# trusts its `gate.exclude`/`gate.allow`. See config/respeak.config.yaml's
# `gate:` block for the full knob list and skills/init/SKILL.md for seeding.
#
# stdin: the PostToolUse hook JSON, e.g. {"tool_input": {"file_path": ...}}.
# Exit 0 = allow (not applicable, gate off, or the file passed).
# Exit 2 = block; stderr carries the measure report, which Claude Code feeds
#          back to the model as the error to fix.
#
# bash 3.2 compatible (macOS default): indexed arrays only, no associative
# arrays, no mapfile. No jq dependency — JSON handling is python3 -c.
set -u

HOOK_JSON="$(cat)"

file_path="$(printf '%s' "$HOOK_JSON" | python3 -c '
import json, sys
try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)
print((data.get("tool_input") or {}).get("file_path") or "")
' 2>/dev/null)"

[ -z "$file_path" ] && exit 0

case "$file_path" in
  *.md) ;;
  *) exit 0 ;;
esac

project_dir="${CLAUDE_PROJECT_DIR:-$(pwd)}"
config="$project_dir/.claude/respeak/config.yaml"
[ -f "$config" ] || exit 0

# Read the gate block; exits silently (empty stdout) if pyyaml is missing,
# the config fails to parse, or gate.enabled is not true — any of those
# means "do nothing", per the opt-in contract above.
gate_json="$(python3 -c '
import json, sys
try:
    import yaml
except ImportError:
    sys.exit(0)
path = sys.argv[1]
try:
    cfg = yaml.safe_load(open(path)) or {}
except Exception:
    sys.exit(0)
gate = cfg.get("gate") or {}
if not gate.get("enabled"):
    sys.exit(0)
print(json.dumps({
    "include": gate.get("include") or ["**/*.md"],
    "exclude": gate.get("exclude") or [],
    "fail_on": gate.get("fail_on") or "error",
}))
' "$config" 2>/dev/null)"

[ -z "$gate_json" ] && exit 0

# Path relative to the project dir, for glob matching against include/exclude.
rel_path="$file_path"
case "$file_path" in
  "$project_dir"/*) rel_path="${file_path#"$project_dir"/}" ;;
esac

matched="$(python3 -c '
import fnmatch, json, sys

gate = json.loads(sys.argv[1])
rel_path = sys.argv[2]

def glob_match(path, patterns):
    for p in patterns:
        cands = [p]
        # fnmatch is not path-aware, so "**/*.md" (a leading-zero-dirs glob)
        # would otherwise require a literal "/" before the match; also try
        # the pattern with that prefix stripped so top-level files match too.
        if p.startswith("**/"):
            cands.append(p[3:])
        for c in cands:
            if fnmatch.fnmatch(path, c):
                return True
    return False

included = glob_match(rel_path, gate["include"])
excluded = glob_match(rel_path, gate["exclude"]) if gate["exclude"] else False
print("1" if (included and not excluded) else "0")
' "$gate_json" "$rel_path")"

[ "$matched" = "1" ] || exit 0

fail_on="$(python3 -c 'import json, sys; print(json.loads(sys.argv[1])["fail_on"])' "$gate_json")"

plugin_root="${CLAUDE_PLUGIN_ROOT:-}"
script_dir="$(cd "$(dirname "$0")" && pwd)"
measure="$script_dir/respeak-measure.py"
[ -f "$measure" ] || exit 0   # fail open: no measure script, nothing to enforce

args=("$file_path" --fail-on "$fail_on" --config "$config")
if [ -n "$plugin_root" ] && [ -f "$plugin_root/corpus/banned-phrases.yaml" ]; then
  args+=(--corpus "$plugin_root/corpus/banned-phrases.yaml")
fi

report="$(python3 "$measure" "${args[@]}" 2>&1)"
status=$?

if [ "$status" -ne 0 ]; then
  echo "respeak gate: $file_path failed the style gate (fail-on: $fail_on)" >&2
  echo "$report" >&2
  exit 2
fi

exit 0
