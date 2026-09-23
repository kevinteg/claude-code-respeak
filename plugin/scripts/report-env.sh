#!/bin/bash
# Environment for /respeak:report — the issue target plus the footer facts a
# bug report needs. Prints one JSON object and ALWAYS exits 0; any fact it
# cannot detect is the string "unknown" (or null for owner_repo), never an
# error, so the report flow is never blocked by its own footer.
#
#   scripts/report-env.sh            # JSON
#   scripts/report-env.sh --footer   # the Markdown footer block
#
# Reads nothing outside the plugin directory. Never reads a project's
# documents, respeak config, lexicon, or proposals: the report skill's
# privacy default is the user's text plus this footer, nothing more.
# bash 3.2 compatible (macOS default).
set -u

script_dir="$(cd "$(dirname "$0")" && pwd)"
plugin_root="${CLAUDE_PLUGIN_ROOT:-$(cd "$script_dir/.." && pwd)}"
manifest="$plugin_root/.claude-plugin/plugin.json"

RESPEAK_PY=""; RESPEAK_PY_STD=""
[ -f "$script_dir/respeak-python.sh" ] && . "$script_dir/respeak-python.sh" 2>/dev/null

json_field() {
  # $1 = key; prints the string value of a top-level key in the manifest, or nothing.
  [ -f "$manifest" ] || return 0
  if [ -n "$RESPEAK_PY_STD" ]; then
    "$RESPEAK_PY_STD" - "$manifest" "$1" 2>/dev/null <<'PY'
import json, sys
try:
    v = json.load(open(sys.argv[1])).get(sys.argv[2])
    if isinstance(v, dict): v = v.get("url")
    if isinstance(v, str): print(v)
except Exception:
    pass
PY
  else
    sed -n 's/.*"'"$1"'"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$manifest" | head -1
  fi
}

repository="$(json_field repository)"
version="$(json_field version)"; [ -n "$version" ] || version="unknown"

# https://github.com/o/r(.git) | git@github.com:o/r.git | o/r  ->  o/r
owner_repo="$(printf '%s' "$repository" \
  | sed -E 's#[/[:space:]]+$##; s#\.git$##; s#^git@github\.com:##; s#^https?://(www\.)?github\.com/##')"
case "$owner_repo" in
  */*/*|""|*" "*|/*) owner_repo="" ;;
esac

plugin_sha="$(git -C "$plugin_root" rev-parse --short HEAD 2>/dev/null || echo unknown)"
claude_version="$(claude --version 2>/dev/null | head -1)"; [ -n "$claude_version" ] || claude_version="unknown"
os="$(uname -sr 2>/dev/null || echo unknown)"
if [ -n "$RESPEAK_PY" ]; then
  python="$("$RESPEAK_PY" -c 'import sys;print(sys.version.split()[0])' 2>/dev/null || echo unknown) ($RESPEAK_PY), PyYAML present"
elif [ -n "$RESPEAK_PY_STD" ]; then
  python="$("$RESPEAK_PY_STD" -c 'import sys;print(sys.version.split()[0])' 2>/dev/null || echo unknown) ($RESPEAK_PY_STD), PyYAML MISSING"
else
  python="none found"
fi

esc() { printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'; }
# The footer is posted publicly: never let it carry a home directory (a
# username). Anything under $HOME is shown as ~/...
tilde() { local t='~'; if [ -n "${HOME:-}" ]; then printf '%s' "${1//"$HOME"/$t}"; else printf '%s' "$1"; fi; }

if [ "${1:-}" = "--footer" ]; then
  printf -- '---\n_Environment_\n'
  printf -- '- respeak plugin: %s (%s)\n' "$version" "$plugin_sha"
  printf -- '- Claude Code: %s\n' "$claude_version"
  printf -- '- python3: %s\n' "$(tilde "$python")"
  printf -- '- OS: %s\n' "$os"
  exit 0
fi

if [ -n "$owner_repo" ]; then or_json="\"$(esc "$owner_repo")\""; else or_json="null"; fi
printf '{"owner_repo": %s, "version": "%s", "plugin_sha": "%s", "plugin_root": "%s", "claude_version": "%s", "python": "%s", "os": "%s"}\n' \
  "$or_json" "$(esc "$version")" "$(esc "$plugin_sha")" "$(esc "$plugin_root")" \
  "$(esc "$claude_version")" "$(esc "$python")" "$(esc "$os")"
exit 0
