#!/bin/bash
# Render README.md from design/readme/source.md (conventions section 6);
# `make readme` calls this.
#
# Usage: readme-render.sh [--repo DIR] [--plugin-root DIR]
#
# The render goes to a temp file first, with design/readme/contract.txt as
# the render's contract. Only when the renderer passed its style gate and
# respeak-verify-edit.py proves the render prose-only against the source
# does it move over README.md, and then readme-fresh.sh stamps both.
#   0  README.md written and stamped
#   1  the render still failed the style gate; README.md untouched
#   2  setup, the renderer's refusals, or the verifier; README.md untouched
# The verifier runs under $PYTHON (the Makefile exports it), else python3.
#
# bash 3.2 compatible.
set -u

here="$(cd "$(dirname "$0")" && pwd)"
REPO="."
PLUGIN_ROOT="$(cd "$here/.." && pwd)/plugin"
while [ $# -gt 0 ]; do
  case "$1" in
    --repo) [ $# -ge 2 ] || { echo "readme-render: --repo needs a directory" >&2; exit 2; }; REPO="$2"; shift 2 ;;
    --plugin-root) [ $# -ge 2 ] || { echo "readme-render: --plugin-root needs a directory" >&2; exit 2; }; PLUGIN_ROOT="$2"; shift 2 ;;
    *) echo "readme-render: unknown argument $1" >&2; exit 2 ;;
  esac
done
PY="${PYTHON:-python3}"
REPO="$(cd "$REPO" 2>/dev/null && pwd)" || { echo "readme-render: no directory $REPO" >&2; exit 2; }
SOURCE="design/readme/source.md"
CONTRACT="design/readme/contract.txt"
for f in "$REPO/$SOURCE" "$REPO/$CONTRACT" "$PLUGIN_ROOT/scripts/respeak-render.sh" "$PLUGIN_ROOT/scripts/respeak-verify-edit.py"; do
  [ -f "$f" ] || { echo "readme-render: missing $f" >&2; exit 2; }
done
cd "$REPO" || exit 2

# The temp directory sits in the repository so the render resolves the
# same layered configuration README.md would.
tmpd="$(mktemp -d "$REPO/.readme-render.XXXXXX" 2>/dev/null)" || { echo "readme-render: mktemp failed" >&2; exit 2; }
trap 'rm -rf "$tmpd"' EXIT
out="$tmpd/README.md"

bash "$PLUGIN_ROOT/scripts/respeak-render.sh" --mode technical --source "$SOURCE" --out "$out" --contract "$CONTRACT"
rc=$?
if [ "$rc" -ne 0 ]; then
  echo "readme-render: the render exited $rc; README.md untouched" >&2
  [ "$rc" -eq 1 ] && exit 1
  exit 2
fi
if ! "$PY" "$PLUGIN_ROOT/scripts/respeak-verify-edit.py" "$SOURCE" "$out"; then
  echo "readme-render: the render is not prose-only against $SOURCE; README.md untouched" >&2
  exit 2
fi
mv "$out" README.md || exit 2
bash "$here/readme-fresh.sh" --stamp || exit 2
