#!/bin/bash
# Tests for scripts/respeak-gate.sh — the opt-in PostToolUse enforcement hook,
# now driven by the layered-config resolver (docs/config-layers.md).
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

run_gate() {
  # $1 = project dir, $2 = file path, $3 = output file; extra env via caller
  hook_json_for "$2" \
    | CLAUDE_PROJECT_DIR="$1" CLAUDE_PLUGIN_ROOT="$REPO_ROOT" "$GATE" > "$3" 2>&1
}

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

# Isolate the user layer: an empty CLAUDE_CONFIG_DIR unless a case sets one.
# HOME stays real because PyYAML may live in the interpreter's user site.
export CLAUDE_CONFIG_DIR="$work/no-user-config"
mkdir -p "$CLAUDE_CONFIG_DIR"
unset CLAUDE_PLUGIN_OPTION_DEFAULT_MODE CLAUDE_PLUGIN_OPTION_TECH_LEVEL CLAUDE_PLUGIN_OPTION_AUTO_NARRATIVE RESPEAK_CONFIG 2>/dev/null || true

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
scopes:
  - paths: ["drafts/**"]
    gate: { fail_on: none }
YAML
doc_on="$proj_on/notes.md"
echo "$BANNED_TEXT" > "$doc_on"
run_gate "$proj_on" "$doc_on" "$work/gate-on.out"
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
run_gate "$proj_off" "$doc_off" "$work/gate-off.out"
check "gate disabled is a silent no-op (exit 0)" 0 "$?"

# --- fixture: no project config at all -> silent no-op (exit 0) ---------
proj_none="$work/proj-none"
mkdir -p "$proj_none"
doc_none="$proj_none/notes.md"
echo "$BANNED_TEXT" > "$doc_none"
run_gate "$proj_none" "$doc_none" "$work/gate-none.out"
check "no project config is a silent no-op (exit 0)" 0 "$?"

# --- fixture: non-.md file is a no-op even with the gate enabled --------
doc_txt="$proj_on/notes.txt"
echo "$BANNED_TEXT" > "$doc_txt"
run_gate "$proj_on" "$doc_txt" "$work/gate-txt.out"
check "non-.md file is a no-op (exit 0)" 0 "$?"

# --- fixture: gate enabled, clean doc -> passes (exit 0) ----------------
doc_clean="$proj_on/clean.md"
echo "$CLEAN_TEXT" > "$doc_clean"
run_gate "$proj_on" "$doc_clean" "$work/gate-clean.out"
check "gate enabled + clean doc passes (exit 0)" 0 "$?"

# --- layered: a folder .respeak.yaml softens fail_on for its own files ---
mkdir -p "$proj_on/scratch"
cat > "$proj_on/scratch/.respeak.yaml" <<'YAML'
gate:
  fail_on: none
YAML
doc_scratch="$proj_on/scratch/idea.md"
echo "$BANNED_TEXT" > "$doc_scratch"
run_gate "$proj_on" "$doc_scratch" "$work/gate-folder-soft.out"
check "folder .respeak.yaml fail_on: none passes a banned doc there (exit 0)" 0 "$?"
run_gate "$proj_on" "$doc_on" "$work/gate-folder-elsewhere.out"
check "...while the project root still blocks (exit 2)" 2 "$?"

# --- layered: a project scope softens fail_on by path glob --------------
mkdir -p "$proj_on/drafts"
doc_draft="$proj_on/drafts/wip.md"
echo "$BANNED_TEXT" > "$doc_draft"
run_gate "$proj_on" "$doc_draft" "$work/gate-scope.out"
check "scopes: drafts/** fail_on: none passes a banned draft (exit 0)" 0 "$?"

# --- layered: a folder file cannot turn the gate ON -----------------------
mkdir -p "$proj_off/docs"
cat > "$proj_off/docs/.respeak.yaml" <<'YAML'
gate:
  enabled: true
YAML
doc_folder_on="$proj_off/docs/page.md"
echo "$BANNED_TEXT" > "$doc_folder_on"
run_gate "$proj_off" "$doc_folder_on" "$work/gate-folder-enable.out"
check "folder .respeak.yaml gate.enabled: true is ignored (exit 0)" 0 "$?"

# --- layered: a user-level file cannot turn the gate ON -------------------
user_cfg="$work/user-config"
mkdir -p "$user_cfg/respeak"
cat > "$user_cfg/respeak/config.yaml" <<'YAML'
gate:
  enabled: true
YAML
hook_json_for "$doc_none" \
  | CLAUDE_CONFIG_DIR="$user_cfg" CLAUDE_PROJECT_DIR="$proj_none" CLAUDE_PLUGIN_ROOT="$REPO_ROOT" "$GATE" \
  > "$work/gate-user-enable.out" 2>&1
check "user-level gate.enabled: true is ignored (exit 0)" 0 "$?"

# --- layered: a user-level gate.allow appends into an enabled project -----
cat > "$user_cfg/respeak/config.yaml" <<'YAML'
gate:
  allow: ["load-bearing"]
YAML
hook_json_for "$doc_on" \
  | CLAUDE_CONFIG_DIR="$user_cfg" CLAUDE_PROJECT_DIR="$proj_on" CLAUDE_PLUGIN_ROOT="$REPO_ROOT" "$GATE" \
  > "$work/gate-user-allow.out" 2>&1
check "user-level gate.allow silences the rule in an enabled project (exit 0)" 0 "$?"

echo
echo "$pass passed, $fail failed"
[ "$fail" -eq 0 ]
