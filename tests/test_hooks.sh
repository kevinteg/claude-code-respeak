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
export RESPEAK_CACHE_DIR="$work/cache"   # the suite never reads or rewrites the user's cache
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

# ----- v0.4.3: statusline must not word-split paths, and its plumbing must matter -----
sp="$work/sp ace/my proj"; mkdir -p "$sp/docs" "$sp/.git"
printf 'narrative: {default_mode: bluf, tech_level: 1}\n' > "$sp/.respeak.yaml"
out="$(sl_json "$sp/docs" "$sp" | bash "$STATUS")"
check_out "statusline: a space in current_dir and project_dir still resolves the folder" 'respeak bluf/t1 ' "$out"
# cwd and workspace.current_dir differ: current_dir wins (only its folder has a file)
mkdir -p "$proj/cur"; printf 'narrative: {profile: exec}\n' > "$proj/cur/.respeak.yaml"
out="$(printf '{"cwd": "%s", "workspace": {"current_dir": "%s", "project_dir": "%s"}}' "$proj/lab" "$proj/cur" "$proj" | bash "$STATUS")"
check_out "statusline: workspace.current_dir is preferred over cwd" 'exec @cur/.respeak.yaml' "$out"
# project_dir decides the root when nothing else can (no .git, no config): labels turn project-relative
bare="$work/bare"; mkdir -p "$bare/lab"; printf 'narrative: {profile: exec}\n' > "$bare/lab/.respeak.yaml"
out_with="$(sl_json "$bare/lab" "$bare" | bash "$STATUS")"
out_without="$(printf '{"workspace": {"current_dir": "%s"}}' "$bare/lab" | bash "$STATUS")"
check_out "statusline: with project_dir the folder label is project-relative" 'exec @lab/.respeak.yaml' "$out_with"
if [ "$out_with" != "$out_without" ]; then pass=$((pass + 1)); echo "ok   - statusline: project_dir changes the answer (plumbing is live)"
else fail=$((fail + 1)); echo "FAIL - statusline: project_dir made no difference: $out_without"; fi

# ----- v0.4.3: the Stop hook reads the knob the way the resolver does -----
for v in True 1 yes; do
  out="$(stop_json "$proj" "$MILESTONE" | CLAUDE_PLUGIN_OPTION_AUTO_NARRATIVE=$v bash "$noresolver/stop-narrative.sh")"
  check_out "stop: knob spelled '$v' fires without the resolver" 'auto-narrative is enabled' "$out"
done
nullproj="$work/nullproj"; mkdir -p "$nullproj/.claude/respeak" "$nullproj/.git"
printf 'narrative: {auto_narrative: null}\n' > "$nullproj/.claude/respeak/config.yaml"
out="$(stop_json "$nullproj" "$MILESTONE" | CLAUDE_PLUGIN_OPTION_AUTO_NARRATIVE=true CLAUDE_PROJECT_DIR="$nullproj" bash "$STOP")"
check_out "stop: a resolved null is off; the knob does not sneak back in" '' "$out"

echo; echo "$pass passed, $fail failed"; [ "$fail" -eq 0 ]
