#!/usr/bin/env python3
"""Verify a respeak (prose-only) edit changed nothing that carries meaning.

Usage: respeak-verify-edit.py <before> <after> [--type md|code|py|html|yaml|json] [--json]
       respeak-verify-edit.py --allow-strings before.py after.py

Format policies (what an edit MAY change / what must be invariant):

  md    prose may change; invariant: headings (text+order — anchors; ATX with
        or without the space after the hashes, and setext), block structure
        (per-kind counts of blockquote lines, list items, thematic breaks,
        table rows, definition lines), link and
        image targets, reference-link definitions, fenced code blocks (byte),
        inline code spans (multiset), numeric tokens outside fences (multiset),
        YAML front matter (byte), admonition types.
  code  (.ts .tsx .js .jsx .c .h .cpp .go .java .rs) comments may change;
        invariant: everything outside comments (byte), numeric tokens inside
        comments (multiset — numbers never change, per never_compress).
  py    # comments may change; invariant: all code including docstrings
        (docstrings can carry doctests, so they are code by default).
        --allow-strings opens the text inside string literals; see below.
  html  text nodes may change; invariant: tag skeleton with attributes,
        <script>/<style>/<pre>/<code> content (byte), numeric tokens in text
        (multiset).
  yaml  comments may change; invariant: parsed data (deep equality).
  json  whitespace only; invariant: parsed data.

--allow-restructure (md only): for passes run under `editorial_pass:
restructure: apply` (the caller owns relinking). Heading, block-structure,
admonition-type, and front-matter changes downgrade to reported warnings;
link targets, fenced code, inline code, and numbers stay hard invariants.

--allow-strings (py only): for an editorial pass over a page generator, whose
display text lives in string literals. Both files are parsed; with every str
constant masked, the two trees must dump identically, so a new dict entry, a
changed call, a moved statement, or a changed number still fails. A paired
string may then differ only with its numbers, %-placeholders, {} format
fields, URLs, Markdown link targets, and inline code spans intact, and a
docstring carrying a doctest (>>>) stays byte-identical.

Exit 0 = safe (warnings allowed), 1 = violation(s), 2 = usage/parse error.
Known limit: the `code` comment walker tracks ' " ` strings and //, /* */
comments; JS regex literals containing quote characters can confuse it — a
false FAIL, never a false PASS, since remainders are compared byte-for-byte.
"""
import argparse
import ast
import json
import re
import sys
from collections import Counter

CODE_EXTS = {".ts", ".tsx", ".js", ".jsx", ".c", ".h", ".cpp", ".cc", ".go", ".java", ".rs"}

# What a rewritten string still has to carry: the tokens a reader acts on.
PROSE_TOKENS = {
    "numbers": re.compile(r"\d+(?:[.,]\d+)?%?"),
    "%-placeholders": re.compile(r"%\(?\w*\)?[-#0 +]*\d*(?:\.\d+)?[sdifrxXeEgGc%]"),
    "format fields": re.compile(r"\{[^{}]*\}"),
    "URLs": re.compile(r"https?://\S+"),
    "link targets": re.compile(r"\]\(([^)\s]+)"),
    "inline code": re.compile(r"`[^`\n]+`"),
}
STRING_TOKEN_KINDS = tuple(PROSE_TOKENS)
SCALAR_TOKEN_KINDS = ("numbers", "URLs", "link targets", "inline code")


class Options:
    """Per-run switches the checkers honour; argparse's namespace also works."""

    def __init__(self, allow_restructure=False, allow_strings=False, prose_keys=None):
        self.allow_restructure = allow_restructure
        self.allow_strings = allow_strings
        self.prose_keys = prose_keys


DEFAULTS = Options()


def _opts(opts):
    return DEFAULTS if opts is None else opts


def numeric_tokens(text):
    return Counter(re.findall(r"\d+(?:[.,]\d+)?%?", text))


def counter_diff(name, before, after, problems):
    lost = before - after
    gained = after - before
    if lost or gained:
        problems.append(f"{name}: lost {dict(lost) or '{}'} gained {dict(gained) or '{}'}")


def token_diff(where, before, after, kinds, problems):
    """Report the meaning-carrying tokens a rewritten string lost or gained."""
    for kind in kinds:
        counter_diff(f"{where}: {kind}",
                     Counter(PROSE_TOKENS[kind].findall(before)),
                     Counter(PROSE_TOKENS[kind].findall(after)), problems)


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


def md_blocks(nofence):
    """Count the block constructs outside fences, by kind.

    Ordered items count anywhere when the marker is `1`, and only at a block
    start otherwise: CommonMark lets only `1.` interrupt a paragraph, and
    Python-Markdown starts a list at a block start. So a rewrap that moves
    "2." to the head of a continuation line changes nothing, and one that
    moves "1." there starts a list.
    """
    counts = Counter()
    at_block_start = True
    for line in nofence.split("\n"):
        if not line.strip():
            at_block_start = True
            continue
        if QUOTE_RE.match(line):
            counts["blockquote lines"] += 1
        if BULLET_RE.match(line):
            counts["bullet items"] += 1
        if ORDERED_ONE_RE.match(line) or (at_block_start and ORDERED_ANY_RE.match(line)):
            counts["ordered items"] += 1
        if at_block_start and HR_RE.match(line):
            counts["thematic breaks"] += 1
        if TABLE_ROW_RE.match(line):
            counts["table rows"] += 1
        if line.startswith(": "):
            counts["definition lines"] += 1
        at_block_start = False
    return counts


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
        "blocks": md_blocks(nofence),
        "link_targets": Counter(re.findall(r"\]\(([^)\s]+)(?:\s[^)]*)?\)", nofence)),
        "ref_defs": Counter(re.findall(r"^\[[^\]]+\]:\s*(\S+)", nofence, re.M)),
        "fences": fences,
        "inline_code": Counter(re.findall(r"`[^`\n]+`", nofence)),
        "admonition_types": re.findall(r'^(!!!|\?\?\?)\+? *(\w+)', nofence, re.M),
        "wikilinks": Counter(re.findall(r"\[\[([^\]|#]+)", nofence)),
        "numbers": numeric_tokens(nofence),
    }


def check_md(before, after, opts=None):
    b, a = md_facts(before), md_facts(after)
    problems = []
    if b["front_matter"] != a["front_matter"]:
        problems.append("front matter changed")
    if b["headings"] != a["headings"]:
        problems.append(f"headings changed: {[h for h in b['headings'] if h not in a['headings']] + [h for h in a['headings'] if h not in b['headings']]}")
    moved = [f"{kind} {b['blocks'][kind]} -> {a['blocks'][kind]}"
             for kind in sorted(set(b["blocks"]) | set(a["blocks"]))
             if b["blocks"][kind] != a["blocks"][kind]]
    if moved:
        problems.append("block structure changed: " + ", ".join(moved))
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


def check_code(before, after, opts=None):
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


def py_strings(tree):
    """Every str constant in walk order, plus the ids of the docstrings."""
    constants = [n for n in ast.walk(tree)
                 if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    docstrings = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                                 ast.AsyncFunctionDef)):
            continue
        body = node.body
        if (body and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)):
            docstrings.add(id(body[0].value))
    return constants, docstrings


def check_py_strings(before, after):
    """py under --allow-strings: only the prose inside string literals moves."""
    try:
        btree, atree = ast.parse(before), ast.parse(after)
    except SyntaxError as e:
        return [f"python parse error: {e}"]
    bnodes, bdocs = py_strings(btree)
    anodes, adocs = py_strings(atree)
    bvalues = [n.value for n in bnodes]
    avalues = [n.value for n in anodes]
    for node in bnodes + anodes:
        node.value = ""
    if ast.dump(btree, include_attributes=False) != ast.dump(atree, include_attributes=False):
        return ["python code changed (with every string masked the trees still differ: "
                "structure, a call, a number, or a new key)"]
    # The trees match, so the string constants pair up position by position.
    problems = []
    for i, (bval, aval) in enumerate(zip(bvalues, avalues)):
        if bval == aval:
            continue
        where = f"string at line {getattr(bnodes[i], 'lineno', '?')}"
        if (id(bnodes[i]) in bdocs or id(anodes[i]) in adocs) and (">>>" in bval or ">>>" in aval):
            problems.append(f"{where}: docstring carries a doctest; it must not change")
            continue
        token_diff(where, bval, aval, STRING_TOKEN_KINDS, problems)
    return problems


def check_py(before, after, opts=None):
    if _opts(opts).allow_strings:
        return check_py_strings(before, after)
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


def check_html(before, after, opts=None):
    b, a = html_facts(before), html_facts(after)
    problems = []
    if b.skeleton != a.skeleton:
        problems.append("tag skeleton or attributes changed")
    if b.protected != a.protected:
        problems.append("script/style/pre/code content changed")
    counter_diff("numeric tokens in text", b.text_numbers, a.text_numbers, problems)
    return problems


# --- yaml / json --------------------------------------------------------

def check_yaml(before, after, opts=None):
    import yaml
    try:
        if yaml.safe_load(before) != yaml.safe_load(after):
            return ["parsed YAML data changed (only comments/formatting may change)"]
    except yaml.YAMLError as e:
        return [f"YAML parse error: {e}"]
    return []


def check_json(before, after, opts=None):
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
RESTRUCTURE_RELAXED = ("headings changed", "block structure changed",
                       "admonition types changed", "front matter changed")


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


def verify_pair(before, after, ftype, opts):
    """Check one before/after pair. Returns (problems, warnings)."""
    problems = CHECKERS[ftype](before, after, opts)
    if _opts(opts).allow_restructure and ftype == "md":
        return partition_restructure(problems)
    return problems, []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("before")
    ap.add_argument("after")
    ap.add_argument("--type", choices=sorted(CHECKERS), default=None)
    ap.add_argument("--allow-restructure", action="store_true",
                    help="md only: heading/block/admonition/front-matter changes are warnings, not failures")
    ap.add_argument("--allow-strings", action="store_true",
                    help="py only: string literals may be rewritten if their numbers, placeholders, "
                         "format fields, URLs, link targets, and inline code survive")
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args()
    opts = Options(allow_restructure=args.allow_restructure,
                   allow_strings=args.allow_strings)

    ftype = args.type or detect(args.after)
    if ftype is None:
        print(f"respeak-verify-edit: unknown file type for {args.after}; pass --type", file=sys.stderr)
        sys.exit(2)

    before = open(args.before, encoding="utf-8").read()
    after = open(args.after, encoding="utf-8").read()
    problems, warnings = verify_pair(before, after, ftype, opts)

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
