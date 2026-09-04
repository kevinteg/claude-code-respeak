#!/bin/bash
# Tests for scripts/stop-narrative.sh and scripts/statusline.sh — the two
# consumers that had no tests before v0.4.1. Bash 3.2 compatible.
#
# Run: bash tests/test_hooks.sh
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$HERE/.." && pwd)"
STOP="$REPO_ROOT/scripts/stop-narrative.sh"
STATUS="$REPO_ROOT/scripts/statusline.sh"
pass=0; fail=0
check() { if [ "$2" -eq "$3" ]; then pass=$((pass + 1)); echo "ok   - $1"; else fail=$((fail + 1)); echo "FAIL - $1 (expected exit $2, got $3)"; fi; }
check_out() {
  # $1 = description, $2 = expected substring ('' = expect empty output), $3 = actual
  if [ -z "$2" ]; then
    if [ -z "$3" ]; then pass=$((pass + 1)); echo "ok   - $1"; else fail=$((fail + 1)); echo "FAIL - $1 (expected no output, got: $3)"; fi
  elif printf '%s' "$3" | grep -q -- "$2"; then pass=$((pass + 1)); echo "ok   - $1"
  else fail=$((fail + 1)); echo "FAIL - $1 (expected '$2' in: $3)"; fi
}

work="$(mktemp -d)"; work="$(cd "$work" && pwd -P)"
trap 'rm -rf "$work"' EXIT
export CLAUDE_CONFIG_DIR="$work/no-user-config"; mkdir -p "$CLAUDE_CONFIG_DIR"
unset CLAUDE_PLUGIN_OPTION_AUTO_NARRATIVE CLAUDE_PLUGIN_OPTION_DEFAULT_MODE CLAUDE_PROJECT_DIR RESPEAK_CONFIG 2>/dev/null || true
export CLAUDE_PLUGIN_ROOT="$REPO_ROOT"

proj="$work/proj"; mkdir -p "$proj/lab" "$proj/.git"
printf 'narrative: {auto_narrative: true, profile: exec}\n' > "$proj/lab/.respeak.yaml"
MILESTONE='All tests are passing and the migration is done.'
stop_json() { printf '{"cwd": "%s", "last_assistant_message": "%s"%s}' "$1" "$2" "${3:-}"; }

# ----- Stop hook ---------------------------------------------------------------
out="$(stop_json "$proj/lab" "$MILESTONE" | CLAUDE_PROJECT_DIR="$proj" bash "$STOP")"; rc=$?
check "stop: folder turns auto_narrative on (exit 0)" 0 "$rc"
check_out "stop: ...and the nudge names the folder's audience" 'profile exec, tech_level 1' "$out"
out="$(stop_json "$proj" "$MILESTONE" | CLAUDE_PROJECT_DIR="$proj" bash "$STOP")"
check_out "stop: cwd without the folder file stays silent" '' "$out"
out="$(stop_json "$proj/lab" "$MILESTONE" ', "stop_hook_active": true' | CLAUDE_PROJECT_DIR="$proj" bash "$STOP")"
check_out "stop: stop_hook_active guard stays silent" '' "$out"
out="$(stop_json "$proj/lab" "Still working on it." | CLAUDE_PROJECT_DIR="$proj" bash "$STOP")"
check_out "stop: a non-milestone turn stays silent" '' "$out"
out="$(stop_json "$proj/lab" "The build was abandoned." | CLAUDE_PROJECT_DIR="$proj" bash "$STOP")"
check_out "stop: 'abandoned' is not 'done' (word-bounded markers)" '' "$out"
out="$(stop_json "$proj" "$MILESTONE" | CLAUDE_PLUGIN_OPTION_AUTO_NARRATIVE=true CLAUDE_PLUGIN_OPTION_DEFAULT_MODE=bluf CLAUDE_PROJECT_DIR="$proj" bash "$STOP")"
check_out "stop: install-time userConfig knob turns it on (mode from the knob)" 'mode: bluf' "$out"
printf 'narrative: {auto_narrative: false}\n' > "$proj/.respeak.yaml"
out="$(stop_json "$proj" "$MILESTONE" | CLAUDE_PLUGIN_OPTION_AUTO_NARRATIVE=true CLAUDE_PROJECT_DIR="$proj" bash "$STOP")"
check_out "stop: a nearer file (false) beats the userConfig knob (true)" '' "$out"
rm -f "$proj/.respeak.yaml"
badpath="$work/badpath"; mkdir -p "$badpath"; printf '#!/bin/sh\nexit 127\n' > "$badpath/python3"; chmod +x "$badpath/python3"
out="$(stop_json "$proj/lab" "$MILESTONE" | PATH="$badpath:$PATH" CLAUDE_PROJECT_DIR="$proj" bash "$STOP")"
check_out "stop: broken python3 shim on PATH does not silence the hook" 'auto-narrative is enabled' "$out"
noresolver="$work/scripts-noresolver"; cp -R "$REPO_ROOT/scripts" "$noresolver"; rm -f "$noresolver/respeak-config.py"
out="$(stop_json "$proj/lab" "$MILESTONE" | CLAUDE_PLUGIN_OPTION_AUTO_NARRATIVE=true bash "$noresolver/stop-narrative.sh")"
check_out "stop: without the resolver, the userConfig knob alone decides (documented)" 'mode: technical' "$out"
out="$(printf 'not json' | CLAUDE_PROJECT_DIR="$proj" bash "$STOP")"; rc=$?
check "stop: malformed stdin exits 0" 0 "$rc"; check_out "stop: ...silently" '' "$out"

# ----- statusline ------------------------------------------------------------
sl_json() { printf '{"cwd": "%s", "workspace": {"current_dir": "%s", "project_dir": "%s"}}' "$1" "$1" "$2"; }
out="$(sl_json "$proj/lab" "$proj" | bash "$STATUS")"; rc=$?
check "statusline: exits 0" 0 "$rc"
check_out "statusline: shows the folder's profile and its file" 'respeak bluf/t1 exec @lab/.respeak.yaml' "$out"
check_out "statusline: ...and the lexicon segment" 'lexicon v' "$out"
out="$(sl_json "$proj" "$proj" | bash "$STATUS")"
check_out "statusline: plugin default outside the folder" 'respeak technical/t3 ' "$out"
mkdir -p "$proj/.claude/respeak"; printf 'gate: {enabled: true}\nnarrative: {default_mode: bluf}\n' > "$proj/.claude/respeak/config.yaml"
out="$(sl_json "$proj/docs" "$proj/docs" | bash "$STATUS")"
check_out "statusline: launched in <repo>/docs, the repo config still shows" 'bluf/t3' "$out"
out="$(printf '{"model": {"display_name": "Opus"}}' | bash "$STATUS")"; rc=$?
check "statusline: payload without cwd exits 0" 0 "$rc"
check_out "statusline: ...and still prints the segment" 'respeak ' "$out"
out="$(sl_json "$proj/lab" "$proj" | PATH="$badpath:$PATH" bash "$STATUS")"
check_out "statusline: broken python3 shim on PATH still resolves" 'exec @lab/.respeak.yaml' "$out"

echo; echo "$pass passed, $fail failed"; [ "$fail" -eq 0 ]
