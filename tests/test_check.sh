#!/bin/bash
# Tests for scripts/respeak-check.sh, the command-line and CI form of the
# gate plus meaning-invariance verification. Bash 3.2 compatible.
#
# Run: bash tests/test_check.sh
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$HERE/.." && pwd)"
CHECK="$REPO_ROOT/plugin/scripts/respeak-check.sh"
pass=0; fail=0
check() { if [ "$2" -eq "$3" ]; then pass=$((pass + 1)); echo "ok   - $1"; else fail=$((fail + 1)); echo "FAIL - $1 (expected exit $2, got $3)"; fi; }
check_out() { if printf '%s' "$3" | grep -q -- "$2"; then pass=$((pass + 1)); echo "ok   - $1"; else fail=$((fail + 1)); echo "FAIL - $1 (expected '$2' in: $3)"; fi; }

work="$(mktemp -d)"; work="$(cd "$work" && pwd -P)"
trap 'rm -rf "$work"' EXIT
export RESPEAK_CACHE_DIR="$work/cache"
export CLAUDE_CONFIG_DIR="$work/no-user-config"; mkdir -p "$CLAUDE_CONFIG_DIR"
export CLAUDE_PLUGIN_ROOT="$REPO_ROOT/plugin"
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

# editorial_pass.verify: the project says what the verifier may relax and
# which non-Markdown files it covers; the flags say the same for one run.
vproj="$work/vproj"; mkdir -p "$vproj/.claude/respeak" "$vproj/docs" "$vproj/gen" "$vproj/data"
cat > "$vproj/.claude/respeak/config.yaml" <<'YAML'
version: 3
gate: {enabled: true, include: ["**/*.md"], exclude: [], fail_on: error}
editorial_pass:
  restructure: apply
  verify:
    prose_keys: [pitch, blurb]
    allow_strings: true
    paths: ["gen/*.py", "data/*.yaml"]
YAML
card_v1='---\ntitle: Card\npitch: "Ten miles of trail — 2 hours out and back"\n---\n\n# Card\n\nA short walk to the point.\n'
printf -- "$card_v1" > "$vproj/docs/card.md"
printf 'LABEL = "Pick the next adventure — camp or trail"\nROWS = {"a": 1}\n' > "$vproj/gen/site.py"
printf 'plants:\n  - id: fern\n    blurb: "Shade lover — needs 2 waterings a week"\n' > "$vproj/data/plants.yaml"
( cd "$vproj" && git init -q && git add -A && git -c user.email=t@example.com -c user.name=t commit -q -m init )

printf -- '---\ntitle: Card\npitch: "Ten miles of trail: 2 hours out and back"\n---\n\n# Card\n\nA short walk to the point.\n' > "$vproj/docs/card.md"
printf 'LABEL = "Pick the next adventure: camp or trail"\nROWS = {"a": 1}\n' > "$vproj/gen/site.py"
printf 'plants:\n  - id: fern\n    blurb: "Shade lover. Needs 2 waterings a week"\n' > "$vproj/data/plants.yaml"
out="$(cd "$vproj" && bash "$CHECK" --verify HEAD)"; rc=$?
check "verify.prose_keys: a reworded front-matter pitch is verified (exit 0)" 0 "$rc"
check_out "...and the Markdown file is reported verified" 'verified docs/card.md' "$out"
check_out "verify.paths + allow_strings: the generator's string edit is verified" 'verified gen/site.py' "$out"
check_out "verify.paths + prose_keys: the data file's blurb is verified" 'verified data/plants.yaml' "$out"
check_out "...and the summary counts all three" '3 verified, 0 changed' "$out"

printf 'LABEL = "Pick the next adventure: camp or trail"\nROWS = {"a": 1, "b": 2}\n' > "$vproj/gen/site.py"
out="$(cd "$vproj" && bash "$CHECK" --verify HEAD)"; rc=$?
check "allow_strings: a new dict entry in the generator still fails (exit 1)" 1 "$rc"
check_out "...and names the generator" 'CHANGED  gen/site.py' "$out"
( cd "$vproj" && git checkout -q -- gen/site.py )

printf -- '---\ntitle: Card\npitch: "Ten miles of trail: 3 hours out and back"\n---\n\n# Card\n\nA short walk to the point.\n' > "$vproj/docs/card.md"
out="$(cd "$vproj" && bash "$CHECK" --verify HEAD)"; rc=$?
check "prose_keys: a changed number inside the pitch still fails (exit 1)" 1 "$rc"
check_out "...and names the page" 'CHANGED  docs/card.md' "$out"

printf -- '---\ntitle: Card\npitch: "Ten miles of trail — 2 hours out and back"\n---\n\n# The card\n\nA short walk to the point.\n' > "$vproj/docs/card.md"
out="$(cd "$vproj" && bash "$CHECK" --verify HEAD docs/card.md)"; rc=$?
check "restructure: apply: a retitled heading is verified with a warning (exit 0)" 0 "$rc"
check_out "...and the run says which flag it passed" 'allow-restructure' "$out"
out="$(cd "$vproj" && bash "$CHECK" --verify HEAD)"; rc=$?
check_out "a named FILE skips verify.paths; the full run still covers them" 'verified data/plants.yaml' "$out"

# Without any verify configuration the strict verdict stands, and the flags
# open the same doors for one run.
( cd "$proj" && git checkout -q -- docs/guide.md )
printf -- '---\npitch: "Ten miles of trail — 2 hours"\n---\n\n# Card\n\nA short walk.\n' > "$proj/docs/card.md"
( cd "$proj" && git add docs/card.md && git -c user.email=t@example.com -c user.name=t commit -q -m card )
printf -- '---\npitch: "Ten miles of trail: 2 hours"\n---\n\n# Card\n\nA short walk.\n' > "$proj/docs/card.md"
out="$(cd "$proj" && bash "$CHECK" --verify HEAD docs/card.md)"; rc=$?
check "no verify config: a front-matter edit is CHANGED (exit 1)" 1 "$rc"
out="$(cd "$proj" && bash "$CHECK" --verify HEAD --prose-keys pitch docs/card.md)"; rc=$?
check "--prose-keys on the command line verifies it for this run (exit 0)" 0 "$rc"
out="$(cd "$proj" && bash "$CHECK" --prose-keys 2>&1)"; rc=$?
check "usage: --prose-keys without a list exits 2" 2 "$rc"

# Dogfood: this repository's own tracked docs pass its own gate. Tracked files
# are named explicitly so a developer's local untracked notes cannot fail the suite.
tracked=(); while IFS= read -r f; do [ -n "$f" ] && tracked+=("$f"); done < <(cd "$REPO_ROOT" && git ls-files -- '*.md')
out="$(cd "$REPO_ROOT" && bash "$CHECK" --quiet "${tracked[@]}")"; rc=$?
check "dogfood: the plugin's own docs pass its own gate" 0 "$rc"
check_out "dogfood: ...with nothing blocked" ' 0 blocked' "$out"

echo; echo "$pass passed, $fail failed"; [ "$fail" -eq 0 ]
