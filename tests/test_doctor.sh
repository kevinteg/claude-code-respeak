#!/bin/bash
# Tests for scripts/respeak-doctor.sh (`make doctor`): six lines, one per
# check, against a fake `claude` on a temporary PATH. Bash 3.2 compatible.
#
# Run: bash tests/test_doctor.sh
set -u

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$HERE/.." && pwd)"
DOCTOR="$REPO_ROOT/plugin/scripts/respeak-doctor.sh"

pass=0
fail=0
check() {
  # $1 = description, $2 = expected, $3 = actual
  if [ "$2" = "$3" ]; then pass=$((pass + 1)); echo "ok   - $1"
  else fail=$((fail + 1)); echo "FAIL - $1 (expected '$2', got '$3')"; fi
}

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
py="$("${PYTHON:-python3}" -c 'import sys; print(sys.executable)')"
pyver="$("$py" -c 'import sys; print("%d.%d.%d" % sys.version_info[:3])')"
manifest="$("$py" -c 'import json,sys; print(json.load(open(sys.argv[1]))["version"])' "$REPO_ROOT/plugin/.claude-plugin/plugin.json")"

mkdir -p "$work/bin" "$work/cfg/respeak" "$work/proj/.claude/respeak"
cat > "$work/bin/claude" <<'SH'
#!/bin/bash
case "$*" in
  "--version") echo "9.9.9 (Claude Code)" ;;
  "plugin marketplace list --json") echo '[{"name":"other","source":"github","repo":"x/y"},{"name":"claude-code-respeak","source":"directory","path":"/src/respeak"}]' ;;
  "plugin list --json") echo '[{"id":"respeak@claude-code-respeak","version":"0.6.0","scope":"user"}]' ;;
  *) exit 1 ;;
esac
SH
chmod +x "$work/bin/claude"
printf 'narrative: {default_mode: technical}\nno_such_key: 1\n' > "$work/proj/.claude/respeak/config.yaml"

run_doctor() { # $1 = PATH
  (cd "$work/proj" && env -u CLAUDE_PLUGIN_ROOT PATH="$1" HOME="$work" CLAUDE_CONFIG_DIR="$work/cfg" \
    CLAUDE_PROJECT_DIR="$work/proj" RESPEAK_PYTHON="$py" RESPEAK_CACHE_DIR="$work/cache" bash "$DOCTOR")
}

# 1. A fake claude answers: the six lines, exit 0.
out="$(run_doctor "$work/bin:$(dirname "$py"):/usr/bin:/bin")"; rc=$?
check "exits 0 with a PyYAML python" 0 "$rc"
check "six lines" 6 "$(printf '%s\n' "$out" | wc -l | tr -d ' ')"
check "python line" "python: $py $pyver pyyaml=yes" "$(printf '%s\n' "$out" | sed -n 1p)"
check "claude line" "claude: 9.9.9" "$(printf '%s\n' "$out" | sed -n 2p)"
check "marketplace line" "marketplace: claude-code-respeak directory /src/respeak" "$(printf '%s\n' "$out" | sed -n 3p)"
check "plugin line" "plugin: respeak@claude-code-respeak 0.6.0, manifest $manifest" "$(printf '%s\n' "$out" | sed -n 4p)"
check "provider line" 1 "$(printf '%s\n' "$out" | sed -n 5p | grep -c '^provider: ')"
check "config line counts the unknown key" "config: 1 unknown keys" "$(printf '%s\n' "$out" | sed -n 6p)"

# 2. No claude on PATH: claude missing, no marketplace, not installed; still exit 0.
mkdir -p "$work/nobin"
for t in bash dirname sed grep head cat env; do ln -s "$(command -v $t)" "$work/nobin/$t"; done
out="$(run_doctor "$work/nobin:$(dirname "$py")")"; rc=$?
check "exits 0 without claude" 0 "$rc"
check "claude: missing" "claude: missing" "$(printf '%s\n' "$out" | sed -n 2p)"
check "marketplace: none" "marketplace: none" "$(printf '%s\n' "$out" | sed -n 3p)"
check "plugin: not installed" "plugin: not installed" "$(printf '%s\n' "$out" | sed -n 4p)"

echo "$pass passed, $fail failed"
[ "$fail" -eq 0 ]
