#!/bin/bash
# respeak statusline segment: effective mode/tech_level (and which layer set
# it) · lexicon version · pending proposals.
# Reads the Claude Code statusline JSON payload on stdin (cwd), prints one
# line. Zero API tokens — pure local reads. Install via /respeak:init or by
# setting the statusLine key in settings.json to this script.
#
# The mode segment comes from the layered config resolved for the cwd
# (docs/config-layers.md): `technical/t3` means the plugin default;
# `bluf/t1 exec @docs/exec/.respeak.yaml` means a nearer layer decided.
set -u

# Resolve our own directory BEFORE changing into the payload's cwd, so a
# relative invocation (bash scripts/statusline.sh) still finds its siblings.
script_dir="$(cd "$(dirname "$0")" && pwd)"
RESPEAK_PY=""
[ -f "$script_dir/respeak-python.sh" ] && . "$script_dir/respeak-python.sh"

cwd=$(python3 -c "import json,sys; print(json.load(sys.stdin).get('cwd') or '.')" 2>/dev/null || pwd)
cd "$cwd" 2>/dev/null || true

mode=""
if [ -n "$RESPEAK_PY" ] && [ -f "$script_dir/respeak-config.py" ]; then
  mode="$("$RESPEAK_PY" "$script_dir/respeak-config.py" resolve --for "$cwd" --format statusline 2>/dev/null)"
fi
if [ -z "$mode" ]; then
  # no resolver available: fall back to a grep of the nearest config file
  cfg=".claude/respeak/config.yaml"
  [ -f "$cfg" ] || cfg="${CLAUDE_PLUGIN_ROOT:-}/config/respeak.config.yaml"
  [ -f "$cfg" ] && mode=$(grep -m1 'default_mode:' "$cfg" | awk '{print $2}')
fi

lex=".claude/respeak/lexicon.yaml"
[ -f "$lex" ] || lex="${CLAUDE_PLUGIN_ROOT:-}/corpus/lexicon.yaml"
ver="-"
[ -f "$lex" ] && ver=$(grep -m1 '^version:' "$lex" | awk '{print $2}')

props=0
[ -d ".claude/respeak/proposals" ] && props=$(find .claude/respeak/proposals -name '*.yaml' 2>/dev/null | wc -l | tr -d ' ')

printf 'respeak %s · lexicon v%s · %s proposals\n' "${mode:-?}" "${ver:--}" "${props}"
