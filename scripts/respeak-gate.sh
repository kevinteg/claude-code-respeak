#!/bin/bash
# PostToolUse hook (matcher: Write|Edit). Runs respeak-measure.py against a
# just-written/edited Markdown file and blocks the tool result on a failing
# style-gate report.
#
# Opt-in per project, deliberately: this hook does nothing unless the
# PROJECT layer (<project>/.claude/respeak/config.yaml or config.local.yaml)
# sets `gate.enabled: true`. A user-level file or a folder .respeak.yaml
# cannot turn it on (the resolver drops gate.enabled from those layers), so
# the corpus never silently gates someone else's repo. What the nearer
# layers CAN do is soften or harden the verdict for their own files
# (`gate.fail_on`) and add `gate.allow` regexes. The full stack, and which
# layer decided each key, is docs/config-layers.md and
#   bash scripts/respeak-config.sh explain --for <file>
#
# stdin: the PostToolUse hook JSON, e.g. {"tool_input": {"file_path": ...}}.
# Exit 0 = allow (not applicable, gate off, or the file passed).
# Exit 2 = block; stderr carries the measure report, which Claude Code feeds
#          back to the model as the error to fix.
#
# bash 3.2 compatible (macOS default). Fails open on every setup problem: no
# PyYAML-capable python, no resolver, no measure script.
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

script_dir="$(cd "$(dirname "$0")" && pwd)"
RESPEAK_PY=""
[ -f "$script_dir/respeak-python.sh" ] && . "$script_dir/respeak-python.sh"
[ -n "$RESPEAK_PY" ] || exit 0

resolver="$script_dir/respeak-config.py"
measure="$script_dir/respeak-measure.py"
[ -f "$resolver" ] && [ -f "$measure" ] || exit 0

project_dir="${CLAUDE_PROJECT_DIR:-$(pwd)}"

resolved="$(mktemp 2>/dev/null || echo "/tmp/respeak-gate.$$.yaml")"
trap 'rm -f "$resolved"' EXIT

decision="$("$RESPEAK_PY" "$resolver" gate --project "$project_dir" --for "$file_path" \
            --write-config "$resolved" 2>/dev/null)" || exit 0
[ -n "$decision" ] || exit 0

read -r applies fail_on <<EOF
$(printf '%s' "$decision" | "$RESPEAK_PY" -c '
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    print("0 error"); sys.exit(0)
fail_on = d.get("fail_on") if d.get("fail_on") in ("none", "warn", "error") else "error"
print(("1" if d.get("applies") else "0") + " " + fail_on)
' 2>/dev/null)
EOF

[ "${applies:-0}" = "1" ] || exit 0

args=("$file_path" --fail-on "${fail_on:-error}" --config "$resolved")
plugin_root="${CLAUDE_PLUGIN_ROOT:-}"
if [ -n "$plugin_root" ] && [ -f "$plugin_root/corpus/banned-phrases.yaml" ]; then
  args+=(--corpus "$plugin_root/corpus/banned-phrases.yaml")
fi

report="$("$RESPEAK_PY" "$measure" "${args[@]}" 2>&1)"
status=$?

if [ "$status" -ne 0 ]; then
  echo "respeak gate: $file_path failed the style gate (fail-on: ${fail_on:-error})" >&2
  echo "$report" >&2
  exit 2
fi

exit 0
