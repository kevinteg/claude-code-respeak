#!/bin/bash
# Tests for scripts/readme-fresh.sh: every verdict on a temporary tree.
# Bash 3.2 compatible.
#
# Run: bash tests/test_readme_fresh.sh
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
FRESH="$(cd "$HERE/.." && pwd)/scripts/readme-fresh.sh"
pass=0; fail=0
check() { if [ "$2" -eq "$3" ] && printf '%s' "$5" | grep -q -- "$4"; then pass=$((pass + 1)); echo "ok   - $1"; else fail=$((fail + 1)); echo "FAIL - $1 (expected exit $2 and '$4', got $3: $5)"; fi; }

work="$(mktemp -d)"; trap 'rm -rf "$work"' EXIT
echo "# readme" > "$work/README.md"

out="$(bash "$FRESH" --repo "$work" 2>&1)"
check "absent source is skipped (exit 0)" 0 "$?" "readme: skipped, absent design/readme/source.md" "$out"

mkdir -p "$work/design/readme"; echo "# readme" > "$work/design/readme/source.md"
out="$(bash "$FRESH" --repo "$work" 2>&1)"
check "source without a stamp is stale (exit 2)" 2 "$?" "readme: stale, run make readme" "$out"

bash "$FRESH" --repo "$work" --stamp >/dev/null 2>&1
out="$(bash "$FRESH" --repo "$work" 2>&1)"
check "stamped tree is fresh (exit 0)" 0 "$?" "readme: fresh" "$out"

echo "more" >> "$work/design/readme/source.md"
out="$(bash "$FRESH" --repo "$work" 2>&1)"
check "source edited after the stamp is stale (exit 2)" 2 "$?" "readme: stale" "$out"

bash "$FRESH" --repo "$work" --stamp >/dev/null 2>&1
echo "hand edit" >> "$work/README.md"
out="$(bash "$FRESH" --repo "$work" 2>&1)"
check "README edited after the stamp is stale (exit 2)" 2 "$?" "readme: stale" "$out"

# ADV6-3: a README edited by hand cannot be re-stamped fresh.
printf '# readme\n\nThe cache is warm.\n' > "$work/design/readme/source.md"
cp "$work/design/readme/source.md" "$work/README.md"
bash "$FRESH" --repo "$work" --stamp >/dev/null 2>&1
out="$(bash "$FRESH" --repo "$work" 2>&1)"
check "a verified render stamps fresh (exit 0)" 0 "$?" "readme: fresh" "$out"
printf '\nRun `make ship` for 3 targets.\n' >> "$work/README.md"
out="$(bash "$FRESH" --repo "$work" --stamp 2>&1)"
check "--stamp refuses a README the verifier rejects (exit 2)" 2 "$?" "not stamping" "$out"
( cd "$work" && shasum -a 256 design/readme/source.md README.md > design/readme/rendered.sha256 )
out="$(bash "$FRESH" --repo "$work" 2>&1)"
check "a hand-written stamp over an edited README is stale (exit 2)" 2 "$?" "not a prose-only render" "$out"

mv "$work/design/readme/source.md" "$work/source.bak"
out="$(bash "$FRESH" --repo "$work" 2>&1)"
check "a stamp without its source is stale, not skipped (exit 2)" 2 "$?" "readme: stale, a stamp without its source" "$out"
mv "$work/source.bak" "$work/design/readme/source.md"

{ echo "# readme"; echo; i=0; while [ $i -lt 400 ]; do echo "The cache is warm and the queue is short today, so the build runs."; i=$((i + 1)); done; } > "$work/design/readme/source.md"
cp "$work/design/readme/source.md" "$work/README.md"
out="$(bash "$FRESH" --repo "$work" 2>&1)"
check "a source over 24,576 bytes is its own verdict (exit 2)" 2 "$?" "over the 24576-byte ceiling" "$out"
out="$(bash "$FRESH" --repo "$work" --stamp 2>&1)"
check "...and --stamp refuses it (exit 2)" 2 "$?" "over the 24576-byte ceiling" "$out"

echo "$pass passed, $fail failed"
[ "$fail" -eq 0 ]
