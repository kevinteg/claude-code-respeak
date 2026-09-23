"""Tests for corpus/banned-phrases.yaml — the shipped rules themselves.

test_measure_gate.py covers the scanner's behavior with small ad-hoc
corpora; this module scans with the REAL corpus file, because the thing
under test is what the shipped entries do to real sentences: a literal
sense (a game title, a filename character, a planting style, food texture)
must pass, and the cliche the entry bans must still flag.

Unit-level checks import the module directly (same style as
test_measure_gate.py); the tier and case-sensitivity checks shell out,
because the JSON report is what the gate hook and the pass readers see.

Run: python3 -m unittest discover tests -v
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(__file__)
MEASURE_PATH = os.path.join(HERE, "..", "plugin", "scripts", "respeak-measure.py")
CORPUS_PATH = os.path.join(HERE, "..", "plugin", "corpus", "banned-phrases.yaml")

_spec = importlib.util.spec_from_file_location("respeak_measure", MEASURE_PATH)
assert _spec is not None and _spec.loader is not None
rm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rm)

CORPUS = rm.load_yaml(CORPUS_PATH)


def write_tmp(text, suffix=".md"):
    f = tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False)
    f.write(text)
    f.close()
    return f.name


def run_measure(args, stdin=None):
    return subprocess.run(
        [sys.executable, MEASURE_PATH] + args,
        input=stdin, capture_output=True, text=True,
    )


def rules_hit(text):
    """Every rule the shipped corpus flags in one sentence, as the scanner
    sees it (exempt spans stripped first, like measure() does)."""
    hits = rm.scan_doc(rm.strip_exempt(text), CORPUS, [])
    return {h["rule"] for sev in hits for h in hits[sev]}


def entry_for(pattern):
    for cat in CORPUS["categories"].values():
        for e in cat["entries"]:
            if e.get("pattern") == pattern or e.get("phrase") == pattern:
                return e
    raise AssertionError("no corpus entry for %r" % pattern)


# rule -> (sentences whose sense is literal, sentence that is the cliche).
# Every literal sentence here is one a 2026-09-21 site pass met on a real
# family page, or the sense named in the entry's comment.
LITERAL_SENSES = {
    r'\bsymphony of\b': (
        ["Castlevania: Symphony of the Night sits on the PS1 shelf.\n"],
        "The release notes read like a symphony of moving parts.\n",
    ),
    r'\bshowcas(e|es|ed|ing)\b': (
        ["The Character Showcase panel is what Enka.Network reads.\n",
         "Turn on the in-game showcase before the account is scanned.\n"],
        "This page showcases the range of the catalog.\n",
    ),
    r'\bseamless(ly)?\b': (
        ["The Seamless HD Project replaces the Resident Evil 2 backgrounds.\n",
         "Seamless HD ships as a texture pack for the PC release.\n"],
        "The two tools work seamlessly together on every run.\n",
    ),
    r'\bunderscor(e|es|ed|ing)\b': (
        ["The true filename uses a hyphen, not underscore, and lowercase with.\n",
         "Use the underscore character between the two words.\n",
         "There is an underscore in the name of every episode file.\n"],
        "These numbers underscore the risk of a second outage.\n",
    ),
    r'\bjourney\b': (
        ["Dragon Quest VIII: Journey of the Cursed King runs on the PS2.\n"],
        "The journey to a working build took four weekends.\n",
    ),
    r'\bindelible( mark)?\b': (
        ["The Indelible Coterie banner returns in version 2.4.\n"],
        "The release left an indelible mark on the whole team.\n",
    ),
    'tapestry': (
        ["The alley bed holds a sempervivum tapestry of twenty-three rosettes.\n",
         "A tapestry lawn replaces turf with low creeping plants.\n",
         "The tapestry hedge mixes beech and hornbeam in one line.\n"],
        "The report weaves a rich tapestry of half-finished ideas.\n",
    ),
    'crisp': (
        ["Rest the bird ten minutes, uncovered to keep skin crisp.\n",
         "Just-picked cukes ferment far crisper than store ones.\n",
         "Leaf scorch shows as crisped margins on the south side.\n",
         "We walked at dawn in crisp air with frost on the deck.\n"],
        "The summary is crisp and the argument is clear.\n",
    ),
}


class TestLiteralSenseExceptions(unittest.TestCase):
    """Each entry's `exceptions:` clear the literal sense without retiring
    the rule. The false positives come from the 2026-09-21 site pass."""

    def test_literal_sense_passes(self):
        for rule, (literals, _) in LITERAL_SENSES.items():
            for sentence in literals:
                with self.subTest(rule=rule, sentence=sentence.strip()):
                    self.assertNotIn(rule, rules_hit(sentence))

    def test_cliche_still_flags(self):
        for rule, (_, cliche) in LITERAL_SENSES.items():
            with self.subTest(rule=rule, sentence=cliche.strip()):
                self.assertIn(rule, rules_hit(cliche))

    def test_every_exempted_entry_documents_its_exceptions(self):
        """A bare exception is a rule nobody can review: each of these
        entries carries a comment naming the page or sense behind it, and
        the YAML loader drops comments, so this checks the raw text."""
        with open(CORPUS_PATH, encoding="utf-8") as f:
            raw = f.read()
        for rule in LITERAL_SENSES:
            with self.subTest(rule=rule):
                self.assertIn(rule, raw)
                start = raw.index(rule)
                body = raw[start:start + 1200]
                self.assertIn("exceptions:", body)
                self.assertIn("#", body[body.index("exceptions:"):])

    def test_error_sense_passes_the_gate_end_to_end(self):
        """The unit checks above read the buckets; this one pins the exit
        code the gate hook acts on, for an error-severity entry."""
        literal = run_measure(["-", "--corpus", CORPUS_PATH, "--fail-on", "error"],
                              stdin=LITERAL_SENSES[r'\bsymphony of\b'][0][0])
        self.assertEqual(literal.returncode, 0, literal.stdout + literal.stderr)
        cliche = run_measure(["-", "--corpus", CORPUS_PATH, "--fail-on", "error"],
                             stdin=LITERAL_SENSES[r'\bsymphony of\b'][1])
        self.assertEqual(cliche.returncode, 1, cliche.stdout + cliche.stderr)


class TestFormatTellDensityTier(unittest.TestCase):
    """Thematic breaks and curly quotes are generator and publisher output,
    so they count against the density budget instead of per occurrence."""

    DOC = ("# Page\n\nOne plain sentence of prose here.\n\n---\n\n"
           "The reviewer said \u201chello\u201d on Monday.\n\n---\n")

    def setUp(self):
        self.doc = write_tmp(self.DOC)

    def tearDown(self):
        os.unlink(self.doc)

    def report(self):
        r = run_measure([self.doc, "--corpus", CORPUS_PATH, "--json"])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return json.loads(r.stdout)[0]

    def test_both_rules_land_in_the_density_bucket(self):
        d = self.report()
        density = {h["rule"]: h["count"] for h in d["detail"]["density"]}
        self.assertEqual(density.get(r'^-{3,}$'), 2)
        self.assertEqual(density.get('[\u201c\u201d]'), 2)

    def test_neither_rule_counts_as_a_warn_hit(self):
        d = self.report()
        warn = {h["rule"] for h in d["detail"]["warn"]}
        self.assertNotIn(r'^-{3,}$', warn)
        self.assertNotIn('[\u201c\u201d]', warn)
        self.assertEqual(d["warn_hits"], 0)

    def test_they_reach_the_density_budget(self):
        d = self.report()
        self.assertEqual(d["density_hits"], 4)
        self.assertEqual(d["budgets"]["warn_phrases_per_1000_words"]["value"],
                         d["density_per_1000_words"])

    def test_the_entries_declare_the_tier(self):
        self.assertEqual(entry_for(r'^-{3,}$').get("tier"), "density")
        self.assertEqual(entry_for('[\u201c\u201d]').get("tier"), "density")


def scanner_reads_case_sensitive():
    """True when the scanner honors a per-entry case_sensitive: true. The
    corpus declares the key before the scanner supports it (two branches),
    so the behavior checks below skip until both are merged."""
    corpus = write_tmp("categories:\n  x:\n    entries:\n"
                       "      - {pattern: '\\bFoo\\b', severity: error, case_sensitive: true}\n",
                       suffix=".yaml")
    try:
        r = run_measure(["-", "--corpus", corpus, "--fail-on", "error"],
                        stdin="the foo value is read once per run\n")
        return r.returncode == 0
    finally:
        os.unlink(corpus)


CASE_SENSITIVE_READY = scanner_reads_case_sensitive()
STOCK_NAMES = r'\b(Lyra|Eira|Jaxon|Elias)\b'


class TestCaseSensitiveStockNames(unittest.TestCase):
    """LYRA is a pencil brand on a real household page, and exceptions
    compile with re.I, so only case-sensitive matching separates the brand
    from the invented-character name."""

    def test_entry_declares_case_sensitive(self):
        self.assertIs(entry_for(STOCK_NAMES).get("case_sensitive"), True)

    @unittest.skipUnless(CASE_SENSITIVE_READY,
                         "scanner has no case_sensitive support yet (measure branch)")
    def test_brand_spelling_passes(self):
        self.assertNotIn(STOCK_NAMES, rules_hit("Two LYRA colored pencils sit in the drawer.\n"))

    @unittest.skipUnless(CASE_SENSITIVE_READY,
                         "scanner has no case_sensitive support yet (measure branch)")
    def test_invented_name_still_flags(self):
        self.assertIn(STOCK_NAMES, rules_hit("Lyra opened the door and read the map.\n"))


if __name__ == "__main__":
    unittest.main()
