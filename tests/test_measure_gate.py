"""Tests for scripts/respeak-measure.py — style-gate scanning and enforcement.

Unit-level checks import the module directly (same style as
test_verify_edit.py); CLI-level checks (exit-code semantics, --config,
multi-doc) shell out via subprocess with sys.executable, because that is
the actual enforcement surface — the gate hook calls the script, not a
Python API.

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
MEASURE_PATH = os.path.join(HERE, "..", "scripts", "respeak-measure.py")

_spec = importlib.util.spec_from_file_location("respeak_measure", MEASURE_PATH)
assert _spec is not None and _spec.loader is not None
rm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rm)


def write_tmp(text, suffix=".md"):
    f = tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False)
    f.write(text)
    f.close()
    return f.name


def run_measure(args):
    return subprocess.run(
        [sys.executable, MEASURE_PATH] + args,
        capture_output=True, text=True,
    )


class TestFailOnSemantics(unittest.TestCase):
    def setUp(self):
        self.error_doc = write_tmp("This design is load-bearing for everything downstream.\n")
        self.warn_doc = write_tmp("The plan really leverages the cache, crisp and fast.\n")
        self.clean_doc = write_tmp("The plan uses the cache and finishes in three steps.\n")

    def tearDown(self):
        for p in (self.error_doc, self.warn_doc, self.clean_doc):
            os.unlink(p)

    def test_fail_on_none_never_fails(self):
        r = run_measure([self.error_doc, "--fail-on", "none"])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_fail_on_error_trips_on_error_hit(self):
        r = run_measure([self.error_doc, "--fail-on", "error"])
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)

    def test_fail_on_error_passes_clean_doc(self):
        r = run_measure([self.clean_doc, "--fail-on", "error"])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_fail_on_warn_trips_on_warn_hit(self):
        r = run_measure([self.warn_doc, "--fail-on", "warn"])
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)

    def test_fail_on_error_does_not_trip_on_warn_only(self):
        r = run_measure([self.warn_doc, "--fail-on", "error"])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_usage_error_exits_2(self):
        r = run_measure(["/no/such/file.md", "--fail-on", "error"])
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)


class TestExceptions(unittest.TestCase):
    """The motivating false positive: literal "spine switch" networking
    prose vs. the owner-banned "the spine" structure metaphor."""

    def test_spine_switch_literal_passes(self):
        doc = write_tmp("The spine switch peers with every leaf switch over eBGP.\n")
        try:
            r = run_measure([doc, "--fail-on", "error"])
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        finally:
            os.unlink(doc)

    def test_spine_metaphor_still_fails(self):
        doc = write_tmp("The spine of the argument is that latency dominates cost.\n")
        try:
            r = run_measure([doc, "--fail-on", "error"])
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        finally:
            os.unlink(doc)

    def test_spine_neighbor_statement_passes(self):
        """Broader networking-vocabulary exception: no verb-list match needed,
        just networking terms (here, "leaf") in the same sentence."""
        doc = write_tmp(
            "Traffic fails when the spine hasn't got a neighbor statement for the leaf.\n"
        )
        try:
            r = run_measure([doc, "--fail-on", "error"])
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        finally:
            os.unlink(doc)

    def test_spine_of_the_argument_still_fails(self):
        doc = write_tmp("The spine of the argument is weak.\n")
        try:
            r = run_measure([doc, "--fail-on", "error"])
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        finally:
            os.unlink(doc)


class TestGateAllow(unittest.TestCase):
    def test_allow_regex_skips_rule(self):
        doc = write_tmp("This design is load-bearing for everything downstream.\n")
        cfg = write_tmp("gate:\n  allow:\n    - 'load-bearing'\n", suffix=".yaml")
        try:
            r = run_measure([doc, "--fail-on", "error"])
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)

            r_allowed = run_measure([doc, "--fail-on", "error", "--config", cfg])
            self.assertEqual(r_allowed.returncode, 0, r_allowed.stdout + r_allowed.stderr)
        finally:
            os.unlink(doc)
            os.unlink(cfg)


class TestBudgets(unittest.TestCase):
    def test_emdash_budget_fails_and_reported(self):
        text = " — ".join(["word"] * 30) + ".\n"
        doc = write_tmp(text)
        cfg = write_tmp("style:\n  budgets:\n    emdash_per_1000_words: 1\n", suffix=".yaml")
        try:
            r = run_measure([doc, "--fail-on", "warn", "--config", cfg, "--json"])
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            data = json.loads(r.stdout)
            self.assertEqual(data[0]["budgets"]["emdash_per_1000_words"]["status"], "FAIL")
        finally:
            os.unlink(doc)
            os.unlink(cfg)

    def test_budget_pass_reported(self):
        doc = write_tmp("This document has no dashes at all and reads cleanly.\n")
        try:
            r = run_measure([doc, "--json"])
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            data = json.loads(r.stdout)
            self.assertEqual(data[0]["budgets"]["emdash_per_1000_words"]["status"], "PASS")
        finally:
            os.unlink(doc)


class TestMultiDoc(unittest.TestCase):
    def test_json_emits_list_for_multiple_docs(self):
        doc1 = write_tmp("Clean sentence one.\n")
        doc2 = write_tmp("This design is load-bearing for everything.\n")
        try:
            r = run_measure([doc1, doc2, "--json"])
            data = json.loads(r.stdout)
            self.assertEqual(len(data), 2)
            self.assertEqual(data[0]["doc"], doc1)
            self.assertEqual(data[1]["doc"], doc2)
        finally:
            os.unlink(doc1)
            os.unlink(doc2)

    def test_fail_on_error_trips_if_any_doc_fails(self):
        doc1 = write_tmp("Clean sentence one.\n")
        doc2 = write_tmp("This design is load-bearing for everything.\n")
        try:
            r = run_measure([doc1, doc2, "--fail-on", "error"])
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        finally:
            os.unlink(doc1)
            os.unlink(doc2)


class TestSentenceWindow(unittest.TestCase):
    def test_window_isolates_sentence(self):
        text = "First sentence here. The spine of the argument matters. Third one."
        start = text.index("spine")
        end = start + len("spine")
        window = rm.sentence_window(text, start, end)
        self.assertIn("The spine of the argument matters", window)
        self.assertNotIn("First sentence", window)


if __name__ == "__main__":
    unittest.main()


class SetupErrorsExit2(unittest.TestCase):
    """v0.4.2: every non-verdict failure exits 2, so the gate hook fails open.
    An uncaught exception exits 1 in CPython, which the hook reads as a
    verdict; these pin the cases an adversarial re-break found."""

    CLEAN = "# T\n\nThe plan uses the cache and finishes in three steps.\n"

    def corpus_file(self, text):
        return write_tmp(text, suffix=".yaml")

    def test_non_utf8_doc_is_a_setup_error(self):
        f = tempfile.NamedTemporaryFile(mode="wb", suffix=".md", delete=False)
        f.write(b"# T\n\nThe plan uses the cache. Caf\xe9 is not UTF-8.\n"); f.close()
        r = run_measure([f.name, "--fail-on", "error"])
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn("not UTF-8", r.stderr)

    def test_bad_allow_regex_is_a_setup_error(self):
        cfg = write_tmp("gate:\n  allow: ['(']\n", suffix=".yaml")
        r = run_measure([write_tmp(self.CLEAN), "--fail-on", "error", "--config", cfg])
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn("gate.allow", r.stderr)

    def test_corpus_shape_errors_exit_2(self):
        cases = {
            "no categories": "foo: bar\n",
            "empty file": "",
            "a list": "- a\n",
            "bad pattern": "categories:\n  x:\n    entries:\n      - {pattern: '(', severity: error}\n",
            "bad exception": "categories:\n  x:\n    entries:\n      - {phrase: foo, severity: error, exceptions: ['(']}\n",
            "bad severity": "categories:\n  x:\n    entries:\n      - {phrase: foo, severity: loud}\n",
            "entry without text": "categories:\n  x:\n    entries:\n      - {severity: error}\n",
        }
        for name, text in cases.items():
            r = run_measure([write_tmp(self.CLEAN), "--fail-on", "error", "--corpus", self.corpus_file(text)])
            self.assertEqual(r.returncode, 2, "%s: rc=%s stderr=%s" % (name, r.returncode, r.stderr))
            self.assertTrue(r.stderr.startswith("respeak-measure:"), name)
            self.assertNotIn("Traceback", r.stderr, name)

    def test_config_that_is_not_a_mapping_exits_2(self):
        cfg = write_tmp("- just\n- a list\n", suffix=".yaml")
        r = run_measure([write_tmp(self.CLEAN), "--config", cfg])
        self.assertEqual(r.returncode, 2, r.stderr)

    def test_a_real_verdict_still_exits_1(self):
        r = run_measure([write_tmp("# T\n\nThis is load-bearing.\n"), "--fail-on", "error"])
        self.assertEqual(r.returncode, 1, r.stderr)


class StdinAndEncoding(unittest.TestCase):
    """v0.4.3: '-' reads the document from stdin (so a skill can verify a
    narrative without a temp file), and a non-UTF-8 stdout never turns a
    report into a crash (which exits 1, the verdict status)."""

    def run_stdin(self, text, *args, env_extra=None):
        env = dict(os.environ); env.update(env_extra or {})
        return subprocess.run([sys.executable, MEASURE_PATH, "-"] + list(args),
                              input=text, capture_output=True, text=True, env=env)

    def test_stdin_pass_and_verdict(self):
        r = self.run_stdin("# T\n\nThe plan uses the cache.\n", "--fail-on", "error")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("<stdin>:", r.stdout)
        r = self.run_stdin("# T\n\nThis is load-bearing.\n", "--fail-on", "error")
        self.assertEqual(r.returncode, 1, r.stderr)
        r = self.run_stdin("# T\n\nfine\n", "--fail-on", "error", "--json")
        self.assertEqual(json.loads(r.stdout)[0]["doc"], "<stdin>")

    def test_stdin_twice_is_a_setup_error(self):
        r = subprocess.run([sys.executable, MEASURE_PATH, "-", "-"], input="x", capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)

    def test_non_utf8_stdout_does_not_crash_a_warn_only_report(self):
        doc = write_tmp("# T\n\nThe team said “hello” on Monday. Nothing else changed.\n")
        for enc in ("ascii", "latin-1"):
            r = subprocess.run([sys.executable, MEASURE_PATH, doc, "--fail-on", "error"],
                               capture_output=True, text=True, env=dict(os.environ, PYTHONIOENCODING=enc))
            self.assertEqual(r.returncode, 0, "%s: %s" % (enc, r.stderr))
            self.assertNotIn("Traceback", r.stderr)
