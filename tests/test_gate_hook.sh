#!/bin/bash
# Tests for scripts/respeak-gate.sh — the opt-in PostToolUse enforcement hook.
# Bash 3.2 compatible (macOS default): indexed arrays only, no associative
# arrays, no mapfile.
#
# Run: bash tests/test_gate_hook.sh
set -u

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$HERE/.." && pwd)"
GATE="$REPO_ROOT/scripts/respeak-gate.sh"

pass=0
fail=0

check() {
  # $1 = description, $2 = expected exit code, $3 = actual exit code
  if [ "$2" -eq "$3" ]; then
    pass=$((pass + 1))
    echo "ok   - $1"
  else
    fail=$((fail + 1))
    echo "FAIL - $1 (expected exit $2, got $3)"
  fi
}

hook_json_for() {
  # $1 = file path -> {"tool_input": {"file_path": "..."}}
  python3 -c 'import json, sys; print(json.dumps({"tool_input": {"file_path": sys.argv[1]}}))' "$1"
}

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

BANNED_TEXT="This design is load-bearing for everything downstream."
CLEAN_TEXT="The plan uses the cache and finishes in three steps."

# --- fixture: gate enabled, banned phrase -> blocks (exit 2) ------------
proj_on="$work/proj-on"
mkdir -p "$proj_on/.claude/respeak"
cat > "$proj_on/.claude/respeak/config.yaml" <<'YAML'
gate:
  enabled: true
  include: ["**/*.md"]
  exclude: []
  fail_on: error
YAML
doc_on="$proj_on/notes.md"
echo "$BANNED_TEXT" > "$doc_on"

hook_json_for "$doc_on" \
  | CLAUDE_PROJECT_DIR="$proj_on" CLAUDE_PLUGIN_ROOT="$REPO_ROOT" "$GATE" \
  > "$work/gate-on.out" 2>&1
check "gate enabled + banned phrase blocks (exit 2)" 2 "$?"

# --- fixture: gate disabled -> silent no-op (exit 0) --------------------
proj_off="$work/proj-off"
mkdir -p "$proj_off/.claude/respeak"
cat > "$proj_off/.claude/respeak/config.yaml" <<'YAML'
gate:
  enabled: false
YAML
doc_off="$proj_off/notes.md"
echo "$BANNED_TEXT" > "$doc_off"

hook_json_for "$doc_off" \
  | CLAUDE_PROJECT_DIR="$proj_off" CLAUDE_PLUGIN_ROOT="$REPO_ROOT" "$GATE" \
  > "$work/gate-off.out" 2>&1
check "gate disabled is a silent no-op (exit 0)" 0 "$?"

# --- fixture: no project config at all -> silent no-op (exit 0) ---------
proj_none="$work/proj-none"
mkdir -p "$proj_none"
doc_none="$proj_none/notes.md"
echo "$BANNED_TEXT" > "$doc_none"

hook_json_for "$doc_none" \
  | CLAUDE_PROJECT_DIR="$proj_none" CLAUDE_PLUGIN_ROOT="$REPO_ROOT" "$GATE" \
  > "$work/gate-none.out" 2>&1
check "no project config is a silent no-op (exit 0)" 0 "$?"

# --- fixture: non-.md file is a no-op even with the gate enabled --------
doc_txt="$proj_on/notes.txt"
echo "$BANNED_TEXT" > "$doc_txt"

hook_json_for "$doc_txt" \
  | CLAUDE_PROJECT_DIR="$proj_on" CLAUDE_PLUGIN_ROOT="$REPO_ROOT" "$GATE" \
  > "$work/gate-txt.out" 2>&1
check "non-.md file is a no-op (exit 0)" 0 "$?"

# --- fixture: gate enabled, clean doc -> passes (exit 0) ----------------
doc_clean="$proj_on/clean.md"
echo "$CLEAN_TEXT" > "$doc_clean"

hook_json_for "$doc_clean" \
  | CLAUDE_PROJECT_DIR="$proj_on" CLAUDE_PLUGIN_ROOT="$REPO_ROOT" "$GATE" \
  > "$work/gate-clean.out" 2>&1
check "gate enabled + clean doc passes (exit 0)" 0 "$?"

echo
echo "$pass passed, $fail failed"
[ "$fail" -eq 0 ]
