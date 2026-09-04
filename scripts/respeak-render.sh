#!/bin/bash
# Headless respeak renderer for the API lane — no interactive Claude Code
# session available (CI, or a swarm's own post-processing step).
#
# Usage:
#   respeak-render.sh --mode {eli5|bluf|technical} --source <file> --out <file>
#                      [--contract <file>] [--max-rounds 2] [--budget-usd 1.50]
#
# Requires `claude-api-agent` on PATH — a headless, non-interactive wrapper
# over the Claude Agent SDK. It is NOT part of this plugin; install it
# separately. This script fails fast with a clear message if it is missing.
#
# What it does:
#   1. Builds a system prompt from agents/respeak.md: strips the YAML
#      frontmatter and substitutes ${CLAUDE_PLUGIN_ROOT} (unset outside a
#      Claude Code plugin session) so the agent's own "resolve config/corpus
#      here" instructions resolve to real paths.
#   1b. Resolves the layered configuration for --out (docs/config-layers.md):
#      user file, project file + scopes, and any .respeak.yaml in the folders
#      above the output file, with --mode applied on top. The resolved YAML
#      goes into the prompt as the agent's configuration (so a folder's tone
#      applies headlessly too) and into every measure call as --config.
#   2. Runs claude-api-agent non-interactively, piping a prompt (mode +
#      resolved config + optional contract notes + the source material) on
#      stdin.
#   3. Extracts the `.result` string from the agent's --output-format json
#      output, strips any preamble before the first real content line (a
#      leading `---` front-matter fence or a `#` heading) — belt-and-suspenders
#      against a chatty preamble the agent's own output contract forbids but
#      a model might still emit — and writes it to --out.
#   4. Gates --out with respeak-measure.py --fail-on error. On FAIL, re-runs
#      with the measure report appended to the prompt as a rewrite request,
#      then gates again; repeats up to --max-rounds (default 2, i.e. one
#      retry). Exits nonzero if still failing after the last round.
#
# Exit codes: 0 = wrote a passing narrative. 1 = still failing the gate
# after --max-rounds. 2 = usage/setup error (missing claude-api-agent, bad
# args, missing files, agent/parse failure).
#
# bash 3.2 compatible (macOS default): indexed arrays only, no associative
# arrays, no mapfile.
set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
. "$SCRIPT_DIR/respeak-python.sh"

MODE=""
SOURCE=""
OUT=""
CONTRACT=""
MAX_ROUNDS=2
BUDGET_USD="1.50"

while [ $# -gt 0 ]; do
  case "$1" in
    --mode) MODE="$2"; shift 2 ;;
    --source) SOURCE="$2"; shift 2 ;;
    --out) OUT="$2"; shift 2 ;;
    --contract) CONTRACT="$2"; shift 2 ;;
    --max-rounds) MAX_ROUNDS="$2"; shift 2 ;;
    --budget-usd) BUDGET_USD="$2"; shift 2 ;;
    *) echo "respeak-render: unknown argument $1" >&2; exit 2 ;;
  esac
done

if [ -z "$MODE" ] || [ -z "$SOURCE" ] || [ -z "$OUT" ]; then
  echo "usage: respeak-render.sh --mode {eli5|bluf|technical} --source <file> --out <file> [--contract <file>] [--max-rounds N] [--budget-usd N]" >&2
  exit 2
fi

[ -n "$RESPEAK_PY" ] || {
  echo "respeak-render: no python3 with PyYAML found — the resolver and the style gate need it (set RESPEAK_PYTHON=/path/to/python3 or install PyYAML)." >&2
  exit 2
}

command -v claude-api-agent >/dev/null 2>&1 || {
  echo "respeak-render: claude-api-agent not found on PATH — install the headless Claude Agent SDK wrapper this script depends on before using the API lane (see docs/architecture.md for the entry-points table)." >&2
  exit 2
}

[ -f "$SOURCE" ] || { echo "respeak-render: source not found: $SOURCE" >&2; exit 2; }

AGENT_MD="$PLUGIN_ROOT/agents/respeak.md"
[ -f "$AGENT_MD" ] || { echo "respeak-render: agent spec not found: $AGENT_MD" >&2; exit 2; }

MEASURE="$PLUGIN_ROOT/scripts/respeak-measure.py"
[ -f "$MEASURE" ] || { echo "respeak-render: measure script not found: $MEASURE" >&2; exit 2; }

TMPDIR_R="$(mktemp -d 2>/dev/null || echo "/tmp/respeak-render.$$")"
mkdir -p "$TMPDIR_R"
trap 'rm -rf "$TMPDIR_R"' EXIT

# --- 1. system prompt: agents/respeak.md, frontmatter stripped, ${CLAUDE_PLUGIN_ROOT}
#        substituted so the agent's path instructions resolve outside a session ---
SYSTEM_PROMPT="$TMPDIR_R/system-prompt.md"
"$RESPEAK_PY" - "$AGENT_MD" "$PLUGIN_ROOT" > "$SYSTEM_PROMPT" <<'PY'
import re, sys
path, plugin_root = sys.argv[1], sys.argv[2]
text = open(path).read()
text = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.S)
text = text.replace("${CLAUDE_PLUGIN_ROOT}", plugin_root)
sys.stdout.write(text)
PY

# --- 1b. resolved configuration for the output path (layered; --mode on top) ---
RESOLVED="$TMPDIR_R/resolved-config.yaml"
if ! CLAUDE_PLUGIN_ROOT="$PLUGIN_ROOT" "$RESPEAK_PY" "$SCRIPT_DIR/respeak-config.py" resolve \
      --for "$OUT" --mode "$MODE" --format yaml > "$RESOLVED" 2> "$TMPDIR_R/resolve.err"; then
  echo "respeak-render: could not resolve the layered config for $OUT; rendering with the agent's own file reads" >&2
  cat "$TMPDIR_R/resolve.err" >&2
  RESOLVED=""
fi

# --- 2. prompt: mode + resolved config + optional contract notes + source material ---
prompt_body() {
  # writes the base prompt (mode + config + contract + source) to stdout
  echo "Render the following source material as a respeak '$MODE' narrative."
  echo "Write only the rendered narrative, per your output contract — no preamble."
  echo
  if [ -n "$RESOLVED" ] && [ -s "$RESOLVED" ]; then
    echo "Resolved respeak configuration for this render (every layer already merged; use these values instead of reading config files):"
    echo '```yaml'
    cat "$RESOLVED"
    echo '```'
    echo
  fi
  if [ -n "$CONTRACT" ] && [ -f "$CONTRACT" ]; then
    echo "Additional contract notes for this render:"
    cat "$CONTRACT"
    echo
  fi
  echo "--- source material ($SOURCE) ---"
  cat "$SOURCE"
}

PROMPT_FILE="$TMPDIR_R/prompt-1.md"
prompt_body > "$PROMPT_FILE"

# --- add-dir: plugin root (config/corpus) + the source and output dirs ---
src_dir="$(cd "$(dirname "$SOURCE")" && pwd)"
out_dir="$(cd "$(dirname "$OUT")" 2>/dev/null && pwd || pwd)"
ADD_DIRS="$PLUGIN_ROOT"
[ "$src_dir" != "$PLUGIN_ROOT" ] && ADD_DIRS="$ADD_DIRS,$src_dir"
[ "$out_dir" != "$PLUGIN_ROOT" ] && [ "$out_dir" != "$src_dir" ] && ADD_DIRS="$ADD_DIRS,$out_dir"

run_agent() {
  # $1 = prompt file, $2 = destination for raw --output-format json
  claude-api-agent \
    --tag phase=render \
    --model claude-sonnet-5 \
    --tools "Read Grep Glob" \
    --permission-mode dontAsk \
    --max-budget-usd "$BUDGET_USD" \
    --output-format json \
    -p \
    --system-prompt-file "$SYSTEM_PROMPT" \
    --add-dir "$ADD_DIRS" \
    < "$1" > "$2"
}

extract_and_write() {
  # $1 = raw --output-format json file, $2 = destination narrative file
  "$RESPEAK_PY" - "$1" "$2" <<'PY'
import json, re, sys
src, dest = sys.argv[1], sys.argv[2]
raw = open(src).read()
try:
    data = json.loads(raw)
except json.JSONDecodeError as e:
    sys.stderr.write(f"respeak-render: could not parse claude-api-agent output as JSON: {e}\n")
    sys.exit(2)
result = data.get("result", "")
if not isinstance(result, str) or not result.strip():
    sys.stderr.write("respeak-render: no non-empty string .result in claude-api-agent output\n")
    sys.exit(2)
m = re.search(r"^(?:---|#)", result, re.M)
if m:
    result = result[m.start():]
with open(dest, "w") as f:
    f.write(result)
PY
}

# --- 3-4. run, extract, gate; retry with the report appended on failure ---
round=1
final_status=1

while [ "$round" -le "$MAX_ROUNDS" ]; do
  raw_out="$TMPDIR_R/agent-output-$round.json"
  err_log="$TMPDIR_R/agent-stderr-$round.log"

  run_agent "$PROMPT_FILE" "$raw_out" 2> "$err_log"
  agent_status=$?
  if [ "$agent_status" -ne 0 ]; then
    echo "respeak-render: claude-api-agent exited $agent_status (round $round)" >&2
    cat "$err_log" >&2
    exit 2
  fi

  extract_and_write "$raw_out" "$OUT" || exit 2

  if [ -n "$RESOLVED" ] && [ -s "$RESOLVED" ]; then
    gate_report="$("$RESPEAK_PY" "$MEASURE" "$OUT" --fail-on error --config "$RESOLVED" 2>&1)"
  else
    gate_report="$("$RESPEAK_PY" "$MEASURE" "$OUT" --fail-on error 2>&1)"
  fi
  gate_status=$?
  if [ "$gate_status" -eq 0 ]; then
    final_status=0
    break
  fi

  echo "respeak-render: round $round failed the style gate:" >&2
  echo "$gate_report" >&2

  [ "$round" -ge "$MAX_ROUNDS" ] && break

  next_round=$((round + 1))
  PROMPT_FILE="$TMPDIR_R/prompt-$next_round.md"
  {
    prompt_body
    echo
    echo "--- previous attempt failed the respeak style gate; rewrite to clear every hit below ---"
    echo "$gate_report"
  } > "$PROMPT_FILE"

  round=$next_round
done

if [ "$final_status" -ne 0 ]; then
  echo "respeak-render: still failing the style gate after $MAX_ROUNDS round(s); see $OUT and the report above" >&2
  exit 1
fi

echo "respeak-render: wrote $OUT (passed --fail-on error in round $round)"
exit 0
