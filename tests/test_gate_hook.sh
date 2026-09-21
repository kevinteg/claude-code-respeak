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
export RESPEAK_CACHE_DIR="$work/cache"   # the suite never reads or rewrites the user's cache

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

# ===== v0.4.1: adversarial-review regressions =================================
# Each case below reproduces a confirmed finding against the fixed hook.

check_grep() {
  # $1 = description, $2 = pattern, $3 = file
  if grep -q -- "$2" "$3"; then pass=$((pass + 1)); echo "ok   - $1"
  else fail=$((fail + 1)); echo "FAIL - $1 (pattern '$2' not in $(basename "$3"))"; cat "$3" | head -5; fi
}

# --- a broken python3 shim first on PATH must not disable an enabled gate ----
badpath="$work/badpath"; mkdir -p "$badpath"
printf '#!/bin/sh\necho "pyenv: python3: command not found" >&2\nexit 127\n' > "$badpath/python3"; chmod +x "$badpath/python3"
hook_json_for "$doc_on" \
  | PATH="$badpath:$PATH" CLAUDE_PROJECT_DIR="$proj_on" CLAUDE_PLUGIN_ROOT="$REPO_ROOT" "$GATE" \
  > "$work/gate-badshim.out" 2>&1
check "broken python3 shim on PATH still blocks (exit 2)" 2 "$?"

# --- a measure SETUP error (corrupt corpus) fails OPEN, with a trace line ----
fakeroot="$work/fakeroot"; mkdir -p "$fakeroot/corpus" "$fakeroot/config"
cp "$REPO_ROOT/config/respeak.config.yaml" "$fakeroot/config/"
printf 'entries: [\n' > "$fakeroot/corpus/banned-phrases.yaml"
hook_json_for "$doc_clean" \
  | RESPEAK_GATE_TRACE=1 CLAUDE_PROJECT_DIR="$proj_on" CLAUDE_PLUGIN_ROOT="$fakeroot" "$GATE" \
  > "$work/gate-corrupt-corpus.out" 2>&1
check "corrupt corpus is a setup error: fails open (exit 0)" 0 "$?"
check_grep "...and the trace names it as a setup error, not a verdict" "setup error" "$work/gate-corrupt-corpus.out"
hook_json_for "$proj_on/ghost.md" \
  | RESPEAK_GATE_TRACE=1 CLAUDE_PROJECT_DIR="$proj_on" CLAUDE_PLUGIN_ROOT="$REPO_ROOT" "$GATE" \
  > "$work/gate-ghost.out" 2>&1
check "unreadable target fails open (exit 0)" 0 "$?"

# --- v0.4.2: setup errors that used to escape as tracebacks (exit 1) --------
doc_latin1="$proj_on/latin1.md"; printf 'The plan uses the cache. Caf\xe9 is not UTF-8.\n' > "$doc_latin1"
hook_json_for "$doc_latin1" | RESPEAK_GATE_TRACE=1 CLAUDE_PROJECT_DIR="$proj_on" CLAUDE_PLUGIN_ROOT="$REPO_ROOT" "$GATE" > "$work/gate-latin1.out" 2>&1
check "non-UTF-8 doc is unreadable: fails open (exit 0)" 0 "$?"
check_grep "...as a setup error" "setup error" "$work/gate-latin1.out"
proj_badallow="$work/proj-badallow"; mkdir -p "$proj_badallow/.claude/respeak"
printf 'gate: {enabled: true, include: ["**/*.md"], fail_on: error, allow: ["("]}\n' > "$proj_badallow/.claude/respeak/config.yaml"
doc_badallow="$proj_badallow/clean.md"; echo "$CLEAN_TEXT" > "$doc_badallow"
hook_json_for "$doc_badallow" | RESPEAK_GATE_TRACE=1 CLAUDE_PROJECT_DIR="$proj_badallow" CLAUDE_PLUGIN_ROOT="$REPO_ROOT" "$GATE" > "$work/gate-badallow.out" 2>&1
check "invalid gate.allow regex is a config error: fails open (exit 0)" 0 "$?"
for shape in 'foo: bar' '- a' 'categories: {x: {entries: [{pattern: "(", severity: error}]}}'; do
  printf '%s\n' "$shape" > "$fakeroot/corpus/banned-phrases.yaml"
  hook_json_for "$doc_clean" | CLAUDE_PROJECT_DIR="$proj_on" CLAUDE_PLUGIN_ROOT="$fakeroot" "$GATE" > "$work/gate-shape.out" 2>&1
  check "corpus shape error ($shape) fails open (exit 0)" 0 "$?"
done
: > "$fakeroot/corpus/banned-phrases.yaml"
hook_json_for "$doc_clean" | CLAUDE_PROJECT_DIR="$proj_on" CLAUDE_PLUGIN_ROOT="$fakeroot" "$GATE" > "$work/gate-empty-corpus.out" 2>&1
check "empty corpus file fails open (exit 0)" 0 "$?"

# --- a pass is a real pass: the trace line proves measure ran ----------------
hook_json_for "$doc_clean" \
  | RESPEAK_GATE_TRACE=1 CLAUDE_PROJECT_DIR="$proj_on" CLAUDE_PLUGIN_ROOT="$REPO_ROOT" "$GATE" \
  > "$work/gate-clean-trace.out" 2>&1
check "clean doc passes (exit 0)" 0 "$?"
check_grep "...with a 'checked ... pass' trace (not failed-open)" "checked .*clean.md (fail-on: error): pass" "$work/gate-clean-trace.out"

# --- CLI mode gates one file exactly like the hook ---------------------------
CLAUDE_PROJECT_DIR="$proj_on" CLAUDE_PLUGIN_ROOT="$REPO_ROOT" "$GATE" --file "$doc_on" > "$work/gate-cli.out" 2>&1
check "--file <banned doc> blocks (exit 2)" 2 "$?"
CLAUDE_PROJECT_DIR="$proj_on" CLAUDE_PLUGIN_ROOT="$REPO_ROOT" "$GATE" --file "$doc_clean" > "$work/gate-cli-clean.out" 2>&1
check "--file <clean doc> passes (exit 0)" 0 "$?"

# --- the Markdown contract: include may widen to .markdown/.mdx, never past --
proj_md="$work/proj-md"; mkdir -p "$proj_md/.claude/respeak"
printf 'gate:\n  enabled: true\n  include: ["**/*.md", "**/*.mdx", "**/*.txt"]\n' > "$proj_md/.claude/respeak/config.yaml"
doc_mdx="$proj_md/page.mdx"; echo "$BANNED_TEXT" > "$doc_mdx"
hook_json_for "$doc_mdx" | CLAUDE_PROJECT_DIR="$proj_md" CLAUDE_PLUGIN_ROOT="$REPO_ROOT" "$GATE" > "$work/gate-mdx.out" 2>&1
check ".mdx listed in gate.include is gated (exit 2)" 2 "$?"
doc_mdx_narrow="$proj_on/page.mdx"; echo "$BANNED_TEXT" > "$doc_mdx_narrow"   # proj_on includes **/*.md only
hook_json_for "$doc_mdx_narrow" | CLAUDE_PROJECT_DIR="$proj_on" CLAUDE_PLUGIN_ROOT="$REPO_ROOT" "$GATE" > "$work/gate-mdx-narrow.out" 2>&1
check ".mdx NOT listed in gate.include is skipped (exit 0)" 0 "$?"
doc_txt2="$proj_md/notes.txt"; echo "$BANNED_TEXT" > "$doc_txt2"
hook_json_for "$doc_txt2" | CLAUDE_PROJECT_DIR="$proj_md" CLAUDE_PLUGIN_ROOT="$REPO_ROOT" "$GATE" > "$work/gate-txt2.out" 2>&1
check ".txt in gate.include is still skipped: the gate covers Markdown only (exit 0)" 0 "$?"

# --- v0.4.3: extension case parity between hook and resolver ----------------
proj_up="$work/proj-up"; mkdir -p "$proj_up/.claude/respeak"
printf 'gate: {enabled: true, include: ["**/*"], fail_on: error}\n' > "$proj_up/.claude/respeak/config.yaml"
for name in README.MDX Page.Markdown NOTES.MD; do
  echo "$BANNED_TEXT" > "$proj_up/$name"
  hook_json_for "$proj_up/$name" | CLAUDE_PROJECT_DIR="$proj_up" CLAUDE_PLUGIN_ROOT="$REPO_ROOT" "$GATE" > "$work/gate-up.out" 2>&1
  check "$name is gated like its lowercase twin (exit 2)" 2 "$?"
done
echo "$BANNED_TEXT" > "$proj_up/notes.TXT"
hook_json_for "$proj_up/notes.TXT" | CLAUDE_PROJECT_DIR="$proj_up" CLAUDE_PLUGIN_ROOT="$REPO_ROOT" "$GATE" > "$work/gate-up-txt.out" 2>&1
check "notes.TXT is still not Markdown (exit 0)" 0 "$?"

# --- v0.4.3: a symlink inside the project pointing outside is still gated -----
mkdir -p "$work/outside"; echo "$BANNED_TEXT" > "$work/outside/ext.md"; ln -s "$work/outside/ext.md" "$proj_on/ext.md"
hook_json_for "$proj_on/ext.md" | CLAUDE_PROJECT_DIR="$proj_on" CLAUDE_PLUGIN_ROOT="$REPO_ROOT" "$GATE" > "$work/gate-inlink.out" 2>&1
check "in-project symlink to an outside file is gated (exit 2)" 2 "$?"

# --- discovery: no CLAUDE_PROJECT_DIR at all (CI), the config is found -------
hook_json_for "$doc_on" | env -u CLAUDE_PROJECT_DIR CLAUDE_PLUGIN_ROOT="$REPO_ROOT" "$GATE" > "$work/gate-nocpd.out" 2>&1
check "no CLAUDE_PROJECT_DIR: discovery finds the project config (exit 2)" 2 "$?"

# --- launched in a subdirectory: the repo's config still governs -------------
mkdir -p "$proj_on/docs"; doc_sub="$proj_on/docs/page.md"; echo "$BANNED_TEXT" > "$doc_sub"
hook_json_for "$doc_sub" | CLAUDE_PROJECT_DIR="$proj_on/docs" CLAUDE_PLUGIN_ROOT="$REPO_ROOT" "$GATE" > "$work/gate-subdir.out" 2>&1
check "session launched in <repo>/docs still enforces the repo config (exit 2)" 2 "$?"

# --- monorepo: a nested project config is the nearest, and it never opted in -
mkdir -p "$proj_on/pkg/.claude/respeak"; printf 'narrative: {default_mode: bluf}\n' > "$proj_on/pkg/.claude/respeak/config.yaml"
doc_pkg="$proj_on/pkg/a.md"; echo "$BANNED_TEXT" > "$doc_pkg"
hook_json_for "$doc_pkg" | RESPEAK_GATE_TRACE=1 CLAUDE_PROJECT_DIR="$proj_on" CLAUDE_PLUGIN_ROOT="$REPO_ROOT" "$GATE" > "$work/gate-nested.out" 2>&1
check "nested project config governs its subtree (exit 0: it did not opt in)" 0 "$?"
check_grep "...and the trace says why" "not applicable" "$work/gate-nested.out"

# --- symlinked spelling of the project path ----------------------------------
ln -s "$work" "$work/../$(basename "$work")-link" 2>/dev/null || true
linkroot="$work/../$(basename "$work")-link"
if [ -d "$linkroot" ]; then
  hook_json_for "$linkroot/proj-on/notes.md" | CLAUDE_PROJECT_DIR="$proj_on" CLAUDE_PLUGIN_ROOT="$REPO_ROOT" "$GATE" > "$work/gate-symlink.out" 2>&1
  check "file path through a symlink is still inside the project (exit 2)" 2 "$?"
  rm -f "$linkroot"
fi

# --- a user-level file cannot enable the gate via discovery either -----------
user2="$work/user2/.claude"; mkdir -p "$user2/respeak" "$work/user2/code/repo/.git"
printf 'gate: {enabled: true}\n' > "$user2/respeak/config.yaml"
doc_home="$work/user2/code/repo/notes.md"; echo "$BANNED_TEXT" > "$doc_home"
hook_json_for "$doc_home" | env -u CLAUDE_PROJECT_DIR CLAUDE_CONFIG_DIR="$user2" CLAUDE_PLUGIN_ROOT="$REPO_ROOT" "$GATE" > "$work/gate-user-discovery.out" 2>&1
check "user file under \$HOME is never discovered as a project file (exit 0)" 0 "$?"

# ===== v0.6: gate.block_on — a verdict is about what the write INTRODUCED ====
# The baseline is the file as it was, so these fixtures need a repository:
# `git show HEAD:./<name>` is the first choice, the Edit's own strings the
# second, an empty file the last.

edit_json_for() {
  # $1 = file path, $2 = old_string, $3 = new_string -> an Edit hook event
  python3 -c 'import json, sys; print(json.dumps({"tool_name": "Edit", "tool_input": {"file_path": sys.argv[1], "old_string": sys.argv[2], "new_string": sys.argv[3]}}))' "$1" "$2" "$3"
}

run_gate_event() {
  # $1 = project dir, $2 = hook JSON, $3 = stdout file; the trace and the
  # measure report land in $3.err, because these cases read both channels
  printf '%s' "$2" \
    | RESPEAK_GATE_TRACE=1 CLAUDE_PROJECT_DIR="$1" CLAUDE_PLUGIN_ROOT="$REPO_ROOT" "$GATE" > "$3" 2>"$3.err"
}

git_in() { git -C "$proj_git" -c commit.gpgsign=false "$@"; }

proj_git="$work/proj-git"
mkdir -p "$proj_git/.claude/respeak" "$proj_git/any"
cat > "$proj_git/.claude/respeak/config.yaml" <<'YAML'
gate:
  enabled: true
  include: ["**/*.md"]
  fail_on: error
YAML
printf 'gate: {block_on: any}\n' > "$proj_git/any/.respeak.yaml"
for f in tracked.md intro.md any/doc.md; do
  printf '# Notes\n\n%s\n' "$BANNED_TEXT" > "$proj_git/$f"
done
git_in init -q >/dev/null 2>&1
git_in config user.name "respeak tests"
git_in config user.email "tests@example.invalid"
git_in add -A >/dev/null 2>&1
git_in commit -q -m "fixture" >/dev/null 2>&1

# --- an edit that adds no hit passes, and names what the file already carried
printf '# Notes today\n\n%s\n' "$BANNED_TEXT" > "$proj_git/tracked.md"
run_gate_event "$proj_git" "$(edit_json_for "$proj_git/tracked.md" "# Notes" "# Notes today")" "$work/gate-preexisting.out"
check "tracked file, only a pre-existing hit: the edit passes (exit 0)" 0 "$?"
check_grep "...and stdout names the hits it did not introduce" "pre-existing style hit(s) remain" "$work/gate-preexisting.out"
check_grep "...as PostToolUse additionalContext" "additionalContext" "$work/gate-preexisting.out"
check_grep "...naming the rule" "load-bearing" "$work/gate-preexisting.out"

# --- an edit that adds one blocks, per-rule: 2 hits against a baseline of 1 --
printf '# Notes\n\n%s\n%s\n' "$BANNED_TEXT" "$BANNED_TEXT" > "$proj_git/intro.md"
run_gate_event "$proj_git" "$(edit_json_for "$proj_git/intro.md" "$BANNED_TEXT" "$BANNED_TEXT
$BANNED_TEXT")" "$work/gate-introduced.out"
check "an edit that introduces a hit blocks (exit 2)" 2 "$?"
check_grep "...and the report separates new from pre-existing" "new 1, pre-existing 1" "$work/gate-introduced.out.err"

# --- block_on: any restores the whole-file verdict (the behaviour before v0.6)
printf '# Notes today\n\n%s\n' "$BANNED_TEXT" > "$proj_git/any/doc.md"
run_gate_event "$proj_git" "$(edit_json_for "$proj_git/any/doc.md" "# Notes" "# Notes today")" "$work/gate-blockon-any.out"
check "block_on: any blocks the same edit on its pre-existing hit (exit 2)" 2 "$?"

# --- a brand-new document has no baseline: it is gated whole ----------------
printf '%s\n' "$BANNED_TEXT" > "$proj_git/fresh.md"
run_gate_event "$proj_git" "$(hook_json_for "$proj_git/fresh.md")" "$work/gate-untracked-new.out"
check "untracked new file with a hit is gated whole (exit 2)" 2 "$?"

# --- untracked, but the Edit carries the pre-edit text: a removal passes -----
printf 'The plan is central to the release.\n' > "$proj_git/removed.md"
run_gate_event "$proj_git" "$(edit_json_for "$proj_git/removed.md" "The plan is load-bearing for the release." "The plan is central to the release.")" "$work/gate-removed.out"
check "untracked file, an edit that removes the only hit passes (exit 0)" 0 "$?"
check_grep "...measured against the text rebuilt from the edit" "baseline .*: the pre-edit text" "$work/gate-removed.out.err"

# --- --file is the CI surface: whole file, unless --baseline-ref says otherwise
RESPEAK_GATE_TRACE=1 CLAUDE_PROJECT_DIR="$proj_git" CLAUDE_PLUGIN_ROOT="$REPO_ROOT" "$GATE" --file "$proj_git/tracked.md" > "$work/gate-cli-whole.out" 2>&1
check "--file gates the whole file whatever block_on says (exit 2)" 2 "$?"
RESPEAK_GATE_TRACE=1 CLAUDE_PROJECT_DIR="$proj_git" CLAUDE_PLUGIN_ROOT="$REPO_ROOT" "$GATE" --file "$proj_git/tracked.md" --baseline-ref HEAD > "$work/gate-cli-ref.out" 2>&1
check "--file --baseline-ref HEAD measures against the commit (exit 0)" 0 "$?"
check_grep "...and says what remains" "pre-existing style hit(s) remain" "$work/gate-cli-ref.out"

echo
echo "$pass passed, $fail failed"
[ "$fail" -eq 0 ]
