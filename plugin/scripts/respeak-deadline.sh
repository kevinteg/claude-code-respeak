#!/bin/bash
# Run one command under a wall clock, in its own process group.
#
#   respeak-deadline.sh SECONDS CMD [ARGS...]
#
# CMD runs as the leader of a new process group (bash job control), with
# stdin, stdout and stderr passed through. When SECONDS pass first, the
# whole group gets TERM, then KILL after 5 s if anything in it is still
# alive, and this script exits 124 with one stderr line:
#   respeak-deadline: CMD killed after SECONDS s
# Otherwise it exits with CMD's status. TERM, INT or HUP sent to this script
# are passed to the group, so killing the caller leaves no orphan runner.
# A group that is not the terminal's foreground stops if it reads the tty,
# so give CMD a file or /dev/null on stdin when the caller has a terminal.
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

mark="$(mktemp 2>/dev/null)" || { echo "respeak-deadline: mktemp failed" >&2; exit 2; }
rm -f "$mark"          # the watcher recreates it when it fires

# Job control puts the background job in its own process group, with the
# job's pid as the group id. It stays on only for this one spawn.
set -m
"$@" &
pid=$!
set +m

group_alive() { kill -0 -- "-$pid" 2>/dev/null; }
stop_group() {
  kill -TERM -- "-$pid" 2>/dev/null
  i=0
  while [ "$i" -lt 5 ] && group_alive; do sleep 1; i=$((i + 1)); done
  group_alive && kill -KILL -- "-$pid" 2>/dev/null
  return 0
}

( sleep "$secs"
  : > "$mark"
  stop_group ) >/dev/null 2>&1 &
watcher=$!

trap 'kill "$watcher" 2>/dev/null; stop_group; rm -f "$mark"; exit 143' TERM INT HUP

wait "$pid" 2>/dev/null               # bash's own "Killed: 9" job notice, not CMD's stderr
status=$?
if [ -e "$mark" ]; then
  wait "$watcher" 2>/dev/null        # let TERM, then KILL, finish on the group
  rm -f "$mark"
  echo "respeak-deadline: $1 killed after $secs s" >&2
  exit 124
fi
kill "$watcher" 2>/dev/null
wait "$watcher" 2>/dev/null
# CMD exited on its own; anything it left in its group goes with it.
group_alive && stop_group
exit "$status"
