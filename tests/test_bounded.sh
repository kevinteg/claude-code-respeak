#!/bin/bash
# Tests for scripts/bounded (the runner `make check` goes through): the wall, the lock, the exit.
# Bash 3.2 compatible.
#
# Run: bash tests/test_bounded.sh
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
BOUNDED="$(cd "$HERE/.." && pwd)/scripts/bounded"
pass=0; fail=0
check() { if [ "$2" = "$3" ]; then pass=$((pass + 1)); echo "ok   - $1"; else fail=$((fail + 1)); echo "FAIL - $1 (expected $2, got $3)"; fi; }

work="$(mktemp -d)"; trap 'rm -rf "$work"' EXIT

# The wall: the whole group dies, the runner exits 124 well inside the command's own 30 s.
t0=$(date +%s)
BOUNDED_GRACE=1 python3 "$BOUNDED" --wall 1 -- sh -c 'echo $$ > "$1"; exec sleep 30' sh "$work/pid" 2>/dev/null
rc=$?; elapsed=$(( $(date +%s) - t0 ))
check "the wall exits 124" 124 "$rc"
check "...in under 5 s" yes "$([ "$elapsed" -lt 5 ] && echo yes || echo "no ($elapsed s)")"
check "...with no survivor" dead "$(kill -0 "$(cat "$work/pid")" 2>/dev/null && echo alive || echo dead)"

# The lock: a live holder (this shell) refuses the second runner with 2, and the command never runs.
mkdir "$work/lock"; echo "$$ $(date +%s)" > "$work/lock/owner"
python3 "$BOUNDED" --lock "$work/lock" -- touch "$work/ran" 2>/dev/null
check "a lock held by a live pid refuses with 2" 2 "$?"
check "...and the command does not run" absent "$([ -e "$work/ran" ] && echo present || echo absent)"
rm -rf "$work/lock"

# The command's own exit passes through, and the lock (a flock file kept after the run) is free again.
python3 "$BOUNDED" --lock "$work/lock" -- sh -c 'exit 7'
check "the command's own exit passes through" 7 "$?"
python3 "$BOUNDED" --lock "$work/lock" -- true
check "a second run after the first takes the lock and runs" 0 "$?"

echo "$pass passed, $fail failed"
[ "$fail" -eq 0 ]
