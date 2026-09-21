#!/usr/bin/env python3
"""Verify a respeak (prose-only) edit changed nothing that carries meaning.

Usage: respeak-verify-edit.py <before> <after> [--type md|code|py|html|yaml|json] [--json]

Format policies (what an edit MAY change / what must be invariant):

  md    prose may change; invariant: headings (text+order — anchors; ATX with
        or without the space after the hashes, and setext), link and
        image targets, reference-link definitions, fenced code blocks (byte),
        inline code spans (multiset), numeric tokens outside fences (multiset),
        YAML front matter (byte), admonition types.
  code  (.ts .tsx .js .jsx .c .h .cpp .go .java .rs) comments may change;
        invariant: everything outside comments (byte), numeric tokens inside
        comments (multiset — numbers never change, per never_compress).
  py    # comments may change; invariant: all code including docstrings
        (docstrings can carry doctests, so they are code by default).
  html  text nodes may change; invariant: tag skeleton with attributes,
        <script>/<style>/<pre>/<code> content (byte), numeric tokens in text
        (multiset).
  yaml  comments may change; invariant: parsed data (deep equality).
  json  whitespace only; invariant: parsed data.

--allow-restructure (md only): for passes run under `editorial_pass:
restructure: apply` (the caller owns relinking). Heading, admonition-type,
and front-matter changes downgrade to reported warnings; link targets,
fenced code, inline code, and numbers stay hard invariants.

Exit 0 = safe (warnings allowed), 1 = violation(s), 2 = usage/parse error.
Known limit: the `code` comment walker tracks ' " ` strings and //, /* */
comments; JS regex literals containing quote characters can confuse it — a
false FAIL, never a false PASS, since remainders are compared byte-for-byte.
"""
import argparse
import json
import re
import sys
from collections import Counter

CODE_EXTS = {".ts", ".tsx", ".js", ".jsx", ".c", ".h", ".cpp", ".cc", ".go", ".java", ".rs"}


def numeric_tokens(text):
    return Counter(re.findall(r"\d+(?:[.,]\d+)?%?", text))


def counter_diff(name, before, after, problems):
    lost = before - after
    gained = after - before
    if lost or gained:
        problems.append(f"{name}: lost {dict(lost) or '{}'} gained {dict(gained) or '{}'}")


# --- markdown -----------------------------------------------------------

FENCE_RE = re.compile(r"^(?:```|~~~).*?^(?:```|~~~)\s*$", re.S | re.M)
# A construct that is a heading in EITHER flavour is a heading here.
# Python-Markdown (what MkDocs runs) makes any line opening with a hash run a
# heading, space or no space; CommonMark wants the space but allows three
# leading ones. A hash the author escaped with a backslash never matches.
ATX_RE = re.compile(r"^ {0,3}#{1,6}")
SETEXT_RE = re.compile(r"^ {0,3}(=+|-+) *$")
QUOTE_RE = re.compile(r"^ {0,3}>")
BULLET_RE = re.compile(r"^\s*[-*+] ")
ORDERED_ONE_RE = re.compile(r"^\s*1[.)] ")
ORDERED_ANY_RE = re.compile(r"^\s*\d+[.)] ")
HR_RE = re.compile(r"^ {0,3}([-*_])( *\1){2,} *$")
TABLE_ROW_RE = re.compile(r"^\s*\|")


def setext_text(line):
    """True if `line` could be the text of a setext heading."""
    if not line.strip():
        return False
    return not (ATX_RE.match(line) or QUOTE_RE.match(line) or BULLET_RE.match(line)
                or ORDERED_ANY_RE.match(line) or TABLE_ROW_RE.match(line)
                or SETEXT_RE.match(line) or HR_RE.match(line))


def md_headings(nofence):
    """Headings outside fences, as an ordered list of their text.

    Setext headings carry the underline's character (which sets the level),
    not its length, so a rewrapped underline is not a change.
    """
    lines = nofence.split("\n")
    headings = []
    for i, line in enumerate(lines):
        if ATX_RE.match(line):
            headings.append(line.rstrip())
            continue
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        if SETEXT_RE.match(nxt) and setext_text(line):
            headings.append(line.rstrip() + "\n" + nxt.strip()[0])
    return headings


def md_facts(text):
    fm = ""
    m = re.match(r"^---\n.*?\n---\n", text, re.S)
    if m:
        fm = m.group(0)
        text = text[m.end():]
    fences = FENCE_RE.findall(text)
    # A blank line in place of each fence keeps neighbouring lines apart, so
    # a stripped fence cannot manufacture a setext pair or a block start.
    nofence = FENCE_RE.sub("\n\n", text)
    return {
        "front_matter": fm,
        "headings": md_headings(nofence),
        "link_targets": Counter(re.findall(r"\]\(([^)\s]+)(?:\s[^)]*)?\)", nofence)),
        "ref_defs": Counter(re.findall(r"^\[[^\]]+\]:\s*(\S+)", nofence, re.M)),
        "fences": fences,
        "inline_code": Counter(re.findall(r"`[^`\n]+`", nofence)),
        "admonition_types": re.findall(r'^(!!!|\?\?\?)\+? *(\w+)', nofence, re.M),
        "wikilinks": Counter(re.findall(r"\[\[([^\]|#]+)", nofence)),
        "numbers": numeric_tokens(nofence),
    }


def check_md(before, after):
    b, a = md_facts(before), md_facts(after)
    problems = []
    if b["front_matter"] != a["front_matter"]:
        problems.append("front matter changed")
    if b["headings"] != a["headings"]:
        problems.append(f"headings changed: {[h for h in b['headings'] if h not in a['headings']] + [h for h in a['headings'] if h not in b['headings']]}")
    counter_diff("link targets", b["link_targets"], a["link_targets"], problems)
    counter_diff("reference-link defs", b["ref_defs"], a["ref_defs"], problems)
    if b["fences"] != a["fences"]:
        problems.append(f"fenced code blocks changed ({len(b['fences'])} -> {len(a['fences'])} or content differs)")
    counter_diff("inline code spans", b["inline_code"], a["inline_code"], problems)
    counter_diff("wikilink targets", b["wikilinks"], a["wikilinks"], problems)
    if b["admonition_types"] != a["admonition_types"]:
        problems.append("admonition types changed")
    counter_diff("numeric tokens", b["numbers"], a["numbers"], problems)
    return problems


# --- C-family / JS / TS -------------------------------------------------

def split_code_comments(text):
    """Return (code_without_comments, comment_text). Tracks ' \" ` strings."""
    code, comments = [], []
    i, n = 0, len(text)
    state = None  # None | "'" | '"' | '`' | 'line' | 'block'
    while i < n:
        c = text[i]
        nxt = text[i + 1] if i + 1 < n else ""
        if state is None:
            if c == "/" and nxt == "/":
                state = "line"; comments.append("//"); i += 2; continue
            if c == "/" and nxt == "*":
                state = "block"; comments.append("/*"); i += 2; continue
            if c in ("'", '"', "`"):
                state = c
            code.append(c); i += 1; continue
        if state in ("'", '"', "`"):
            code.append(c)
            if c == "\\":
                if i + 1 < n:
                    code.append(text[i + 1]); i += 2; continue
            elif c == state:
                state = None
            i += 1; continue
        if state == "line":
            if c == "\n":
                state = None; code.append(c)
            else:
                comments.append(c)
            i += 1; continue
        if state == "block":
            if c == "*" and nxt == "/":
                state = None; comments.append("*/"); i += 2; continue
            comments.append(c); i += 1; continue
    return "".join(code), "".join(comments)


def check_code(before, after):
    bc, bm = split_code_comments(before)
    ac, am = split_code_comments(after)
    problems = []
    if bc != ac:
        for i, (x, y) in enumerate(zip(bc.splitlines(), ac.splitlines())):
            if x != y:
                problems.append(f"non-comment code changed (first at stripped line {i+1}): {x!r} -> {y!r}")
                break
        else:
            problems.append("non-comment code changed (length differs)")
    counter_diff("numeric tokens in comments", numeric_tokens(bm), numeric_tokens(am), problems)
    return problems


# --- python -------------------------------------------------------------

def strip_py_comments(text):
    out = []
    state = None  # None | quote char(s)
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if state is None:
            if c == "#":
                while i < n and text[i] != "\n":
                    i += 1
                continue
            for q in ('"""', "'''", '"', "'"):
                if text.startswith(q, i):
                    state = q; out.append(q); i += len(q); break
            else:
                out.append(c); i += 1
            continue
        if c == "\\" and len(state) == 1:
            out.append(text[i:i+2]); i += 2; continue
        if text.startswith(state, i):
            out.append(state); i += len(state); state = None; continue
        out.append(c); i += 1
    return "".join(out)


def check_py(before, after):
    problems = []
    if strip_py_comments(before) != strip_py_comments(after):
        problems.append("non-comment python changed (code or docstrings)")
    return problems


# --- html ---------------------------------------------------------------

def html_facts(text):
    from html.parser import HTMLParser

    class P(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=False)
            self.skeleton = []
            self.protected = []
            self.text_numbers = Counter()
            self._stack = []
        def handle_starttag(self, tag, attrs):
            self.skeleton.append((tag, tuple(sorted(attrs))))
            self._stack.append(tag)
        def handle_endtag(self, tag):
            self.skeleton.append(("/" + tag,))
            if self._stack and self._stack[-1] == tag:
                self._stack.pop()
        def handle_data(self, data):
            if any(t in ("script", "style", "pre", "code") for t in self._stack):
                self.protected.append(data)
            else:
                self.text_numbers.update(numeric_tokens(data))

    p = P()
    p.feed(text)
    return p


def check_html(before, after):
    b, a = html_facts(before), html_facts(after)
    problems = []
    if b.skeleton != a.skeleton:
        problems.append("tag skeleton or attributes changed")
    if b.protected != a.protected:
        problems.append("script/style/pre/code content changed")
    counter_diff("numeric tokens in text", b.text_numbers, a.text_numbers, problems)
    return problems


# --- yaml / json --------------------------------------------------------

def check_yaml(before, after):
    import yaml
    try:
        if yaml.safe_load(before) != yaml.safe_load(after):
            return ["parsed YAML data changed (only comments/formatting may change)"]
    except yaml.YAMLError as e:
        return [f"YAML parse error: {e}"]
    return []


def check_json(before, after):
    try:
        if json.loads(before) != json.loads(after):
            return ["parsed JSON data changed"]
    except json.JSONDecodeError as e:
        return [f"JSON parse error: {e}"]
    return []


# --- driver -------------------------------------------------------------

CHECKERS = {"md": check_md, "code": check_code, "py": check_py,
            "html": check_html, "yaml": check_yaml, "json": check_json}

# Problem classes that a restructure-permitted pass may change (md only).
RESTRUCTURE_RELAXED = ("headings changed", "admonition types changed",
                       "front matter changed")


def partition_restructure(problems):
    """Split md problems into (hard, warnings) under --allow-restructure."""
    hard = [p for p in problems if not p.startswith(RESTRUCTURE_RELAXED)]
    warnings = [p for p in problems if p.startswith(RESTRUCTURE_RELAXED)]
    return hard, warnings


def detect(path):
    ext = "." + path.rsplit(".", 1)[-1].lower() if "." in path else ""
    if ext in (".md", ".markdown"):
        return "md"
    if ext in CODE_EXTS:
        return "code"
    if ext == ".py":
        return "py"
    if ext in (".html", ".htm"):
        return "html"
    if ext in (".yaml", ".yml"):
        return "yaml"
    if ext == ".json":
        return "json"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("before")
    ap.add_argument("after")
    ap.add_argument("--type", choices=sorted(CHECKERS), default=None)
    ap.add_argument("--allow-restructure", action="store_true",
                    help="md only: heading/admonition/front-matter changes are warnings, not failures")
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args()

    ftype = args.type or detect(args.after)
    if ftype is None:
        print(f"respeak-verify-edit: unknown file type for {args.after}; pass --type", file=sys.stderr)
        sys.exit(2)

    before = open(args.before, encoding="utf-8").read()
    after = open(args.after, encoding="utf-8").read()
    problems = CHECKERS[ftype](before, after)
    warnings = []
    if args.allow_restructure and ftype == "md":
        problems, warnings = partition_restructure(problems)

    if args.as_json:
        print(json.dumps({"type": ftype, "safe": not problems,
                          "problems": problems, "warnings": warnings}))
    else:
        if problems:
            print(f"FAIL ({ftype}): {len(problems)} invariant violation(s)")
            for p in problems:
                print(f"  - {p}")
        else:
            print(f"PASS ({ftype}): edit is prose-only; all meaning-carrying content invariant")
        for w in warnings:
            print(f"  warning (restructure permitted): {w}")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
