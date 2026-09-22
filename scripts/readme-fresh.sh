#!/bin/bash
# Is README.md the render of design/readme/source.md? (conventions section 5)
#
# Usage: readme-fresh.sh [--repo DIR] [--stamp]
#
# Freshness is content, not mtime (git keeps no mtimes): `make readme` writes
# design/readme/rendered.sha256, two `shasum -a 256` lines (the source and the
# README, repo-relative). This script checks them.
#   no source            -> "readme: skipped, absent design/readme/source.md", exit 0
#   no stamp or mismatch -> "readme: stale, run make readme", exit 2
#   otherwise            -> "readme: fresh", exit 0
# --stamp writes the stamp from the current files instead, exit 0.
#
# bash 3.2 compatible.
set -u

REPO="."
STAMP_MODE=0
while [ $# -gt 0 ]; do
  case "$1" in
    --repo) REPO="$2"; shift 2 ;;
    --stamp) STAMP_MODE=1; shift ;;
    *) echo "readme-fresh: unknown argument $1" >&2; exit 2 ;;
  esac
done

cd "$REPO" || { echo "readme-fresh: no directory $REPO" >&2; exit 2; }
SOURCE="design/readme/source.md"
STAMP="design/readme/rendered.sha256"

if [ ! -f "$SOURCE" ]; then
  echo "readme: skipped, absent $SOURCE"
  exit 0
fi

if [ "$STAMP_MODE" -eq 1 ]; then
  [ -f README.md ] || { echo "readme-fresh: no README.md to stamp" >&2; exit 2; }
  shasum -a 256 "$SOURCE" README.md > "$STAMP" || exit 2
  echo "readme: stamped $STAMP"
  exit 0
fi

if [ -f "$STAMP" ] && [ -f README.md ] && shasum -a 256 -c --status "$STAMP" 2>/dev/null; then
  echo "readme: fresh"
  exit 0
fi
echo "readme: stale, run make readme"
exit 2
