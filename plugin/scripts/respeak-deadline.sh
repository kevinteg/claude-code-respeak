#!/bin/bash
# Run one command under a wall clock, in its own process group.
#
#   respeak-deadline.sh SECONDS CMD [ARGS...]
#
# CMD runs as the leader of a new process group (bash job control), with
# stdin, stdout and stderr passed through. When SECONDS pass first, the
# whole group gets TERM, then KILL after RESPEAK_DEADLINE_GRACE seconds
# (default 2) if anything in it is still alive, and this script exits 124
# with one stderr line:
#   respeak-deadline: CMD killed after SECONDS s
# Otherwise it exits with CMD's status. TERM, INT or HUP sent to this script
# are passed to the group, so killing the caller leaves no orphan runner.
# A group that is not the terminal's foreground stops if it reads the tty,
# so give CMD a file or /dev/null on stdin when the caller has a terminal.
#
# The watchdog runs in a process group of its own too, so a kill of the
# caller's whole group (a SIGKILL to it, which no trap sees) does not reach
# it: it ticks once a second, and when this script is gone or SECONDS have
# passed it stops CMD's group the same way (review ADV10-2). When CMD ends
# first, this script kills the watchdog's group, its one-second sleep
# included, so no timer outlives a run (ADV10-7). The grace stays under
# scripts/bounded's 5 s, so an inner kill finishes before an outer one.
#
# The kill is a group kill because CMD's children (a `claude -p` runner, a
# python under a shim) are what outlive a plain `kill` of CMD. A stock Mac
# has no `timeout`, so this is bash. bash 3.2 compatible.
set -u

usage() { echo "usage: respeak-deadline.sh SECONDS CMD [ARGS...]" >&2; exit 2; }
[ $# -ge 2 ] || usage
secs="$1"; shift
case "$secs" in ''|*[!0-9]*) usage ;; esac
[ "$secs" -ge 1 ] || usage

grace="${RESPEAK_DEADLINE_GRACE:-2}"
case "$grace" in ''|*[!0-9]*) grace=2 ;; esac

mark="$(mktemp 2>/dev/null)" || { echo "respeak-deadline: mktemp failed" >&2; exit 2; }
rm -f "$mark"          # the watchdog recreates it when it fires
self=$$

group_alive() { kill -0 -- "-$pid" 2>/dev/null; }
stop_group() {
  kill -TERM -- "-$pid" 2>/dev/null
  i=0
  while [ "$i" -lt "$grace" ] && group_alive; do sleep 1; i=$((i + 1)); done
  group_alive && kill -KILL -- "-$pid" 2>/dev/null
  return 0
}

# Job control puts each background job in its own process group, with the
# job's pid as the group id: CMD's group, then the watchdog's. It stays on
# only for these two spawns.
set -m
"$@" &
pid=$!
( ticks=0
  while [ "$ticks" -lt "$secs" ]; do
    sleep 1
    ticks=$((ticks + 1))
    kill -0 "$self" 2>/dev/null || break      # this script is gone: stop CMD anyway
  done
  kill -0 "$self" 2>/dev/null && : > "$mark"
  stop_group ) </dev/null >/dev/null 2>&1 &
watcher=$!
set +m

stop_watcher() { kill -TERM -- "-$watcher" 2>/dev/null; wait "$watcher" 2>/dev/null; }

trap 'stop_watcher; stop_group; rm -f "$mark"; exit 143' TERM INT HUP

wait "$pid" 2>/dev/null               # bash's own "Killed: 9" job notice, not CMD's stderr
status=$?
if [ -e "$mark" ]; then
  wait "$watcher" 2>/dev/null        # let TERM, then KILL, finish on the group
  rm -f "$mark"
  echo "respeak-deadline: $1 killed after $secs s" >&2
  exit 124
fi
stop_watcher
# CMD exited on its own; anything it left in its group goes with it.
group_alive && stop_group
exit "$status"
