#!/bin/bash
# Gate, and optionally verify, a set of Markdown files the way the hooks
# would: the same resolver, the same include/exclude, the same verdict a
# Write in an editor session gets. The command-line and CI entry point.
#
#   respeak-check.sh [--verify <git-ref>] [--prose-keys KEYS] [--allow-strings]
#                    [--allow-restructure] [--quiet] [FILE...]
#
# With no FILE, every Markdown file git knows about under the current
# directory is checked: tracked files plus untracked files that are not
# ignored, so a new page is gated before its first commit. The project's
# gate.include and gate.exclude decide which of them apply, so an excluded
# file reports "skipped", never "blocked".
#
# --verify REF  For each file that differs from REF, also require the edit
#               to be meaning-invariant (scripts/respeak-verify-edit.py):
#               headings, block structure, links, fenced code, inline code,
#               and numbers unchanged. Files absent from REF are new and are
#               not verified. What the verifier may relax comes from each
#               file's resolved configuration, `editorial_pass`:
#               `restructure: apply` passes --allow-restructure,
#               `verify.prose_keys` passes --prose-keys, `verify.allow_strings`
#               passes --allow-strings, and `verify.paths` (git pathspecs,
#               read from the project layer) names the non-Markdown files
#               (page generators, data YAML) that are verified as well, though
#               never gated. --prose-keys, --allow-strings, and
#               --allow-restructure set the same things for one run, for every
#               file, on top of the configuration.
#
# Session overrides (RESPEAK_GATE, RESPEAK_HOOKS), RESPEAK_CONFIG, and the
# session provider (CLAUDE_CODE_SESSION_ID, XDG_STATE_HOME) are ignored here
# on purpose: this command answers what the committed configuration says,
# not what one session or one shell chose. Each file is gated with
# `respeak-gate.sh --committed`, so a folder file or an ignored local file
# cannot soften the verdict either; a file the gate cannot judge (exit 3)
# is an ERROR, never a pass. Exit 0 = every file allowed and verified; 1 =
# at least one block, error, or verification failure; 2 = usage or setup
# error, a git failure (the run stops at the first, with its line), or the
# per-file counts do not add up to the files named.
# bash 3.2 compatible.
set -u
unset RESPEAK_GATE RESPEAK_HOOKS RESPEAK_CONFIG CLAUDE_CODE_SESSION_ID XDG_STATE_HOME 2>/dev/null || true
script_dir="$(cd "$(dirname "$0")" && pwd)"
RESPEAK_PY=""; RESPEAK_PY_STD=""
. "$script_dir/respeak-python.sh"
[ -n "$RESPEAK_PY" ] || { echo "respeak-check: no python3 with PyYAML found; set RESPEAK_PYTHON or install PyYAML" >&2; exit 2; }
export CLAUDE_PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$script_dir/.." && pwd)}"
resolver="$script_dir/respeak-config.py"

ref=""; quiet=0; files=(); cli_keys=""; cli_strings=0; cli_restructure=0
while [ $# -gt 0 ]; do
  case "$1" in
    --verify) [ $# -ge 2 ] || { echo "respeak-check: --verify needs a git ref" >&2; exit 2; }; ref="$2"; shift 2 ;;
    --prose-keys) [ $# -ge 2 ] || { echo "respeak-check: --prose-keys needs a key list" >&2; exit 2; }; cli_keys="$2"; shift 2 ;;
    --allow-strings) cli_strings=1; shift ;;
    --allow-restructure) cli_restructure=1; shift ;;
    --quiet) quiet=1; shift ;;
    -h|--help) sed -n '2,39p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    --*) echo "respeak-check: unknown option $1" >&2; exit 2 ;;
    *) files+=("$1"); shift ;;
  esac
done
named="${#files[@]}"
if [ "${#files[@]}" -eq 0 ]; then
  git rev-parse --show-toplevel >/dev/null 2>&1 || { echo "respeak-check: not in a git repository; name the files to check" >&2; exit 2; }
  while IFS= read -r f; do [ -n "$f" ] && files+=("$f"); done < <(git ls-files --cached --others --exclude-standard -- '*.md' '*.markdown' '*.mdx' 2>/dev/null | sort -u)
fi
[ "${#files[@]}" -gt 0 ] || { echo "respeak-check: nothing to check"; exit 0; }
if [ -n "$ref" ]; then git rev-parse --verify --quiet "$ref^{commit}" >/dev/null || { echo "respeak-check: unknown git ref $ref" >&2; exit 2; }; fi
launch_dir="$(pwd -P)"

# The verifier's leniencies for one file, one flag per line, from the
# file's resolved `editorial_pass`. A resolver failure yields no flags: the
# strict verdict, never a skipped check.
verify_flags() {
  "$RESPEAK_PY" "$resolver" resolve --for "$1" --launch-dir "$launch_dir" --format json 2>/dev/null \
    | "$RESPEAK_PY" -c '
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
ep = d.get("editorial_pass") or {}
v = ep.get("verify") or {}
keys = v.get("prose_keys") or []
if isinstance(keys, list) and keys:
    print("--prose-keys=" + ",".join(str(k) for k in keys))
if v.get("allow_strings") is True:
    print("--allow-strings")
if ep.get("restructure") == "apply":
    print("--allow-restructure")
' 2>/dev/null
}

# The non-Markdown files the project asks to have verified
# (editorial_pass.verify.paths): only with --verify, and only when the
# file list was not given by hand.
vonly=(); globs=()
if [ -n "$ref" ] && [ "$named" -eq 0 ]; then
  while IFS= read -r g; do [ -n "$g" ] && globs+=("$g"); done < <("$RESPEAK_PY" "$resolver" resolve --for "$launch_dir" --launch-dir "$launch_dir" --format json 2>/dev/null | "$RESPEAK_PY" -c '
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
for g in ((d.get("editorial_pass") or {}).get("verify") or {}).get("paths") or []:
    print(g)
' 2>/dev/null)
  if [ "${#globs[@]}" -gt 0 ]; then
    while IFS= read -r f; do
      case "$f" in ""|*.md|*.markdown|*.mdx) continue ;; esac
      vonly+=("$f")
    done < <(git ls-files --cached --others --exclude-standard -- "${globs[@]}" 2>/dev/null | sort -u)
  fi
fi

say() { [ "$quiet" -eq 1 ] || echo "$*"; }
# The gate keeps the resolver's stderr to itself, so a gate exit 3 asks the
# resolver once more for its reason; a `git failed` line is a failure of the
# whole run, never one file's error (review ADV11-2).
git_failure() {
  "$RESPEAK_PY" "$resolver" gate --for "$1" --committed 2>&1 >/dev/null | grep -m1 'respeak-config: git failed'
}
tmp="$(mktemp 2>/dev/null)" || { echo "respeak-check: mktemp failed" >&2; exit 2; }; trap 'rm -f "$tmp" "$tmp.before"' EXIT
passed=0; skipped=0; blocked=0; errors=0; missing=0; verified=0; vfailed=0

# Verify one file against REF when it exists there and differs.
verify_one() {
  git cat-file -e "$ref:$1" 2>/dev/null && ! git diff --quiet "$ref" -- "$1" 2>/dev/null || return 0
  git show "$ref:$1" > "$tmp.before"
  vargs=()
  while IFS= read -r a; do [ -n "$a" ] && vargs+=("$a"); done < <(verify_flags "$1")
  [ -n "$cli_keys" ] && vargs+=("--prose-keys=$cli_keys")
  [ "$cli_strings" -eq 1 ] && vargs+=(--allow-strings)
  [ "$cli_restructure" -eq 1 ] && vargs+=(--allow-restructure)
  note=""; [ "${#vargs[@]}" -gt 0 ] && note="; ${vargs[*]}"
  if "$RESPEAK_PY" "$script_dir/respeak-verify-edit.py" ${vargs[@]+"${vargs[@]}"} "$tmp.before" "$1" >"$tmp" 2>&1; then
    verified=$((verified + 1)); say "verified $1 (prose-only edit since $ref$note)"
  else
    vfailed=$((vfailed + 1)); echo "CHANGED  $1 (meaning-carrying content differs from $ref)"; sed 's/^/         /' "$tmp"
  fi
}

for f in "${files[@]}"; do
  [ -f "$f" ] || { missing=$((missing + 1)); say "missing  $f"; continue; }
  RESPEAK_GATE_TRACE=1 "$script_dir/respeak-gate.sh" --file "$f" --committed >"$tmp" 2>&1; rc=$?
  if [ "$rc" -eq 3 ] && gitfail="$(git_failure "$f")"; then
    echo "$gitfail" >&2
    echo "respeak-check: stopped at $f; a git failure spoils every file, not one" >&2
    exit 2
  elif [ "$rc" -eq 2 ]; then
    blocked=$((blocked + 1)); echo "BLOCKED  $f"; sed 's/^/         /' "$tmp"
  elif [ "$rc" -ne 0 ]; then
    errors=$((errors + 1)); echo "ERROR    $f"; sed 's/^/         /' "$tmp"
  elif grep -q 'not applicable' "$tmp"; then
    skipped=$((skipped + 1)); say "skipped  $f"
  elif grep -q -E 'allowing' "$tmp" && ! grep -q ': pass' "$tmp"; then
    skipped=$((skipped + 1)); say "skipped  $f ($(grep -o -E 'gate: .*' "$tmp" | head -1 | cut -c7-))"
  else
    passed=$((passed + 1)); say "pass     $f"
  fi
  [ -n "$ref" ] && verify_one "$f"
done
for f in ${vonly[@]+"${vonly[@]}"}; do
  [ -f "$f" ] && verify_one "$f"
done
# Invariant: every file named lands in exactly one count. A file that
# slipped through every branch would otherwise read as a quiet green.
counted=$((passed + skipped + blocked + errors + missing))
if [ "$counted" -ne "${#files[@]}" ]; then
  echo "respeak-check: counted $counted of ${#files[@]} files; refusing to report" >&2
  exit 2
fi
echo "respeak-check: $passed passed, $skipped skipped, $blocked blocked, $errors errors${ref:+; $verified verified, $vfailed changed against $ref}"
[ "$blocked" -eq 0 ] && [ "$errors" -eq 0 ] && [ "$vfailed" -eq 0 ]
