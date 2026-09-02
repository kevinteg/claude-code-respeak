#!/usr/bin/env python3
"""Measure one or more Markdown documents against the respeak style gates.

Usage: respeak-measure.py <doc.md> [<doc2.md> ...]
                           [--corpus <banned-phrases.yaml>]
                           [--config <respeak.config.yaml>]
                           [--fail-on {none,error,warn}]
                           [--max-sentence-words N] [--json]

Reports banned-phrase hits (error / warn / density-tier), sentence-length
stats against the technical-mode caps, em-dash density, budget PASS/FAIL,
and word count, for each document given. Fenced code blocks, inline code,
and blockquotes are exempt (config style.quoting_exempt). Zero API tokens —
pure local scan, no network.

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

Per-entry `exceptions:` (list of regexes, already in the corpus) exempt a
hit whose surrounding sentence also matches one of the entry's exceptions —
this is what lets "the spine switch" pass while "the spine of the argument"
still flags the owner-banned metaphor.
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

# Severity ordering for --fail-on: a result's level must be >= the
# requested threshold's level for the run to fail.
FAIL_LEVELS = {"none": 0, "warn": 1, "error": 2}


def strip_exempt(text: str) -> str:
    text = re.sub(r"```.*?```", "", text, flags=re.S)   # fenced code
    text = re.sub(r"`[^`\n]+`", "", text)                # inline code
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


def allowed_by_gate(entry, allow_regexes) -> bool:
    txt = rule_text(entry)
    return any(re.search(a, txt) for a in allow_regexes)


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
    if not config:
        return []
    return list((config.get("gate") or {}).get("allow") or [])


def check_budgets(result, budgets):
    def check(key, value):
        threshold = budgets[key]
        return {"value": value, "threshold": threshold,
                "status": "PASS" if value <= threshold else "FAIL"}

    return {
        "emdash_per_1000_words": check("emdash_per_1000_words", result["em_dashes_per_1000_words"]),
        "warn_phrases_per_1000_words": check("warn_phrases_per_1000_words", result["density_per_1000_words"]),
        "avg_sentence_words": check("avg_sentence_words", result["avg_sentence_words"]),
        "max_sentence_words": check("max_sentence_words", result["max_sentence_words"]),
    }


def measure(doc_path, corpus, config, max_sentence_words):
    raw = open(doc_path).read()
    text = strip_exempt(raw)
    allow_regexes = get_allow(config)
    hits = scan_doc(text, corpus, allow_regexes)

    sents = list(sentences(text))
    lens = [len(s.split()) for s in sents]
    over = [(l, s) for l, s in zip(lens, sents) if l > max_sentence_words]
    words = len(text.split())
    emdash = len(re.findall(r" — ", text))

    result = {
        "doc": doc_path,
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
    budgets = get_budgets(config)
    result["budgets"] = check_budgets(result, budgets)
    result["budget_failures"] = sum(1 for b in result["budgets"].values() if b["status"] == "FAIL")
    return result


def result_level(result) -> str:
    """Highest --fail-on severity this result trips: error > warn > none."""
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
        for h in sorted(hits, key=lambda x: -x["count"])[:12]:
            print(f"  {h['count']:3d}  [{h['category']}] {h['rule']}")
    print("budgets:")
    for name, b in result["budgets"].items():
        print(f"  {b['status']:4s}  {name}: {b['value']} (budget {b['threshold']})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("docs", nargs="+")
    ap.add_argument("--corpus", default=None)
    ap.add_argument("--config", default=None)
    ap.add_argument("--fail-on", choices=("none", "error", "warn"), default="none")
    ap.add_argument("--max-sentence-words", type=int, default=25)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    corpus_path = args.corpus or os.path.join(
        os.environ.get("CLAUDE_PLUGIN_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "corpus", "banned-phrases.yaml")

    try:
        corpus = load_yaml(corpus_path)
        config = load_yaml(args.config) if args.config else None
    except (OSError, yaml.YAMLError) as e:
        print(f"respeak-measure: {e}", file=sys.stderr)
        sys.exit(2)

    results = []
    for doc in args.docs:
        try:
            results.append(measure(doc, corpus, config, args.max_sentence_words))
        except OSError as e:
            print(f"respeak-measure: {e}", file=sys.stderr)
            sys.exit(2)

    if args.json:
        print(json.dumps(results, indent=1))
    else:
        for i, r in enumerate(results):
            if i:
                print()
            print_result(r, args.max_sentence_words)

    if args.fail_on != "none":
        threshold = FAIL_LEVELS[args.fail_on]
        for r in results:
            if FAIL_LEVELS[result_level(r)] >= threshold:
                sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
