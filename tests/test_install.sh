#!/bin/bash
# Tests for `make install`: add when absent, update when the marketplace is
# this checkout, refuse (exit 2, nothing run) for any other source or a
# missing CLI. A fake `claude`, passed as CLAUDE=, records its argv; a
# decoy `claude` first on PATH records any call that bypassed the variable.
# Bash 3.2 compatible.
#
# Run: bash tests/test_install.sh
set -u

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$HERE/.." && pwd)"

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
mkdir -p "$work/bin"
cat > "$work/bin/claude" <<'SH'
#!/bin/bash
echo "$*" >> "$FAKE_LOG"
case "$*" in
  "plugin marketplace list --json") cat "$FAKE_MKT" ;;
esac
exit 0
SH
chmod +x "$work/bin/claude"
mkdir -p "$work/decoy"
printf '#!/bin/sh\necho "BARE claude $*" >> "$FAKE_LOG"\nexit 1\n' > "$work/decoy/claude"
chmod +x "$work/decoy/claude"

run_install() { # $1 = marketplace list JSON, $2 = the CLAUDE to pass (default the fake)
  printf '%s\n' "$1" > "$work/mkt.json"; : > "$work/log"
  FAKE_LOG="$work/log" FAKE_MKT="$work/mkt.json" PATH="$work/decoy:$PATH" \
    make -s -C "$REPO_ROOT" install PYTHON="$py" CLAUDE="${2:-$work/bin/claude}" > "$work/out" 2>&1
}
calls() { grep -v '^plugin marketplace list --json$' "$work/log" | tr '\n' ';'; }

# 1. No marketplace named claude-code-respeak: add this checkout, then install.
run_install '[{"name":"other","source":"directory","path":"/elsewhere"}]'; rc=$?
check "absent: exit 0" 0 "$rc"
check "absent: add, then install" "plugin marketplace add $REPO_ROOT;plugin install respeak@claude-code-respeak;" "$(calls)"

# 2. The marketplace is this checkout: update both.
run_install "[{\"name\":\"claude-code-respeak\",\"source\":\"directory\",\"path\":\"$REPO_ROOT\"}]"; rc=$?
check "this checkout: exit 0" 0 "$rc"
check "this checkout: update, then update" "plugin marketplace update claude-code-respeak;plugin update respeak@claude-code-respeak;" "$(calls)"

# 3. Any other source: print it and the owner's two commands; run nothing; exit 2.
run_install '[{"name":"claude-code-respeak","source":"github","repo":"example/fork"}]'; rc=$?
check "other source: exit 2" 2 "$rc"
check "other source: nothing but the list ran" "" "$(calls)"
check "other source: names the source" 1 "$(grep -c 'comes from example/fork' "$work/out")"
check "other source: prints the remove command" 1 "$(grep -c '^  claude plugin marketplace remove claude-code-respeak$' "$work/out")"

# 4. No claude CLI at CLAUDE: exit 2, name it, run nothing.
run_install '[]' "$work/bin/no-such-claude"; rc=$?
check "missing CLAUDE: exit 2" 2 "$rc"
check "missing CLAUDE: nothing ran" "" "$(cat "$work/log")"
check "missing CLAUDE: names it" 1 "$(grep -c "no claude CLI at CLAUDE=$work/bin/no-such-claude" "$work/out")"

echo "$pass passed, $fail failed"
[ "$fail" -eq 0 ]
