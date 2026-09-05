#!/bin/bash
# The style gate. Two entry points, one behaviour:
#
#   PostToolUse hook (hooks/hooks.json, matcher Write|Edit): reads the hook
#     JSON on stdin and gates tool_input.file_path.
#   CLI / CI:  respeak-gate.sh --file <path>   gates one file the same way.
#
# It runs respeak-measure.py against a Markdown file (.md .markdown .mdx —
# the resolver's gate decision uses the same list) and blocks on a failing
# style-gate report.
#
# Opt-in per project, deliberately: nothing happens unless the PROJECT layer
# (<project>/.claude/respeak/config.yaml or config.local.yaml) sets
# `gate.enabled: true`. A user-level file or a folder .respeak.yaml cannot
# turn it on (the resolver drops gate.enabled from those layers). Nearer
# layers CAN soften or harden the verdict for their own files
# (`gate.fail_on`) and add `gate.allow` regexes. The project root is found
# by the resolver the same way for every consumer (nearest
# .claude/respeak/config.yaml above the file, then $CLAUDE_PROJECT_DIR),
# so what `respeak-config.sh explain --for <file>` shows is what this
# script enforces. Contract: docs/config-layers.md.
#
# Exit 0 = allow (not applicable, gate off, the file passed, or a setup
#          problem — the gate fails OPEN; set RESPEAK_GATE_TRACE=1 to get a
#          one-line stderr note saying which).
# Exit 2 = block; stderr carries the measure report, which Claude Code feeds
#          back to the model as the error to fix. In CI, `|| exit 1` on it.
#
# bash 3.2 compatible (macOS default).
set -u

script_dir="$(cd "$(dirname "$0")" && pwd)"
RESPEAK_PY=""; RESPEAK_PY_STD=""
[ -f "$script_dir/respeak-python.sh" ] && . "$script_dir/respeak-python.sh"

trace() { [ "${RESPEAK_GATE_TRACE:-0}" = "1" ] && echo "respeak gate: $*" >&2; return 0; }

file_path=""
if [ "${1:-}" = "--file" ]; then
  file_path="${2:-}"
else
  HOOK_JSON="$(cat)"
  pyj="${RESPEAK_PY:-$RESPEAK_PY_STD}"
  if [ -z "$pyj" ]; then trace "no python3 found; allowing"; exit 0; fi
  file_path="$(printf '%s' "$HOOK_JSON" | "$pyj" -c '
import json, sys
try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)
print((data.get("tool_input") or {}).get("file_path") or "")
' 2>/dev/null)"
fi

[ -z "$file_path" ] && exit 0

# Cheap pre-filter, identical to the resolver's MARKDOWN_EXTS (which
# lowercases too): the measure script is a Markdown scanner, and most
# Write/Edit calls are not Markdown.
case "$(printf '%s' "$file_path" | tr '[:upper:]' '[:lower:]')" in
  *.md|*.markdown|*.mdx) ;;
  *) exit 0 ;;
esac

if [ -z "$RESPEAK_PY" ]; then trace "no python3 with PyYAML; allowing $file_path"; exit 0; fi
resolver="$script_dir/respeak-config.py"
measure="$script_dir/respeak-measure.py"
if [ ! -f "$resolver" ] || [ ! -f "$measure" ]; then trace "resolver or measure script missing; allowing"; exit 0; fi

resolved="$(mktemp 2>/dev/null || echo "/tmp/respeak-gate.$$.yaml")"
trap 'rm -f "$resolved"' EXIT

# No --project: the resolver discovers the root from the file and falls back
# to $CLAUDE_PROJECT_DIR, which Claude Code exports to hooks.
decision="$("$RESPEAK_PY" "$resolver" gate --for "$file_path" --write-config "$resolved" 2>/dev/null)" || {
  trace "resolver failed; allowing $file_path"; exit 0; }
[ -n "$decision" ] || { trace "resolver returned nothing; allowing $file_path"; exit 0; }

verdict="$(printf '%s' "$decision" | "$RESPEAK_PY" -c '
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    print("0 error resolver-output-unparseable"); sys.exit(0)
fail_on = d.get("fail_on") if d.get("fail_on") in ("none", "warn", "error") else "error"
print(("1" if d.get("applies") else "0") + " " + fail_on + " " + (d.get("reason") or "").replace(" ", "_"))
' 2>/dev/null)"
applies="${verdict%% *}"; rest="${verdict#* }"; fail_on="${rest%% *}"; reason="${rest#* }"

if [ "${applies:-0}" != "1" ]; then trace "not applicable to $file_path (${reason:-?})"; exit 0; fi

args=("$file_path" --fail-on "${fail_on:-error}" --config "$resolved")
plugin_root="${CLAUDE_PLUGIN_ROOT:-}"
if [ -n "$plugin_root" ] && [ -f "$plugin_root/corpus/banned-phrases.yaml" ]; then
  args+=(--corpus "$plugin_root/corpus/banned-phrases.yaml")
fi

report="$("$RESPEAK_PY" "$measure" "${args[@]}" 2>&1)"
status=$?

# measure: 0 = passed, 1 = a gate hit at or above --fail-on, 2 = setup/IO
# error (unreadable doc, corrupt corpus or config). Only 1 is a verdict;
# everything else fails open, as the header promises.
if [ "$status" -eq 1 ]; then
  echo "respeak gate: $file_path failed the style gate (fail-on: ${fail_on:-error})" >&2
  echo "$report" >&2
  exit 2
fi
if [ "$status" -ne 0 ]; then
  trace "measure exited $status (setup error, not a verdict); allowing $file_path"
  [ "${RESPEAK_GATE_TRACE:-0}" = "1" ] && echo "$report" >&2
  exit 0
fi
trace "checked $file_path (fail-on: ${fail_on:-error}): pass"
exit 0
