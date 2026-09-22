#!/bin/bash
# Tests for scripts/readme-fresh.sh: the four verdicts on a temporary tree.
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

echo "$pass passed, $fail failed"
[ "$fail" -eq 0 ]
