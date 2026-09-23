#!/bin/bash
# Render the ratified-terms digest from the lexicon YAML.
# The digest (.claude/respeak/lexicon-active.md) is what CLAUDE.md imports —
# compact, ratified-only, regenerated on every ratification.
set -euo pipefail

LEX="${1:-.claude/respeak/lexicon.yaml}"
[ -f "$LEX" ] || LEX="${CLAUDE_PLUGIN_ROOT:-}/corpus/lexicon.yaml"
OUT="${2:-.claude/respeak/lexicon-active.md}"

python3 - "$LEX" "$OUT" <<'PY'
import re, sys

lex_path, out_path = sys.argv[1], sys.argv[2]
text = open(lex_path).read()

version = "0"
m = re.search(r"^version:\s*(\S+)", text, re.M)
if m:
    version = m.group(1)

# Parse entries without requiring PyYAML: split on "- term:" list items.
entries = []
for block in re.split(r"\n  - term:", text)[1:]:
    block = "term:" + block
    def field(name):
        fm = re.search(rf'^\s*{name}:\s*"?(.*?)"?\s*$', block, re.M)
        return fm.group(1) if fm else ""
    if field("status") == "ratified":
        entries.append((field("term"), field("expansion"), field("definition")))

with open(out_path, "w") as f:
    f.write(f"# Respeak ratified shorthand (lexicon v{version})\n\n")
    f.write("Only these terms may be used as shorthand in agent traffic. ")
    f.write("Anything else is written out in full. Never compress: error\n")
    f.write("messages, security findings, user quotes, numbers with units.\n\n")
    f.write("| term | expands to | meaning |\n|---|---|---|\n")
    for t, e, d in entries:
        f.write(f"| `{t}` | {e} | {d} |\n")

print(f"wrote {out_path}: {len(entries)} ratified terms (lexicon v{version})")
PY
