#!/bin/bash
# Tests for scripts/report-env.sh — the /respeak:report issue target and
# environment footer. Bash 3.2 compatible (macOS default).
#
# Run: bash tests/test_report_env.sh
set -u

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$HERE/.." && pwd)"
ENV_SH="$REPO_ROOT/scripts/report-env.sh"

pass=0
fail=0
check() {
  # $1 = description, $2 = expected, $3 = actual
  if [ "$2" = "$3" ]; then pass=$((pass + 1)); echo "ok   - $1"
  else fail=$((fail + 1)); echo "FAIL - $1 (expected '$2', got '$3')"; fi
}
jget() { # $1 = json, $2 = key -> value, or "null"
  printf '%s' "$1" | "${PYTHON:-python3}" -c 'import json,sys; v=json.load(sys.stdin).get(sys.argv[1]); print("null" if v is None else v)' "$2"
}

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

# 1. Real plugin: valid JSON, owner_repo from the manifest, version matches.
out="$(bash "$ENV_SH")"; rc=$?
check "exits 0 against the real plugin" 0 "$rc"
check "owner_repo parsed from the https URL" "kevinteg/claude-code-respeak" "$(jget "$out" owner_repo)"
want_version="$("${PYTHON:-python3}" -c 'import json,sys; print(json.load(open(sys.argv[1]))["version"])' "$REPO_ROOT/.claude-plugin/plugin.json")"
check "version matches plugin.json" "$want_version" "$(jget "$out" version)"
check "plugin_root is the repo" "$REPO_ROOT" "$(jget "$out" plugin_root)"

# 2. Footer form.
footer="$(bash "$ENV_SH" --footer)"
check "footer has the environment heading" 1 "$(printf '%s\n' "$footer" | grep -c '^_Environment_$')"
check "footer names the plugin version" 1 "$(printf '%s\n' "$footer" | grep -c "^- respeak plugin: $want_version ")"
check "footer has an OS line" 1 "$(printf '%s\n' "$footer" | grep -c '^- OS: ')"

# 3. SSH-style repository URL, via CLAUDE_PLUGIN_ROOT.
mkdir -p "$work/ssh/.claude-plugin"
printf '{"name":"x","version":"9.9.9","repository":"git@github.com:someone/their-fork.git"}\n' > "$work/ssh/.claude-plugin/plugin.json"
out="$(CLAUDE_PLUGIN_ROOT="$work/ssh" bash "$ENV_SH")"
check "ssh URL parses to owner/repo" "someone/their-fork" "$(jget "$out" owner_repo)"
check "version read from the overridden root" "9.9.9" "$(jget "$out" version)"

# 4. No repository field: owner_repo is null, still exit 0.
mkdir -p "$work/none/.claude-plugin"
printf '{"name":"x","version":"1.0.0"}\n' > "$work/none/.claude-plugin/plugin.json"
out="$(CLAUDE_PLUGIN_ROOT="$work/none" bash "$ENV_SH")"; rc=$?
check "missing repository still exits 0" 0 "$rc"
check "missing repository gives null owner_repo" "null" "$(jget "$out" owner_repo)"

# 5. Missing manifest entirely.
out="$(CLAUDE_PLUGIN_ROOT="$work/nowhere" bash "$ENV_SH")"; rc=$?
check "missing manifest still exits 0" 0 "$rc"
check "missing manifest gives version unknown" "unknown" "$(jget "$out" version)"

# 6. Degraded PATH (no gh, no claude): still valid JSON with unknowns.
out="$(PATH=/usr/bin:/bin bash "$ENV_SH")"; rc=$?
check "degraded PATH exits 0" 0 "$rc"
check "degraded PATH still yields JSON" "kevinteg/claude-code-respeak" "$(jget "$out" owner_repo)"
cv="$(jget "$out" claude_version)"; [ -n "$cv" ] && cv=nonempty
check "claude_version is never empty" nonempty "$cv"

# 7. The footer never carries a home directory: a python under $HOME shows as ~/...
# A symlinked python under a fake HOME, given a stub `yaml` module on PYTHONPATH so the
# override is accepted whether or not this machine has PyYAML installed.
fakehome="$work/home"; mkdir -p "$fakehome/bin" "$fakehome/lib"; ln -s "$(command -v "${PYTHON:-python3}")" "$fakehome/bin/python3"; : > "$fakehome/lib/yaml.py"
footer="$(HOME="$fakehome" PYTHONPATH="$fakehome/lib" RESPEAK_PYTHON="$fakehome/bin/python3" RESPEAK_CACHE_DIR="$work/cache7" bash "$ENV_SH" --footer)"
check "footer shows a home-directory python as ~/..." 1 "$(printf '%s\n' "$footer" | grep -c -- '- python3: .*(~/bin/python3)')"
check "footer contains no literal home path" 0 "$(printf '%s\n' "$footer" | grep -c -F -- "$fakehome")"

echo "$pass passed, $fail failed"
[ "$fail" -eq 0 ]
