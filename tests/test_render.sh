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
# gone MARKER: waits up to 5 s for every process matching MARKER to exit.
gone() { i=0; while [ "$i" -lt 50 ] && [ "$(survivors "$1")" = yes ]; do sleep 0.1; i=$((i + 1)); done
  [ "$(survivors "$1")" = no ]; }
# killpg_after CMD [ARGS...]: CMD starts as the leader of a new session (the
# way a caller's `bounded` or a relay starts it), and its whole group is
# SIGKILLed 2 s later: nothing gets a chance to clean up.
killpg_after() {
  python3 - "$@" <<'PY'
import os, signal, sys, time
pid = os.fork()
if pid == 0:
    os.setsid()
    fd = os.open(os.devnull, os.O_RDWR)
    for i in (0, 1, 2):
        os.dup2(fd, i)
    os.execvp(sys.argv[1], sys.argv[1:])
time.sleep(2)
os.killpg(pid, signal.SIGKILL)
os.waitpid(pid, 0)
PY
}

work="$(mktemp -d)"; work="$(cd "$work" && pwd -P)"
trap 'pkill -f "sleep 4[4-7].25" 2>/dev/null; pkill -f "sleep 43\$" 2>/dev/null; rm -rf "$work"' EXIT
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
  sleep) sleep "${FAKE_SLEEP:-46.25}" ;;
  banned) printf '%s\n' '{"result": "# Fixture\n\nThis design is load-bearing for the release.\n"}' ;;
  limit) printf '%s\n' '{"type": "result", "subtype": "success", "is_error": true, "result": "Claude AI usage limit reached|1790000000\nsecond line"}' ;;
  iserr) printf '%s\n' '{"type": "result", "subtype": "success", "is_error": true, "result": "# Fixture\n\nSomething broke.\n"}' ;;
  maxturns) printf '%s\n' '{"type": "result", "subtype": "error_max_turns", "is_error": false, "result": "# Fixture\n\nPartial.\n"}' ;;
  result) python3 -c 'import json, os; print(json.dumps({"type": "result", "subtype": "success", "is_error": True, "result": os.environ["FAKE_RESULT"]}))' ;;
  text) printf '%s\n' "$FAKE_TEXT"; exit 1 ;;
  login) echo "Invalid API key · Please run /login" >&2; exit 1 ;;
  crash) echo "segfault in the runner" >&2; exit 1 ;;
  nonl) printf '%s\n' '{"result": "# Fixture\n\nThe cache is warm."}' ;;
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

# A fixture repository with a README source, its status line, a manifest,
# and the real contract.
fx="$work/fx"; mkdir -p "$fx/design/readme" "$fx/plugin/.claude-plugin"
printf '# Fixture\n\nThe cache is warm, and the build runs in 3 steps.\n\n## Status\n\nStatus: version `0.0.0`, rendered `2000-01-01`, `0` unittest cases and `0` bash suites.\n' > "$fx/design/readme/source.md"
printf '{"name": "fixture", "version": "9.8.7"}\n' > "$fx/plugin/.claude-plugin/plugin.json"
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

# --- ADV10-2: a SIGKILL to the caller's group still stops CMD's group -------
killpg_after bash "$DEADLINE" 30 sleep 45.25
if gone 'sleep 45.25'; then ok "deadline: a killpg of the caller's group leaves no survivor"
else bad "deadline: a killpg of the caller's group leaves no survivor (sleep 45.25 is alive)"; fi
: > "$FAKE_LOG"
FAKE_MODE=sleep FAKE_SLEEP=44.25 RESPEAK_RENDER_WALL=60 killpg_after bash "$RENDER" --mode technical --source "$src" --out "$out"
if gone 'sleep 44.25'; then ok "render: a killpg of the caller's group leaves no runner"
else bad "render: a killpg of the caller's group leaves no runner (sleep 44.25 is alive)"; fi
# ADV10-7: the watchdog's timer does not outlive a run that ends first.
for n in 1 2 3; do bash "$DEADLINE" 43 true; done
if gone 'sleep 43$'; then ok "deadline: three quick runs leave no sleep 43 behind"
else bad "deadline: three quick runs leave no sleep 43 behind"; fi

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

# --- ADV10-3: an account failure is exit 4, and nothing reaches --out -------
rm -f "$out"
err="$(FAKE_MODE=limit bash "$RENDER" --mode technical --source "$src" --out "$out" 2>&1 >/dev/null)"; rc=$?
check "render: is_error with a usage-limit result exits 4" 4 "$rc"
check_out "...with the account-failure line" 'respeak-render: account failure: Claude AI usage limit reached|1790000000$' "$err"
if [ ! -e "$out" ]; then ok "...and writes no --out"; else bad "...and writes no --out"; fi
rm -f "$out"; err="$(FAKE_MODE=iserr bash "$RENDER" --mode technical --source "$src" --out "$out" 2>&1 >/dev/null)"; rc=$?
check "render: is_error with any other result exits 2" 2 "$rc"
if [ ! -e "$out" ]; then ok "...and writes no --out"; else bad "...and writes no --out"; fi
rm -f "$out"; FAKE_MODE=maxturns bash "$RENDER" --mode technical --source "$src" --out "$out" >/dev/null 2>&1; rc=$?
check "render: a subtype other than success exits 2" 2 "$rc"
if [ ! -e "$out" ]; then ok "...and writes no --out"; else bad "...and writes no --out"; fi
err="$(FAKE_MODE=login bash "$RENDER" --mode technical --source "$src" --out "$out" 2>&1 >/dev/null)"; rc=$?
check "render: a runner exiting 1 with /login on stderr exits 4" 4 "$rc"
check_out "...with the account-failure line" 'respeak-render: account failure: Invalid API key' "$err"
FAKE_MODE=crash bash "$RENDER" --mode technical --source "$src" --out "$out" >/dev/null 2>&1; rc=$?
check "render: any other runner error stays exit 2" 2 "$rc"
# ADV11-5: every measured phrasing is an account failure, and so is one
# printed as plain text outside JSON; the guard against the pattern drifting.
for phrase in '5-hour limit reached ∙ resets 3pm' 'Weekly limit reached ∙ resets Mon 9am' 'API Error: 429 rate_limit_error'; do
  rm -f "$out"; FAKE_MODE=result FAKE_RESULT="$phrase" bash "$RENDER" --mode technical --source "$src" --out "$out" >/dev/null 2>&1; rc=$?
  check "render: is_error result '$phrase' exits 4" 4 "$rc"
done
err="$(FAKE_MODE=text FAKE_TEXT='Claude AI usage limit reached|1790000000' bash "$RENDER" --mode technical --source "$src" --out "$out" 2>&1 >/dev/null)"; rc=$?
check "render: a plain-text usage limit on stdout with exit 1 exits 4" 4 "$rc"
check_out "...with that line" 'respeak-render: account failure: Claude AI usage limit reached|1790000000$' "$err"
FAKE_MODE=text FAKE_TEXT=boom bash "$RENDER" --mode technical --source "$src" --out "$out" >/dev/null 2>&1; rc=$?
check "render: a plain-text boom with exit 1 stays exit 2" 2 "$rc"
cp "$fx/README.md" "$work/README.before"
FAKE_MODE=login bash "$README_RENDER" --repo "$fx" >/dev/null 2>&1; rc=$?
check "readme-render: an account failure passes through as exit 4" 4 "$rc"
if cmp -s "$fx/README.md" "$work/README.before"; then ok "...and leaves README.md untouched"
else bad "...and leaves README.md untouched"; fi

# --- ADV10-6: a failed render leaves the source byte-identical --------------
sed 's/^Status: version .*/Status: version `0.0.0`, rendered `2000-01-01`, `0` unittest cases and `0` bash suites./' "$src" > "$work/source.before"
cp "$work/source.before" "$src"
(cd "$fx" && git init -q && git add -A && git -c user.name=t -c user.email=t@t commit -qm fixture)
FAKE_MODE=crash bash "$README_RENDER" --repo "$fx" >/dev/null 2>&1; rc=$?
check "readme-render: a runner exiting 1 exits 2" 2 "$rc"
if cmp -s "$src" "$work/source.before" && [ -z "$(git -C "$fx" status --short)" ]; then
  ok "...and leaves the source byte-identical, git status empty"
else bad "...and leaves the source byte-identical, git status empty ($(git -C "$fx" status --short | tr '\n' ' '))"; fi
rm -rf "$fx/.git"

# --- ruling 10: the renderer keeps the source's final newline ---------------
rm -f "$out"
FAKE_MODE=nonl bash "$RENDER" --mode technical --source "$src" --out "$out" >/dev/null 2>&1; rc=$?
check "render: a result without a final newline, from a source with one (exit 0)" 0 "$rc"
if [ "$(tail -c 1 "$out" | od -An -c | tr -d ' ')" = '\n' ] && [ "$(tail -c 2 "$out" | od -An -c | tr -d ' ')" != '\n\n' ]; then
  ok "...writes an output ending in exactly one newline"
else bad "...writes an output ending in exactly one newline"; fi
printf '%s' "$(cat "$src")" > "$work/nonl-src.md"
bash "$RENDER" --mode technical --source "$work/nonl-src.md" --out "$out" >/dev/null 2>&1; rc=$?
if [ "$rc" -eq 0 ] && [ "$(tail -c 1 "$out" | od -An -c | tr -d ' ')" != '\n' ]; then
  ok "render: a source without a final newline gives an output without one"
else bad "render: a source without a final newline gives an output without one (rc $rc)"; fi

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

# --- R9: the status step writes the manifest's version; no line, no render --
today="$(date +%Y-%m-%d)"
if grep -q -x "Status: version \`9.8.7\`, rendered \`$today\`, \`0\` unittest cases and \`0\` bash suites." "$fx/README.md"; then
  ok "readme-render: the README's status line names the manifest's version"
else bad "readme-render: the README's status line names the manifest's version ($(grep '^Status' "$fx/README.md"))"; fi
grep -v '^Status: version' "$src" > "$work/nostatus.md" && cp "$work/nostatus.md" "$src"
cp "$fx/README.md" "$work/README.before"; : > "$FAKE_LOG"
err="$(bash "$README_RENDER" --repo "$fx" 2>&1 >/dev/null)"; rc=$?
check "readme-render: a source without a status line exits 2" 2 "$rc"
check_out "...and says so" "readme-render: no status line in design/readme/source.md" "$err"
if cmp -s "$fx/README.md" "$work/README.before"; then ok "...and leaves README.md untouched"
else bad "...and leaves README.md untouched"; fi
no_runner "...and starts no runner"

echo; echo "$pass passed, $fail failed"; [ "$fail" -eq 0 ]
