#!/bin/bash
# respeak-doctor.sh: one line per check, for `make doctor` and a bug report.
#
#   python: <path> <version> pyyaml=<yes|no>
#   claude: <version>                                   | claude: missing
#   marketplace: claude-code-respeak <source> <path>    | marketplace: none
#   plugin: respeak@claude-code-respeak <v>, manifest <v> | plugin: not installed
#   provider: ...        (the line `respeak-config.sh explain --for README.md` prints)
#   config: <n> unknown keys   (user, project and project-local files; never fatal)
#
# Exit 0, or 2 when no python3 can import PyYAML (every hook is then a no-op).
# Reads only: the plugin's own files, `claude --version`, and the two
# `claude plugin ... --json` lists. Writes nothing. bash 3.2 compatible.
set -u

script_dir="$(cd "$(dirname "$0")" && pwd)"
root="${CLAUDE_PLUGIN_ROOT:-$(cd "$script_dir/.." && pwd)}"
. "$script_dir/respeak-python.sh"
py="${RESPEAK_PY:-${RESPEAK_PY_STD:-}}"
rc=0

# python
if [ -n "$py" ]; then
  ver="$("$py" -c 'import sys; print("%d.%d.%d" % sys.version_info[:3])' 2>/dev/null)"
  path="$("$py" -c 'import sys; print(sys.executable)' 2>/dev/null)"
  if [ -n "${RESPEAK_PY:-}" ]; then yaml=yes; else yaml=no; rc=2; fi
  echo "python: ${path:-$py} ${ver:-unknown} pyyaml=$yaml"
else
  echo "python: missing pyyaml=no"
  rc=2
fi

# json_field <python expression over d> : reads JSON on stdin, prints the result or nothing
json_field() {
  [ -n "$py" ] || return 0
  "$py" -c 'import json, sys
try:
    d = json.load(sys.stdin)
    r = eval(sys.argv[1])
except Exception:
    r = None
if r:
    print(r)' "$1" 2>/dev/null
}

# claude, marketplace, plugin
if command -v claude >/dev/null 2>&1; then
  cver="$(claude --version 2>/dev/null | head -n 1)"
  echo "claude: ${cver%% *}"
  mkt="$(claude plugin marketplace list --json 2>/dev/null | json_field \
    '" ".join(str(x) for x in next((m.get("source", "?"), m.get("path") or m.get("repo") or m.get("url") or m.get("installLocation", "?")) for m in d if m.get("name") == "claude-code-respeak"))')"
  if [ -n "$mkt" ]; then echo "marketplace: claude-code-respeak $mkt"; else echo "marketplace: none"; fi
  inst="$(claude plugin list --json 2>/dev/null | json_field \
    'next(str(p.get("version", "?")) for p in d if p.get("id") == "respeak@claude-code-respeak")')"
else
  echo "claude: missing"
  echo "marketplace: none"
  inst=""
fi
if [ -n "$inst" ]; then
  mver="$(json_field 'd.get("version")' < "$root/.claude-plugin/plugin.json")"
  echo "plugin: respeak@claude-code-respeak $inst, manifest ${mver:-unknown}"
else
  echo "plugin: not installed"
fi

# provider, config
if [ -n "${RESPEAK_PY:-}" ]; then
  prov="$(CLAUDE_PLUGIN_ROOT="$root" bash "$script_dir/respeak-config.sh" explain --for README.md 2>/dev/null | grep -m 1 '^provider:')"
  echo "${prov:-provider: unknown}"
  cfgdir="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
  proj="${CLAUDE_PROJECT_DIR:-$PWD}"
  files=""
  for f in "$cfgdir/respeak/config.yaml" "$proj/.claude/respeak/config.yaml" "$proj/.claude/respeak/config.local.yaml"; do
    [ -f "$f" ] && files="$files
$f"
  done
  n=0
  if [ -n "$files" ]; then
    n="$(printf '%s\n' "$files" | sed '/^$/d' | while IFS= read -r f; do
      "$RESPEAK_PY" "$script_dir/respeak-config.py" validate --plugin-root "$root" "$f" 2>/dev/null
    done | grep -c 'unknown top-level key')"
  fi
  echo "config: ${n:-0} unknown keys"
else
  echo "provider: unknown (no python3 with PyYAML)"
  echo "config: unknown (no python3 with PyYAML)"
fi

exit $rc
