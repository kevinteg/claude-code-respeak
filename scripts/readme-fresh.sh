#!/bin/bash
# Is README.md the render of design/readme/source.md? (conventions section 5)
#
# Usage: readme-fresh.sh [--repo DIR] [--stamp]
#
# Freshness is content, not mtime (git keeps no mtimes): `make readme` writes
# design/readme/rendered.sha256, two `shasum -a 256` lines (the source and the
# README, repo-relative). This script checks them, then proves the README a
# prose-only render of the source with respeak-verify-edit.py, so a README
# edited by hand and re-stamped still reads stale.
#   no source, no stamp  -> "readme: skipped, absent design/readme/source.md", exit 0
#   a stamp, no source   -> "readme: stale, a stamp without its source", exit 2
#   source over ceiling  -> "readme: source over the 24576-byte ceiling (N bytes)", exit 2
#   no stamp or mismatch -> "readme: stale, run make readme", exit 2
#   verifier fails       -> "readme: stale, README.md is not a prose-only render ...", exit 2
#   otherwise            -> "readme: fresh", exit 0
# --stamp writes the stamp from the current files instead, exit 0, and
# refuses (exit 2) unless the verifier passes and the source is under the
# ceiling. The verifier runs under $PYTHON (the Makefile exports it), else
# python3.
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

VERIFY="$(cd "$(dirname "$0")/.." && pwd)/plugin/scripts/respeak-verify-edit.py"
PY="${PYTHON:-python3}"
CEILING=24576
cd "$REPO" || { echo "readme-fresh: no directory $REPO" >&2; exit 2; }
SOURCE="design/readme/source.md"
STAMP="design/readme/rendered.sha256"

if [ ! -f "$SOURCE" ]; then
  if [ -f "$STAMP" ]; then
    echo "readme: stale, a stamp without its source ($STAMP names $SOURCE)"
    exit 2
  fi
  echo "readme: skipped, absent $SOURCE"
  exit 0
fi

size="$(wc -c < "$SOURCE" | tr -d ' ')"
if [ "$size" -gt "$CEILING" ]; then
  echo "readme: source over the $CEILING-byte ceiling ($size bytes); shorten $SOURCE"
  exit 2
fi

# Is README.md a prose-only render of the source? The same proof `make
# readme` runs before it stamps.
verified() {
  [ -f README.md ] || return 1
  [ -f "$VERIFY" ] || { echo "readme-fresh: no verifier at $VERIFY" >&2; return 1; }
  "$PY" "$VERIFY" "$SOURCE" README.md >/dev/null 2>&1
}

if [ "$STAMP_MODE" -eq 1 ]; then
  [ -f README.md ] || { echo "readme-fresh: no README.md to stamp" >&2; exit 2; }
  verified || { echo "readme-fresh: README.md is not a prose-only render of $SOURCE; not stamping" >&2; exit 2; }
  shasum -a 256 "$SOURCE" README.md > "$STAMP" || exit 2
  echo "readme: stamped $STAMP"
  exit 0
fi

if [ -f "$STAMP" ] && [ -f README.md ] && shasum -a 256 -c --status "$STAMP" 2>/dev/null; then
  if verified; then
    echo "readme: fresh"
    exit 0
  fi
  echo "readme: stale, README.md is not a prose-only render of $SOURCE (respeak-verify-edit.py); run make readme"
  exit 2
fi
echo "readme: stale, run make readme"
exit 2
