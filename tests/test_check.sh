#!/bin/bash
# Tests for scripts/respeak-check.sh, the command-line and CI form of the
# gate plus meaning-invariance verification. Bash 3.2 compatible.
#
# Run: bash tests/test_check.sh
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$HERE/.." && pwd)"
CHECK="$REPO_ROOT/scripts/respeak-check.sh"
pass=0; fail=0
check() { if [ "$2" -eq "$3" ]; then pass=$((pass + 1)); echo "ok   - $1"; else fail=$((fail + 1)); echo "FAIL - $1 (expected exit $2, got $3)"; fi; }
check_out() { if printf '%s' "$3" | grep -q -- "$2"; then pass=$((pass + 1)); echo "ok   - $1"; else fail=$((fail + 1)); echo "FAIL - $1 (expected '$2' in: $3)"; fi; }

work="$(mktemp -d)"; work="$(cd "$work" && pwd -P)"
trap 'rm -rf "$work"' EXIT
export RESPEAK_CACHE_DIR="$work/cache"
export CLAUDE_CONFIG_DIR="$work/no-user-config"; mkdir -p "$CLAUDE_CONFIG_DIR"
export CLAUDE_PLUGIN_ROOT="$REPO_ROOT"
unset RESPEAK_GATE RESPEAK_HOOKS CLAUDE_PROJECT_DIR RESPEAK_CONFIG 2>/dev/null || true

proj="$work/proj"; mkdir -p "$proj/.claude/respeak" "$proj/docs" "$proj/research"
printf 'version: 3\ngate: {enabled: true, include: ["**/*.md"], exclude: ["research/**"], fail_on: error}\n' > "$proj/.claude/respeak/config.yaml"
printf '# Guide\n\nThe release ships on Friday. See [the plan](plan.md) and run `make check`; 3 steps.\n' > "$proj/docs/guide.md"
printf '# Notes\n\nThis note is load-bearing and stays out of the gate.\n' > "$proj/research/notes.md"
( cd "$proj" && git init -q && git add -A && git -c user.email=t@example.com -c user.name=t commit -q -m init )

out="$(cd "$proj" && bash "$CHECK")"; rc=$?
check "clean tree: exit 0" 0 "$rc"
check_out "clean tree: the gated doc passes" 'pass     docs/guide.md' "$out"
check_out "clean tree: the excluded doc is skipped, not blocked" 'skipped  research/notes.md' "$out"
check_out "clean tree: summary line" '1 passed, 1 skipped, 0 blocked' "$out"

printf '# Bad\n\nThis design is load-bearing for the release.\n' > "$proj/docs/bad.md"
out="$(cd "$proj" && bash "$CHECK")"; rc=$?
check "a banned phrase blocks: exit 1" 1 "$rc"
check_out "...and names the file" 'BLOCKED  docs/bad.md' "$out"
out="$(cd "$proj" && RESPEAK_GATE=off bash "$CHECK")"; rc=$?
check "session overrides are ignored by the check" 1 "$rc"
rm -f "$proj/docs/bad.md"

# --verify: a prose-only edit passes, a changed number fails
printf '# Guide\n\nThe release ships on Friday. See [the plan](plan.md), then run `make check`; 3 steps.\n' > "$proj/docs/guide.md"
out="$(cd "$proj" && bash "$CHECK" --verify HEAD)"; rc=$?
check "verify: prose-only edit exits 0" 0 "$rc"
check_out "verify: ...and is reported verified" 'verified docs/guide.md' "$out"
printf '# Guide\n\nThe release ships on Friday. See [the plan](plan.md) and run `make check`; 4 steps.\n' > "$proj/docs/guide.md"
out="$(cd "$proj" && bash "$CHECK" --verify HEAD)"; rc=$?
check "verify: a changed number exits 1" 1 "$rc"
check_out "verify: ...and names the file" 'CHANGED  docs/guide.md' "$out"
printf '# New\n\nA new page.\n' > "$proj/docs/new.md"; ( cd "$proj" && git add docs/new.md )
out="$(cd "$proj" && bash "$CHECK" --verify HEAD docs/new.md)"; rc=$?
check "verify: a file absent from the ref is gated but not verified" 0 "$rc"
( cd "$proj" && git checkout -q -- docs/guide.md )

out="$(cd "$proj" && bash "$CHECK" --verify no-such-ref 2>&1)"; rc=$?
check "usage: an unknown ref exits 2" 2 "$rc"
out="$(cd "$proj" && bash "$CHECK" --bogus 2>&1)"; rc=$?
check "usage: an unknown option exits 2" 2 "$rc"

# Dogfood: this repository's own tracked docs pass its own gate.
out="$(cd "$REPO_ROOT" && bash "$CHECK" --quiet)"; rc=$?
check "dogfood: the plugin's own docs pass its own gate" 0 "$rc"
check_out "dogfood: ...with nothing blocked" ' 0 blocked' "$out"

echo; echo "$pass passed, $fail failed"; [ "$fail" -eq 0 ]
