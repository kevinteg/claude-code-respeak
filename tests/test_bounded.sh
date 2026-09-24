#!/bin/bash
# Tests for scripts/bounded (the runner `make check` goes through): the wall, the lock, the load
# breaker, the exit, and ADV10-2, 4 and 5. Bash 3.2 compatible.
#
# Run: bash tests/test_bounded.sh   (BOUNDED=<path> runs the suite against another copy)
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
BOUNDED="${BOUNDED:-$(cd "$HERE/.." && pwd)/scripts/bounded}"
pass=0; fail=0
check() { if [ "$2" = "$3" ]; then pass=$((pass + 1)); echo "ok   - $1"; else fail=$((fail + 1)); echo "FAIL - $1 (expected $2, got $3)"; fi; }

last() { tail -1 "$1" 2>/dev/null; }

work="$(mktemp -d)"; trap 'pkill -f "sleep 353" 2>/dev/null; rm -rf "$work"' EXIT

# The wall: the whole group dies, the runner exits 124 well inside the command's own 30 s.
t0=$(date +%s)
BOUNDED_GRACE=1 python3 "$BOUNDED" --wall 1 -- sh -c 'echo $$ > "$1"; exec sleep 30' sh "$work/pid" 2>"$work/wall.err"
rc=$?; elapsed=$(( $(date +%s) - t0 ))
check "the wall exits 124" 124 "$rc"
check "...in under 5 s" yes "$([ "$elapsed" -lt 5 ] && echo yes || echo "no ($elapsed s)")"
check "...with no survivor" dead "$(kill -0 "$(cat "$work/pid")" 2>/dev/null && echo alive || echo dead)"
check "...and its last stderr line is the wall stop (ADV10-4)" "bounded: stop: wall" "$(last "$work/wall.err")"

# The lock: a live holder (this shell) refuses the second runner with 2, and the command never runs.
mkdir "$work/lock"; echo "$$ $(date +%s)" > "$work/lock/owner"
python3 "$BOUNDED" --lock "$work/lock" -- touch "$work/ran" 2>"$work/lock.err"
check "a lock held by a live pid refuses with 2" 2 "$?"
check "...and the command does not run" absent "$([ -e "$work/ran" ] && echo present || echo absent)"
check "...and its last stderr line is the lock stop (ADV10-4)" "bounded: stop: lock" "$(last "$work/lock.err")"
rm -rf "$work/lock"

# The command's own exit passes through, and the lock (a flock file kept after the run) is free again.
python3 "$BOUNDED" --lock "$work/lock" -- sh -c 'exit 7'
check "the command's own exit passes through" 7 "$?"
python3 "$BOUNDED" --lock "$work/lock" -- true
check "a second run after the first takes the lock and runs" 0 "$?"

# ADV10-4: a load refusal exits 2 before the command runs, and says so on its last stderr line.
BOUNDED_LOADAVG=1000 BOUNDED_LOAD_MAX=1 BOUNDED_LOAD_POLL=1 \
  python3 "$BOUNDED" --load 4 -- touch "$work/loaded" 2>"$work/load.err"
check "a load refusal exits 2" 2 "$?"
check "...its last stderr line is the load stop" "bounded: stop: load" "$(last "$work/load.err")"
check "...and the command does not run" absent "$([ -e "$work/loaded" ] && echo present || echo absent)"

# ADV10-5: two runners started together on one lock file; exactly one runs, the other exits 2.
mkdir "$work/race"
python3 "$BOUNDED" --lock "$work/race.lock" -- sh -c 'touch "$1/$$"; sleep 1' sh "$work/race" 2>"$work/race1.err" &
r1=$!
python3 "$BOUNDED" --lock "$work/race.lock" -- sh -c 'touch "$1/$$"; sleep 1' sh "$work/race" 2>"$work/race2.err" &
r2=$!
wait "$r1"; rc1=$?; wait "$r2"; rc2=$?
check "two runners on one lock: exactly one marker (ADV10-5)" 1 "$(ls "$work/race" | wc -l | tr -d ' ')"
check "...and one runner exits 2" 1 "$( { [ "$rc1" = 2 ] && echo x; [ "$rc2" = 2 ] && echo x; } | wc -l | tr -d ' ')"

# ADV10-5: a leftover mkdir-era lock directory whose owner pid is dead is removed, and the run goes ahead.
sh -c 'exit 0' & dead=$!; wait "$dead"
mkdir "$work/old.lock"; echo "$dead $(date +%s)" > "$work/old.lock/owner"
python3 "$BOUNDED" --lock "$work/old.lock" -- true 2>/dev/null
check "a lock directory with a dead owner is removed and the run goes ahead (ADV10-5)" 0 "$?"

# ADV10-5: a live holder is never taken over, at any age (the old copy took a lock older than 900 s).
mkdir "$work/aged.lock"; echo "$$ $(( $(date +%s) - 1000 ))" > "$work/aged.lock/owner"
python3 "$BOUNDED" --lock "$work/aged.lock" -- touch "$work/aged" 2>/dev/null
check "a live holder 1000 s old still refuses with 2 (ADV10-5)" 2 "$?"
check "...and the command does not run" absent "$([ -e "$work/aged" ] && echo present || echo absent)"

# ADV10-2: bounded's whole group SIGKILLed at 1 s leaves no survivor of the command 3 s later.
BOUNDED_GRACE=1 python3 -c '
import os, signal, subprocess, sys, time
p = subprocess.Popen([sys.executable, sys.argv[1], "--wall", "20", "--", "sleep", "353"],
                     preexec_fn=os.setsid, stderr=subprocess.DEVNULL)
time.sleep(1)
os.killpg(p.pid, signal.SIGKILL)
p.wait()
' "$BOUNDED"
sleep 3
check "a SIGKILLed group leaves no sleep 353 behind (ADV10-2)" 0 "$(pgrep -f 'sleep 353' | wc -l | tr -d ' ')"

echo "$pass passed, $fail failed"
[ "$fail" -eq 0 ]
