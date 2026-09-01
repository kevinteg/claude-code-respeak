#!/bin/bash
# respeak statusline segment: mode · lexicon version · pending proposals.
# Reads the Claude Code statusline JSON payload on stdin (cwd), prints one line.
# Zero API tokens — pure local reads. Install via /respeak:init or by setting
# the statusLine key in settings.json to this script.
set -u

cwd=$(python3 -c "import json,sys; print(json.load(sys.stdin).get('cwd') or '.')" 2>/dev/null || pwd)
cd "$cwd" 2>/dev/null || true

cfg=".claude/respeak/config.yaml"
[ -f "$cfg" ] || cfg="${CLAUDE_PLUGIN_ROOT:-}/config/respeak.config.yaml"
mode="?"
[ -f "$cfg" ] && mode=$(grep -m1 'default_mode:' "$cfg" | awk '{print $2}')

lex=".claude/respeak/lexicon.yaml"
[ -f "$lex" ] || lex="${CLAUDE_PLUGIN_ROOT:-}/corpus/lexicon.yaml"
ver="-"
[ -f "$lex" ] && ver=$(grep -m1 '^version:' "$lex" | awk '{print $2}')

props=0
[ -d ".claude/respeak/proposals" ] && props=$(find .claude/respeak/proposals -name '*.yaml' 2>/dev/null | wc -l | tr -d ' ')

printf 'respeak %s · lexicon v%s · %s proposals\n' "${mode:-?}" "${ver:--}" "${props}"
