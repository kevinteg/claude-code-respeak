#!/usr/bin/env python3
"""Measure one or more Markdown documents against the respeak style gates.

Usage: respeak-measure.py <doc.md|-> [<doc2.md> ...]        ('-' = stdin, once)
                           [--corpus <banned-phrases.yaml>]
                           [--config <respeak.config.yaml>]
                           [--fail-on {none,error,warn}]
                           [--max-sentence-words N] [--json]

Reports banned-phrase hits (error / warn / density-tier), sentence-length
stats against the technical-mode caps, em-dash density, budget PASS/FAIL,
and word count, for each document given. Fenced code blocks, inline code,
and blockquotes are exempt (config style.quoting_exempt), and so are HTML
comments (`<!-- ... -->`): nothing inside one reaches the rendered page, so
a vendored banner must not spend the document's em-dash or phrase budget.
URLs (bare, autolinked, or the target of an inline link) are dropped before
anything is counted — an address is a target, not a word.
Zero API tokens — pure local scan, no network.

--fail-on {none,error,warn} (default none): exit 1 if any document trips a
hit (or, for warn, a budget failure) at or above that severity; exit 0
otherwise. `none` never fails — this keeps the pre-enforcement behavior for
callers that only want the report. Exit 2 is reserved for usage/IO errors
(bad doc path, unreadable corpus/config).

--config <path>: optional project or plugin config YAML.
  * `style.budgets` — checked against the measured stats and reported
    PASS/FAIL (see BUDGET_DEFAULTS below for the keys and defaults used when
    a key is absent from the config); a FAIL counts as a warn-level hit for
    --fail-on.
  * `gate.allow` — a list of regexes; any corpus rule whose defining
    `pattern`/`phrase` matches one of them is skipped entirely for this run.
    This is the per-project escape hatch for a domain term the corpus
    mis-flags (e.g. a networking-heavy project silencing a rule the shared
    `exceptions:` list does not yet cover), separate from the corpus's own
    per-entry `exceptions:` (below).

--baseline <path|->: scan that text with the same corpus and config and
  classify the document's hits against it. A rule's hits beyond the
  baseline's count for the same rule are "introduced"; the rest are
  pre-existing, reported but never counted by --fail-on. A failing budget
  counts only when its value rose above the baseline's. This is what the
  gate hook passes (`gate.block_on: introduced`), with the committed
  version of the file as the baseline, so an edit is blocked for what it
  adds, not for what the file already carried. Takes exactly one document.

Per-entry `exceptions:` (list of regexes, already in the corpus) exempt a
hit whose surrounding sentence also matches one of the entry's exceptions —
this is what lets "the spine switch" pass while "the spine of the argument"
still flags the project-banned metaphor.
"""
import argparse
import json
import os
import re
import sys

try:
    import yaml
except ImportError:
    sys.exit("respeak-measure: pyyaml required (pip install pyyaml)")


# Budget key -> default used when the key is absent from style.budgets in
# the resolved config. Each maps to one measured field in `result` below.
BUDGET_DEFAULTS = {
    "emdash_per_1000_words": 5,          # -> em_dashes_per_1000_words
    "warn_phrases_per_1000_words": 8,    # -> density_per_1000_words (tier: density hits)
    "avg_sentence_words": 20,            # -> avg_sentence_words
    "max_sentence_words": 35,            # -> max_sentence_words (distinct from the
                                          #    --max-sentence-words CLI cap, which only
                                          #    drives the sentences_over_N report field)
}

# Budget key -> the measured field it is checked against (the "->" above).
BUDGET_FIELDS = {
    "emdash_per_1000_words": "em_dashes_per_1000_words",
    "warn_phrases_per_1000_words": "density_per_1000_words",
    "avg_sentence_words": "avg_sentence_words",
    "max_sentence_words": "max_sentence_words",
}

# Severity ordering for --fail-on: a result's level must be >= the
# requested threshold's level for the run to fail.
FAIL_LEVELS = {"none": 0, "warn": 1, "error": 2}


def strip_exempt(text: str) -> str:
    text = re.sub(r"```.*?```", "", text, flags=re.S)   # fenced code
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)   # HTML comments
    text = re.sub(r"`[^`\n]+`", "", text)                # inline code
    text = re.sub(r"<https?://[^>]+>", "", text)         # autolinks
    # Bare URLs and the targets of inline links: an address is not prose, so
    # it has no words to count and no sentence to end. It stops at the
    # closing delimiter rather than at `\S+`, which would eat the `)` of
    # `[label](url)` and hide the link from sentences() below.
    text = re.sub(r"https?://[^\s)>\]]+", "", text)      # bare URLs, link targets
    text = re.sub(r"^>.*$", "", text, flags=re.M)        # blockquotes
    text = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.S)  # front matter
    text = re.sub(r"^!!!.*$", "", text, flags=re.M)      # mkdocs admonition markers
    return text


def sentences(text: str):
    prose = re.sub(r"^#+ .*$", "", text, flags=re.M)     # headings
    prose = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", prose)  # link targets
    prose = re.sub(r"^\s*[|].*$", "", prose, flags=re.M)  # tables
    for s in re.split(r"(?<=[.!?])\s+", prose):
        s = s.strip()
        if len(s.split()) >= 3:
            yield s


def sentence_window(text: str, start: int, end: int) -> str:
    """Cheap, local approximation of "the sentence containing text[start:end]",
    used only to test an entry's `exceptions:` regexes against local context.
    Not a real sentence tokenizer — bounded by the nearest .!? on either
    side (or the string edges), which is enough for short exception regexes
    like literal networking terms next to a banned metaphor phrase."""
    left = max((text.rfind(c, 0, start) for c in ".!?"), default=-1)
    right_candidates = [i for i in (text.find(c, end) for c in ".!?") if i != -1]
    right = min(right_candidates) if right_candidates else len(text) - 1
    return text[left + 1:right + 1]


def load_yaml(path):
    with open(path) as f:
        return yaml.safe_load(f) or {}


def rule_text(entry) -> str:
    return entry.get("pattern") or entry.get("phrase") or ""


class SetupError(Exception):
    """A problem with the inputs (corpus, config, or document), as opposed to
    a style-gate verdict. main() maps it to exit 2 so the gate hook fails
    open; exit 1 is reserved for a real verdict."""


def allowed_by_gate(entry, allow_regexes) -> bool:
    txt = rule_text(entry)
    return any(a.search(txt) for a in allow_regexes)


def validate_corpus(corpus, path):
    """Raise SetupError unless the corpus has the shape scan_doc needs."""
    cats = corpus.get("categories") if isinstance(corpus, dict) else None
    if not isinstance(cats, dict):
        raise SetupError(f"{path}: corpus has no 'categories' mapping")
    for cat, cdef in cats.items():
        entries = cdef.get("entries") if isinstance(cdef, dict) else None
        if not isinstance(entries, list):
            raise SetupError(f"{path}: category {cat!r} has no 'entries' list")
        for i, e in enumerate(entries):
            if not isinstance(e, dict) or not (e.get("pattern") or e.get("phrase")):
                raise SetupError(f"{path}: {cat}[{i}] needs a 'pattern' or 'phrase'")
            if e.get("severity") not in ("error", "warn", None):
                raise SetupError(f"{path}: {cat}[{i}] severity {e.get('severity')!r} is not error/warn")
            for field in ("pattern",):
                if e.get(field):
                    try:
                        re.compile(e[field], re.I | re.M)
                    except re.error as exc:
                        raise SetupError(f"{path}: {cat}[{i}] {field} {e[field]!r}: {exc}")
            for x in e.get("exceptions") or []:
                try:
                    re.compile(x, re.I | re.M)
                except re.error as exc:
                    raise SetupError(f"{path}: {cat}[{i}] exception {x!r}: {exc}")


def scan_doc(text: str, corpus, allow_regexes):
    """Return {"error": [...], "warn": [...], "density": [...]} hit buckets,
    honoring gate.allow (skip the rule entirely) and the entry's own
    exceptions: (skip a match whose surrounding sentence also matches)."""
    hits = {"error": [], "warn": [], "density": []}
    for cat, cdef in corpus["categories"].items():
        for e in cdef["entries"]:
            if allow_regexes and allowed_by_gate(e, allow_regexes):
                continue
            pat = e.get("pattern") or re.escape(e["phrase"])
            flags = re.I | re.M
            exc_res = [re.compile(x, flags) for x in e.get("exceptions", [])]
            count = 0
            for m in re.finditer(pat, text, flags):
                if exc_res:
                    window = sentence_window(text, m.start(), m.end())
                    if any(r.search(window) for r in exc_res):
                        continue
                count += 1
            if not count:
                continue
            bucket = "density" if e.get("tier") == "density" else e["severity"]
            hits[bucket].append({
                "category": cat,
                "rule": e.get("pattern", e.get("phrase")),
                "count": count,
            })
    return hits


def get_budgets(config):
    budgets = dict(BUDGET_DEFAULTS)
    if config:
        configured = ((config.get("style") or {}).get("budgets") or {})
        for k in BUDGET_DEFAULTS:
            if k in configured:
                budgets[k] = configured[k]
    return budgets


def get_allow(config):
    """gate.allow as compiled regexes; a bad one is a SetupError (a config
    problem), never a verdict."""
    if not config:
        return []
    raw = (config.get("gate") or {}).get("allow") or []
    if not isinstance(raw, list):
        raise SetupError(f"gate.allow must be a list, got {type(raw).__name__}")
    out = []
    for a in raw:
        try:
            out.append(re.compile(str(a)))
        except re.error as exc:
            raise SetupError(f"gate.allow entry {a!r} is not a valid regex: {exc}")
    return out


def check_budgets(result, budgets):
    out = {}
    for key, field in BUDGET_FIELDS.items():
        value, threshold = result[field], budgets[key]
        out[key] = {"value": value, "threshold": threshold,
                    "status": "PASS" if value <= threshold else "FAIL"}
    return out


def read_doc(doc_path):
    """Read a document as UTF-8 ('-' reads stdin, so a caller can gate text it
    holds without writing a temp file); anything else is an unreadable file (a
    SetupError), not a style verdict."""
    try:
        if doc_path == "-":
            return sys.stdin.buffer.read().decode("utf-8")
        with open(doc_path, encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError as e:
        raise SetupError(f"{doc_path}: not UTF-8 text ({e})")


def scan_text(text, corpus, allow_regexes, max_sentence_words):
    """Every measured field for one already-stripped text, minus the budget
    verdicts; measure() adds those, and the baseline deltas when asked."""
    hits = scan_doc(text, corpus, allow_regexes)

    sents = list(sentences(text))
    lens = [len(s.split()) for s in sents]
    over = [(l, s) for l, s in zip(lens, sents) if l > max_sentence_words]
    words = len(text.split())
    emdash = len(re.findall(r" — ", text))

    return {
        "words": words,
        "sentences": len(sents),
        "avg_sentence_words": round(sum(lens) / len(lens), 1) if lens else 0,
        "max_sentence_words": max(lens) if lens else 0,
        f"sentences_over_{max_sentence_words}": len(over),
        "em_dashes": emdash,
        "em_dashes_per_1000_words": round(1000 * emdash / words, 1) if words else 0,
        "error_hits": sum(h["count"] for h in hits["error"]),
        "warn_hits": sum(h["count"] for h in hits["warn"]),
        "density_hits": sum(h["count"] for h in hits["density"]),
        "density_per_1000_words": round(1000 * sum(h["count"] for h in hits["density"]) / words, 1) if words else 0,
        "detail": hits,
    }


def apply_baseline(result, baseline_path, corpus, allow_regexes, max_sentence_words):
    """Classify the document's hits against a baseline text. A rule's hits
    beyond the baseline's count for that rule are `introduced`; the rest are
    pre-existing and never trip --fail-on. A failing budget is `worsened`
    only when the measured value rose above the baseline's."""
    base = scan_text(strip_exempt(read_doc(baseline_path)), corpus, allow_regexes, max_sentence_words)
    base_counts = {(h["category"], h["rule"]): h["count"]
                   for sev in base["detail"] for h in base["detail"][sev]}
    result["baseline"] = "<stdin>" if baseline_path == "-" else baseline_path
    preexisting = 0
    for sev in ("error", "warn", "density"):
        for h in result["detail"][sev]:
            was = base_counts.get((h["category"], h["rule"]), 0)
            h["baseline"] = was
            h["introduced"] = max(0, h["count"] - was)
            preexisting += min(h["count"], was)
        result[f"introduced_{sev}_hits"] = sum(h["introduced"] for h in result["detail"][sev])
    result["preexisting_hits"] = preexisting
    for key, field in BUDGET_FIELDS.items():
        b = result["budgets"][key]
        b["baseline"] = base[field]
        b["worsened"] = b["status"] == "FAIL" and b["value"] > base[field]
    result["budget_failures_introduced"] = sum(1 for b in result["budgets"].values() if b["worsened"])


def measure(doc_path, corpus, config, max_sentence_words, baseline_path=None):
    text = strip_exempt(read_doc(doc_path))
    allow_regexes = get_allow(config)
    result = {"doc": "<stdin>" if doc_path == "-" else doc_path}
    result.update(scan_text(text, corpus, allow_regexes, max_sentence_words))
    budgets = get_budgets(config)
    result["budgets"] = check_budgets(result, budgets)
    result["budget_failures"] = sum(1 for b in result["budgets"].values() if b["status"] == "FAIL")
    if baseline_path is not None:
        apply_baseline(result, baseline_path, corpus, allow_regexes, max_sentence_words)
    return result


def result_level(result) -> str:
    """Highest --fail-on severity this result trips: error > warn > none.
    Against a baseline, only introduced hits and worsened budgets count."""
    if "baseline" in result:
        if result["introduced_error_hits"]:
            return "error"
        if (result["introduced_warn_hits"] or result["introduced_density_hits"]
                or result["budget_failures_introduced"]):
            return "warn"
        return "none"
    if result["error_hits"]:
        return "error"
    if result["warn_hits"] or result["density_hits"] or result["budget_failures"]:
        return "warn"
    return "none"


def print_result(result, max_sentence_words):
    over_key = f"sentences_over_{max_sentence_words}"
    print(f"{result['doc']}: {result['words']} words, {result['sentences']} sentences "
          f"(avg {result['avg_sentence_words']}w, max {result['max_sentence_words']}w, "
          f"{result[over_key]} over {max_sentence_words}w)")
    print(f"em-dashes: {result['em_dashes']} ({result['em_dashes_per_1000_words']}/1000w)")
    for sev in ("error", "warn", "density"):
        hits = result["detail"][sev]
        total = sum(h["count"] for h in hits)
        print(f"{sev}: {total} hits across {len(hits)} rules")
        for h in sorted(hits, key=lambda x: (-x.get("introduced", x["count"]), -x["count"]))[:12]:
            tag = ""
            if "baseline" in result:
                tag = f"  [new {h['introduced']}, pre-existing {min(h['count'], h['baseline'])}]"
            print(f"  {h['count']:3d}  [{h['category']}] {h['rule']}{tag}")
    print("budgets:")
    for name, b in result["budgets"].items():
        tag = ""
        if "baseline" in result:
            tag = f" (baseline {b['baseline']}{', worsened' if b['worsened'] else ''})"
        print(f"  {b['status']:4s}  {name}: {b['value']} (budget {b['threshold']}){tag}")
    if "baseline" in result:
        print(f"baseline: {result['preexisting_hits']} pre-existing hit(s) not counted; "
              f"introduced: {result['introduced_error_hits']} error, "
              f"{result['introduced_warn_hits']} warn, {result['introduced_density_hits']} density; "
              f"budgets worsened: {result['budget_failures_introduced']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("docs", nargs="+")
    ap.add_argument("--corpus", default=None)
    ap.add_argument("--config", default=None)
    ap.add_argument("--fail-on", choices=("none", "error", "warn"), default="none")
    ap.add_argument("--max-sentence-words", type=int, default=25)
    ap.add_argument("--baseline", default=None, metavar="PATH",
                    help="classify hits against this text; only hits beyond its per-rule "
                         "counts (and budgets that got worse) count for --fail-on")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    corpus_path = args.corpus or os.path.join(
        os.environ.get("CLAUDE_PLUGIN_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "corpus", "banned-phrases.yaml")

    # The report carries corpus rule text (curly quotes, dashes), so a
    # non-UTF-8 stdout must never turn a pass into a crash.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(errors="replace")
            except Exception:  # noqa: BLE001
                pass

    # Every failure that is not a style verdict exits 2, including ones
    # nobody anticipated: the gate hook reads exit 1 as "the document failed
    # the gate" and blocks the write, so an uncaught traceback (which CPython
    # exits 1 for) would turn a broken corpus into a blocked edit. Printing
    # sits inside the same guard for the same reason.
    try:
        corpus = load_yaml(corpus_path)
        validate_corpus(corpus, corpus_path)
        config = load_yaml(args.config) if args.config else None
        if config is not None and not isinstance(config, dict):
            raise SetupError(f"{args.config}: top level is not a mapping")
        if args.docs.count("-") > 1:
            raise SetupError("'-' (stdin) may be given once")
        if args.baseline is not None:
            if len(args.docs) != 1:
                raise SetupError("--baseline takes exactly one document")
            if args.baseline == "-" and args.docs[0] == "-":
                raise SetupError("'-' (stdin) may be given once")
        results = []
        for doc in args.docs:
            results.append(measure(doc, corpus, config, args.max_sentence_words,
                                   baseline_path=args.baseline))
        if args.json:
            print(json.dumps(results, indent=1))
        else:
            for i, r in enumerate(results):
                if i:
                    print()
                print_result(r, args.max_sentence_words)
    except (OSError, yaml.YAMLError, SetupError) as e:
        print(f"respeak-measure: {e}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:  # noqa: BLE001 — anything unexpected is a setup error, not a verdict
        print(f"respeak-measure: internal error ({type(e).__name__}: {e})", file=sys.stderr)
        sys.exit(2)

    if args.fail_on != "none":
        threshold = FAIL_LEVELS[args.fail_on]
        for r in results:
            if FAIL_LEVELS[result_level(r)] >= threshold:
                sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
