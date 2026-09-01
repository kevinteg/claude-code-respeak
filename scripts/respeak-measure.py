#!/usr/bin/env python3
"""Measure a Markdown document against the respeak style gates.

Usage: respeak-measure.py <doc.md> [--corpus <banned-phrases.yaml>] [--json]

Reports banned-phrase hits (error / warn / density-tier), sentence-length
stats against the technical-mode caps, em-dash density, and word count.
Fenced code blocks, inline code, and blockquotes are exempt
(config style.quoting_exempt). Zero API tokens — pure local scan.
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("doc")
    ap.add_argument("--corpus", default=None)
    ap.add_argument("--max-sentence-words", type=int, default=25)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    corpus = args.corpus or os.path.join(
        os.environ.get("CLAUDE_PLUGIN_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "corpus", "banned-phrases.yaml")

    raw = open(args.doc).read()
    text = strip_exempt(raw)
    bp = yaml.safe_load(open(corpus))

    hits = {"error": [], "warn": [], "density": []}
    for cat, cdef in bp["categories"].items():
        for e in cdef["entries"]:
            pat = e.get("pattern") or re.escape(e["phrase"])
            flags = re.I | re.M
            found = re.findall(pat, text, flags)
            if not found:
                continue
            bucket = "density" if e.get("tier") == "density" else e["severity"]
            hits[bucket].append({
                "category": cat,
                "rule": e.get("pattern", e.get("phrase")),
                "count": len(found),
            })

    sents = list(sentences(text))
    lens = [len(s.split()) for s in sents]
    over = [(l, s) for l, s in zip(lens, sents) if l > args.max_sentence_words]
    words = len(text.split())
    emdash = len(re.findall(r" — ", text))

    result = {
        "doc": args.doc,
        "words": words,
        "sentences": len(sents),
        "avg_sentence_words": round(sum(lens) / len(lens), 1) if lens else 0,
        "max_sentence_words": max(lens) if lens else 0,
        f"sentences_over_{args.max_sentence_words}": len(over),
        "em_dashes": emdash,
        "em_dashes_per_1000_words": round(1000 * emdash / words, 1) if words else 0,
        "error_hits": sum(h["count"] for h in hits["error"]),
        "warn_hits": sum(h["count"] for h in hits["warn"]),
        "density_hits": sum(h["count"] for h in hits["density"]),
        "density_per_1000_words": round(1000 * sum(h["count"] for h in hits["density"]) / words, 1) if words else 0,
        "detail": hits,
    }

    if args.json:
        print(json.dumps(result, indent=1))
        return

    print(f"{args.doc}: {words} words, {len(sents)} sentences "
          f"(avg {result['avg_sentence_words']}w, max {result['max_sentence_words']}w, "
          f"{len(over)} over {args.max_sentence_words}w)")
    print(f"em-dashes: {emdash} ({result['em_dashes_per_1000_words']}/1000w)")
    for sev in ("error", "warn", "density"):
        total = sum(h["count"] for h in hits[sev])
        print(f"{sev}: {total} hits across {len(hits[sev])} rules")
        for h in sorted(hits[sev], key=lambda x: -x["count"])[:12]:
            print(f"  {h['count']:3d}  [{h['category']}] {h['rule']}")


if __name__ == "__main__":
    main()
