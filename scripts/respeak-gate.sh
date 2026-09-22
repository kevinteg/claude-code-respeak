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
# What a verdict is measured against is `gate.block_on`. The default,
# `introduced`, hands measure a --baseline of the file as it was, so the
# write is judged on the hits it ADDED and a document that already carries
# one (a banned term inside a heading, which the editorial pass may not be
# able to move) stays editable; the leftovers are reported to the model
# instead, as PostToolUse additionalContext on a pass. `any` drops the
# baseline and gates the whole file, the behaviour before v0.6.
#
# The baseline, in order: the committed version of the file
# (`git show HEAD:./<name>`); else, for an Edit, the pre-edit text rebuilt
# by putting tool_input.old_string back where new_string now sits; else an
# empty file, so a brand-new document is gated whole. Each step falls
# through to the next on any failure, and RESPEAK_GATE_TRACE=1 names the
# one used. The --file form has no edit to compare against and is the CI
# surface, so it keeps whole-file semantics whatever block_on says, unless
# --baseline-ref REF names a git ref to measure against.
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
# Session overrides (scripts/respeak-override.sh) sit above the config:
# RESPEAK_HOOKS=off or RESPEAK_GATE=off silences the gate for a launch,
# RESPEAK_GATE=on runs it as if gate.enabled were true, and a marker from
# /respeak:off or /respeak:on does the same for one session and outranks
# the environment. The --file form has no session, so only the
# environment applies to it.
#
# Exit 0 = allow (not applicable, gate off, overridden off, the file passed,
#          or a setup problem — the gate fails OPEN; set RESPEAK_GATE_TRACE=1
#          to get a one-line stderr note saying which). A pass over a file
#          that still carries hits the write did not introduce prints one
#          line of JSON on stdout naming them, as PostToolUse
#          additionalContext.
# Exit 2 = block; stderr carries the measure report, which Claude Code feeds
#          back to the model as the error to fix. In CI, `|| exit 1` on it.
#
# bash 3.2 compatible (macOS default).
set -u

script_dir="$(cd "$(dirname "$0")" && pwd)"
RESPEAK_PY=""; RESPEAK_PY_STD=""
[ -f "$script_dir/respeak-python.sh" ] && . "$script_dir/respeak-python.sh"
[ -f "$script_dir/respeak-override.sh" ] && . "$script_dir/respeak-override.sh"

trace() { [ "${RESPEAK_GATE_TRACE:-0}" = "1" ] && echo "respeak gate: $*" >&2; return 0; }

file_path=""; session_id=""; cli_mode=0; has_edit=0; baseline_ref=""; HOOK_JSON=""
if [ "${1:-}" = "--file" ]; then
  cli_mode=1
  shift
  file_path="${1:-}"
  [ $# -gt 0 ] && shift
  while [ $# -gt 0 ]; do
    if [ "$1" = "--baseline-ref" ]; then baseline_ref="${2:-}"; shift; fi
    shift
  done
else
  HOOK_JSON="$(cat)"
  pyj="${RESPEAK_PY:-$RESPEAK_PY_STD}"
  if [ -z "$pyj" ]; then trace "no python3 found; allowing"; exit 0; fi
  parsed="$(printf '%s' "$HOOK_JSON" | "$pyj" -c '
import json, sys
try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)
ti = data.get("tool_input") or {}
print(ti.get("file_path") or "")
print(str(data.get("session_id") or ""))
# An Edit carries the two strings the pre-edit text can be rebuilt from; a
# Write carries neither, and is measured against the committed file or
# nothing at all.
print("edit" if isinstance(ti.get("old_string"), str) and isinstance(ti.get("new_string"), str) else "")
' 2>/dev/null)"
  file_path="$(printf '%s\n' "$parsed" | sed -n '1p')"
  session_id="$(printf '%s\n' "$parsed" | sed -n '2p')"
  [ "$(printf '%s\n' "$parsed" | sed -n '3p')" = "edit" ] && has_edit=1
fi

[ -z "$file_path" ] && exit 0

# Session overrides outrank the configuration (see the header).
force_on=0
if command -v respeak_override >/dev/null 2>&1; then
  ov="$(respeak_override gate "$session_id")"
  case "${ov%% *}" in
    off)     trace "gate disabled for this session (${ov#* }); allowing $file_path"; exit 0 ;;
    gate-on) force_on=1; trace "gate forced on for this session (${ov#* })" ;;
  esac
fi

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
baseline=""
trap 'rm -f "$resolved" ${baseline:+"$baseline"}' EXIT

# No --project: the resolver discovers the root from the file and falls back
# to $CLAUDE_PROJECT_DIR, which Claude Code exports to hooks.
gate_args=(gate --for "$file_path" --write-config "$resolved")
[ "$force_on" -eq 1 ] && gate_args+=(--set gate.enabled=true)
decision="$("$RESPEAK_PY" "$resolver" "${gate_args[@]}" 2>/dev/null)" || {
  trace "resolver failed; allowing $file_path"; exit 0; }
[ -n "$decision" ] || { trace "resolver returned nothing; allowing $file_path"; exit 0; }

verdict="$(printf '%s' "$decision" | "$RESPEAK_PY" -c '
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    print("0 error introduced resolver-output-unparseable"); sys.exit(0)
fail_on = d.get("fail_on") if d.get("fail_on") in ("none", "warn", "error") else "error"
block_on = d.get("block_on") if d.get("block_on") in ("introduced", "any") else "introduced"
print(("1" if d.get("applies") else "0") + " " + fail_on + " " + block_on + " "
      + (d.get("reason") or "").replace(" ", "_"))
' 2>/dev/null)"
applies="${verdict%% *}"; rest="${verdict#* }"
fail_on="${rest%% *}"; rest="${rest#* }"
block_on="${rest%% *}"; reason="${rest#* }"

if [ "${applies:-0}" != "1" ]; then trace "not applicable to $file_path (${reason:-?})"; exit 0; fi

args=("$file_path" --fail-on "${fail_on:-error}" --config "$resolved")
plugin_root="${CLAUDE_PLUGIN_ROOT:-}"
if [ -n "$plugin_root" ] && [ -f "$plugin_root/corpus/banned-phrases.yaml" ]; then
  args+=(--corpus "$plugin_root/corpus/banned-phrases.yaml")
fi

# The baseline: the file as it was, so measure can tell what this write
# ADDED from what it merely inherited (the header's "block_on" note lists
# the order). Every step falls through on failure, because a missing git, a
# shallow checkout, or a string that moved must cost a wider scan, never a
# blocked write.
want_baseline=0
[ "$cli_mode" -eq 0 ] && [ "${block_on:-introduced}" = "introduced" ] && want_baseline=1
[ "$cli_mode" -eq 1 ] && [ -n "$baseline_ref" ] && want_baseline=1
if [ "$want_baseline" -eq 1 ]; then
  baseline="$(mktemp 2>/dev/null || echo "/tmp/respeak-gate.$$.base")"
  baseline_from=""
  ref="${baseline_ref:-HEAD}"
  # `-C <dir>` with a `./<name>` path resolves the file inside whatever
  # repository holds it, whatever the caller's working directory is.
  if git -C "$(dirname "$file_path")" show "$ref:./$(basename "$file_path")" > "$baseline" 2>/dev/null; then
    baseline_from="$ref"
  else
    : > "$baseline"
    if [ "$cli_mode" -eq 1 ]; then
      # --baseline-ref named a ref that does not carry this file; the CI
      # caller asked for a comparison, so say it did not happen.
      rm -f "$baseline"; baseline=""
      trace "$ref does not carry $file_path; gating the whole file"
    elif [ "$has_edit" -eq 1 ] && printf '%s' "$HOOK_JSON" | "$RESPEAK_PY" -c '
import json, sys
data = json.load(sys.stdin)
ti = data.get("tool_input") or {}
old, new = ti["old_string"], ti["new_string"]
if not new:
    sys.exit(1)          # a pure deletion leaves no anchor to put old back at
with open(sys.argv[1], encoding="utf-8") as f:
    cur = f.read()
if new not in cur:
    sys.exit(1)          # the text moved on since the edit; not our baseline
pre = cur.replace(new, old) if ti.get("replace_all") else cur.replace(new, old, 1)
with open(sys.argv[2], "w", encoding="utf-8") as f:
    f.write(pre)
' "$file_path" "$baseline" 2>/dev/null; then
      baseline_from="the pre-edit text"
    else
      : > "$baseline"
      baseline_from="an empty file (nothing to compare against)"
    fi
  fi
  if [ -n "$baseline" ]; then
    args+=(--baseline "$baseline")
    trace "baseline for $file_path: $baseline_from"
  fi
fi

report="$("$RESPEAK_PY" "$measure" "${args[@]}" 2>&1)"
status=$?

# measure: 0 = passed, 1 = a gate hit at or above --fail-on, 2 = setup/IO
# error (unreadable doc, corrupt corpus or config). Only 1 is a verdict;
# everything else fails open, as the header promises.
if [ "$status" -eq 1 ]; then
  echo "respeak gate: $file_path failed the style gate (fail-on: ${fail_on:-error}${baseline:+, on what this write introduced})" >&2
  echo "$report" >&2
  exit 2
fi
if [ "$status" -ne 0 ]; then
  trace "measure exited $status (setup error, not a verdict); allowing $file_path"
  [ "${RESPEAK_GATE_TRACE:-0}" = "1" ] && echo "$report" >&2
  exit 0
fi
# A pass with notes: the write introduced nothing, but the document still
# carries hits it inherited. Blocking on those is the trap block_on exists
# to remove, so instead they reach the model as PostToolUse
# additionalContext — the hook reference's field for feedback that does not
# block — and the session decides whether the pass can reach them. The
# --file form has no model to tell, so it says the same thing in prose.
# Only hits at or above fail_on are named: those are the ones `any` would
# have blocked on. A page's density-tier tells (em-dashes, dividers) are
# budget material, and listing dozens of them would invite exactly the
# layout edits the editorial pass is told not to make.
if [ -n "$baseline" ] && ! printf '%s\n' "$report" | grep -q '^baseline: 0 pre-existing'; then
  printf '%s\n' "$report" | "$RESPEAK_PY" -c '
import json, re, sys
path, form, fail_on = sys.argv[1], sys.argv[2], sys.argv[3]
report = sys.stdin.read()
rank = {"error": 2, "warn": 1, "density": 1}      # density hits count as warn-level
threshold = {"error": 2, "warn": 1, "none": 0}.get(fail_on, 2)
section, rules, n = None, [], 0
for line in report.splitlines():
    s = re.match(r"^(error|warn|density): ", line)
    if s:
        section = s.group(1)
        continue
    r = re.match(r"^\s+\d+\s+(\[.+\].*?)\s+\[new \d+, pre-existing ([1-9]\d*)\]$", line)
    if r and section and rank[section] >= threshold:
        rules.append(r.group(1))
        n += int(r.group(2))
if n <= 0:
    sys.exit(0)
msg = ("respeak gate: %s passed; %d pre-existing style hit(s) remain that would block "
       "(fail-on: %s), not introduced by this edit: %s" % (path, n, fail_on, ", ".join(rules)))
if form == "json":
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse",
                                             "additionalContext": msg}}))
else:
    print(msg)
' "$file_path" "$([ "$cli_mode" -eq 1 ] && echo text || echo json)" "${fail_on:-error}" 2>/dev/null
fi
trace "checked $file_path (fail-on: ${fail_on:-error}): pass"
exit 0
