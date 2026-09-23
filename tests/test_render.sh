#!/bin/bash
# Tests for the bounded spawns: plugin/scripts/respeak-deadline.sh, the
# renderer's breakers (plugin/scripts/respeak-render.sh), and
# scripts/readme-render.sh. A fake `claude` (and, for the load breaker, a
# fake `sysctl`) sits first on PATH; nothing here starts a real runner or
# touches the real checkout. Bash 3.2 compatible.
#
# Run: bash tests/test_render.sh
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$HERE/.." && pwd)"
DEADLINE="$REPO_ROOT/plugin/scripts/respeak-deadline.sh"
RENDER="$REPO_ROOT/plugin/scripts/respeak-render.sh"
README_RENDER="$REPO_ROOT/scripts/readme-render.sh"
pass=0; fail=0
ok() { pass=$((pass + 1)); echo "ok   - $1"; }
bad() { fail=$((fail + 1)); echo "FAIL - $1"; }
check() { if [ "$2" -eq "$3" ]; then ok "$1"; else bad "$1 (expected exit $2, got $3)"; fi; }
check_out() { if printf '%s' "$3" | grep -q -- "$2"; then ok "$1"; else bad "$1 (expected '$2' in: $3)"; fi; }
no_runner() { if [ ! -s "$FAKE_LOG" ]; then ok "$1"; else bad "$1 (the runner ran: $(cat "$FAKE_LOG"))"; fi; }
survivors() { pgrep -f "$1" >/dev/null 2>&1 && echo yes || echo no; }

work="$(mktemp -d)"; work="$(cd "$work" && pwd -P)"
trap 'pkill -f "sleep 4[67].25" 2>/dev/null; rm -rf "$work"' EXIT
export RESPEAK_CACHE_DIR="$work/cache"
export CLAUDE_CONFIG_DIR="$work/no-user-config"; mkdir -p "$CLAUDE_CONFIG_DIR"
export CLAUDE_PLUGIN_ROOT="$REPO_ROOT/plugin"
unset RESPEAK_RENDER_DEPTH RESPEAK_RENDER_CMD RESPEAK_RENDER_WALL RESPEAK_RENDER_MAX_TURNS RESPEAK_CONFIG \
  CLAUDE_PROJECT_DIR CLAUDE_CODE_SESSION_ID XDG_STATE_HOME 2>/dev/null || true
export RESPEAK_LOAD_MAX=100000        # only the load test below looks at the real breaker
export FAKE_LOG="$work/runner.log"

# The fake runner: logs its flags and depth, then answers by FAKE_MODE.
mkdir -p "$work/bin" "$work/loadbin"
cat > "$work/bin/claude" <<'SH'
#!/bin/bash
{ echo "args: $*"; echo "depth: ${RESPEAK_RENDER_DEPTH:-}"; } >> "$FAKE_LOG"
prompt="$(cat)"
case "${FAKE_MODE:-echo}" in
  sleep) sleep 46.25 ;;
  banned) printf '%s\n' '{"result": "# Fixture\n\nThis design is load-bearing for the release.\n"}' ;;
  *) printf '%s\n' "$prompt" | python3 -c '
import json, sys
t = sys.stdin.read()
i = t.index("--- source material")
print(json.dumps({"result": t[t.index("\n", i) + 1:]}))' ;;
esac
SH
cat > "$work/loadbin/sysctl" <<'SH'
#!/bin/sh
case "$2" in vm.loadavg) echo "{ 999.00 999.00 999.00 }" ;; hw.ncpu) echo 16 ;; esac
SH
chmod +x "$work/bin/claude" "$work/loadbin/sysctl"
export PATH="$work/bin:$PATH"

# A fixture repository with a README source and the real contract.
fx="$work/fx"; mkdir -p "$fx/design/readme"
printf '# Fixture\n\nThe cache is warm, and the build runs in 3 steps.\n' > "$fx/design/readme/source.md"
cp "$REPO_ROOT/design/readme/contract.txt" "$fx/design/readme/contract.txt"
printf '# Fixture\n\nThe old text.\n' > "$fx/README.md"
src="$fx/design/readme/source.md"; out="$work/out.md"

# --- the helper alone ------------------------------------------------------
start=$(date +%s)
bash "$DEADLINE" 1 sleep 47.25 2>"$work/dl.err"; rc=$?
took=$(( $(date +%s) - start ))
check "deadline: sleep past 1 s exits 124" 124 "$rc"
if [ "$took" -lt 7 ] && [ "$(survivors 'sleep 47.25')" = no ]; then ok "...inside 7 s, with no survivor"
else bad "...inside 7 s, with no survivor (took $took s, survivor $(survivors 'sleep 47.25'))"; fi
check_out "...and says so" 'respeak-deadline: sleep killed after 1 s' "$(cat "$work/dl.err")"
got="$(echo hi | bash "$DEADLINE" 5 cat)"; rc=$?
if [ "$rc" -eq 0 ] && [ "$got" = hi ]; then ok "deadline: stdin and stdout pass through"; else bad "deadline: stdin and stdout pass through (rc $rc, '$got')"; fi
bash "$DEADLINE" 5 sh -c 'exit 7'; check "deadline: the command's own exit passes through" 7 "$?"

# --- the renderer's breakers: exit 2, no runner started ----------------------
: > "$FAKE_LOG"
err="$(RESPEAK_RENDER_DEPTH=1 bash "$RENDER" --mode technical --source "$src" --out "$out" 2>&1)"; rc=$?
check "render: RESPEAK_RENDER_DEPTH set refuses (exit 2)" 2 "$rc"
check_out "...naming the cause" 'RESPEAK_RENDER_DEPTH' "$err"
no_runner "...before any runner starts"
err="$(env -u RESPEAK_LOAD_MAX PATH="$work/loadbin:$PATH" bash "$RENDER" --mode technical --source "$src" --out "$out" 2>&1)"; rc=$?
check "render: a load of 999 over 4 x 16 cores refuses (exit 2)" 2 "$rc"
check_out "...naming the load" 'load 999.00 is over RESPEAK_LOAD_MAX=64' "$err"
no_runner "...before any runner starts"
for bad_rounds in x 0 9; do
  bash "$RENDER" --mode technical --source "$src" --out "$out" --max-rounds "$bad_rounds" 2>/dev/null
  check "render: --max-rounds $bad_rounds refuses (exit 2)" 2 "$?"
done
no_runner "...before any runner starts"

# --- ADV6-5: a runner that hangs dies with its group at the wall clock ------
: > "$FAKE_LOG"
start=$(date +%s)
FAKE_MODE=sleep RESPEAK_RENDER_WALL=1 bash "$RENDER" --mode technical --source "$src" --out "$out" 2>"$work/wall.err"; rc=$?
took=$(( $(date +%s) - start ))
check "render: a hung runner exits 2 at the wall clock" 2 "$rc"
if [ "$took" -lt 8 ] && [ "$(survivors 'sleep 46.25')" = no ]; then ok "...inside 8 s, with no survivor in its group"
else bad "...inside 8 s, with no survivor in its group (took $took s, survivor $(survivors 'sleep 46.25'))"; fi
check_out "...naming the wall clock" 'RESPEAK_RENDER_WALL' "$(cat "$work/wall.err")"
FAKE_MODE=sleep RESPEAK_RENDER_WALL=60 bash "$RENDER" --mode technical --source "$src" --out "$out" 2>/dev/null &
rpid=$!
i=0; while [ "$i" -lt 50 ] && [ "$(survivors 'sleep 46.25')" = no ]; do sleep 0.1; i=$((i + 1)); done
kill -TERM "$rpid"; wait "$rpid" 2>/dev/null
i=0; while [ "$i" -lt 70 ] && [ "$(survivors 'sleep 46.25')" = yes ]; do sleep 0.1; i=$((i + 1)); done
if [ "$(survivors 'sleep 46.25')" = no ]; then ok "render: a TERM to the renderer leaves no orphan runner"
else bad "render: a TERM to the renderer leaves no orphan runner"; fi
check_out "render: the runner gets --tools and --max-turns" '--tools Read Grep Glob --allowedTools Read Grep Glob --max-turns 8' "$(cat "$FAKE_LOG")"
check_out "render: the runner sees RESPEAK_RENDER_DEPTH" 'depth: 1' "$(cat "$FAKE_LOG")"

# --- ADV6-6: readme-render.sh writes and stamps only a verified render ------
cp "$fx/README.md" "$work/README.before"
FAKE_MODE=banned bash "$README_RENDER" --repo "$fx" >/dev/null 2>&1; rc=$?
check "readme-render: a render that fails the gate exits 1" 1 "$rc"
if cmp -s "$fx/README.md" "$work/README.before" && [ ! -f "$fx/design/readme/rendered.sha256" ]; then
  ok "...and leaves README.md byte-identical, unstamped"
else bad "...and leaves README.md byte-identical, unstamped"; fi
bash "$README_RENDER" --repo "$fx" >/dev/null 2>&1; rc=$?
check "readme-render: a verified render writes and stamps (exit 0)" 0 "$rc"
if cmp -s "$fx/README.md" "$src" && bash "$REPO_ROOT/scripts/readme-fresh.sh" --repo "$fx" >/dev/null; then
  ok "...and readme-fresh reads it fresh"
else bad "...and readme-fresh reads it fresh"; fi
if ls -d "$fx"/.readme-render.* >/dev/null 2>&1; then bad "readme-render: no temp directory is left behind"
else ok "readme-render: no temp directory is left behind"; fi

echo; echo "$pass passed, $fail failed"; [ "$fail" -eq 0 ]
