#!/bin/bash
# Gate, and optionally verify, a set of Markdown files the way the hooks
# would: the same resolver, the same include/exclude, the same verdict a
# Write in an editor session gets. The command-line and CI entry point.
#
#   respeak-check.sh [--verify <git-ref>] [--quiet] [FILE...]
#
# With no FILE, every Markdown file git knows about under the current
# directory is checked: tracked files plus untracked files that are not
# ignored, so a new page is gated before its first commit. The project's
# gate.include and gate.exclude decide which of them apply, so an excluded
# file reports "skipped", never "blocked".
#
# --verify REF  For each file that differs from REF, also require the edit
#               to be meaning-invariant (scripts/respeak-verify-edit.py):
#               headings, links, fenced code, inline code, and numbers
#               unchanged. Files absent from REF are new and are not verified.
#
# Session overrides (RESPEAK_GATE, RESPEAK_HOOKS) are ignored here on
# purpose: this command answers what the configuration says, not what one
# session chose. Exit 0 = every file allowed and verified; 1 = at least one
# block or verification failure; 2 = usage or setup error.
# bash 3.2 compatible.
set -u
unset RESPEAK_GATE RESPEAK_HOOKS 2>/dev/null || true
script_dir="$(cd "$(dirname "$0")" && pwd)"
RESPEAK_PY=""; RESPEAK_PY_STD=""
. "$script_dir/respeak-python.sh"
[ -n "$RESPEAK_PY" ] || { echo "respeak-check: no python3 with PyYAML found; set RESPEAK_PYTHON or install PyYAML" >&2; exit 2; }
export CLAUDE_PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$script_dir/.." && pwd)}"

ref=""; quiet=0; files=()
while [ $# -gt 0 ]; do
  case "$1" in
    --verify) [ $# -ge 2 ] || { echo "respeak-check: --verify needs a git ref" >&2; exit 2; }; ref="$2"; shift 2 ;;
    --quiet) quiet=1; shift ;;
    -h|--help) sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    --*) echo "respeak-check: unknown option $1" >&2; exit 2 ;;
    *) files+=("$1"); shift ;;
  esac
done
if [ "${#files[@]}" -eq 0 ]; then
  git rev-parse --show-toplevel >/dev/null 2>&1 || { echo "respeak-check: not in a git repository; name the files to check" >&2; exit 2; }
  while IFS= read -r f; do [ -n "$f" ] && files+=("$f"); done < <(git ls-files --cached --others --exclude-standard -- '*.md' '*.markdown' '*.mdx' 2>/dev/null | sort -u)
fi
[ "${#files[@]}" -gt 0 ] || { echo "respeak-check: nothing to check"; exit 0; }
if [ -n "$ref" ]; then git rev-parse --verify --quiet "$ref^{commit}" >/dev/null || { echo "respeak-check: unknown git ref $ref" >&2; exit 2; }; fi

say() { [ "$quiet" -eq 1 ] || echo "$*"; }
tmp="$(mktemp 2>/dev/null || echo "/tmp/respeak-check.$$")"; trap 'rm -f "$tmp" "$tmp.before"' EXIT
passed=0; skipped=0; blocked=0; verified=0; vfailed=0
for f in "${files[@]}"; do
  [ -f "$f" ] || { say "missing  $f"; continue; }
  RESPEAK_GATE_TRACE=1 "$script_dir/respeak-gate.sh" --file "$f" >"$tmp" 2>&1; rc=$?
  if [ "$rc" -eq 2 ]; then
    blocked=$((blocked + 1)); echo "BLOCKED  $f"; sed 's/^/         /' "$tmp"
  elif grep -q 'not applicable' "$tmp"; then
    skipped=$((skipped + 1)); say "skipped  $f"
  elif grep -q -E 'allowing' "$tmp" && ! grep -q ': pass' "$tmp"; then
    skipped=$((skipped + 1)); say "skipped  $f ($(grep -o -E 'gate: .*' "$tmp" | head -1 | cut -c7-))"
  else
    passed=$((passed + 1)); say "pass     $f"
  fi
  if [ -n "$ref" ] && git cat-file -e "$ref:$f" 2>/dev/null && ! git diff --quiet "$ref" -- "$f" 2>/dev/null; then
    git show "$ref:$f" > "$tmp.before"
    if "$RESPEAK_PY" "$script_dir/respeak-verify-edit.py" "$tmp.before" "$f" >"$tmp" 2>&1; then
      verified=$((verified + 1)); say "verified $f (prose-only edit since $ref)"
    else
      vfailed=$((vfailed + 1)); echo "CHANGED  $f (meaning-carrying content differs from $ref)"; sed 's/^/         /' "$tmp"
    fi
  fi
done
echo "respeak-check: $passed passed, $skipped skipped, $blocked blocked${ref:+; $verified verified, $vfailed changed against $ref}"
[ "$blocked" -eq 0 ] && [ "$vfailed" -eq 0 ]
