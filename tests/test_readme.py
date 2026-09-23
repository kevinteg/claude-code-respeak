"""Tests for the public README: design/readme/source.md and its render README.md.

The status line names the manifest's version and the suite's live counts
(scripts/readme-render.sh writes it before each render); the icon line sits
on line 3 and points at a plain SVG; the source stays under its ceiling; the
two files share their `## ` headings; neither names a sibling path or any
sibling but the optional provider.
"""
import glob
import json
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(ROOT, "design", "readme", "source.md")
README = os.path.join(ROOT, "README.md")
ICON = os.path.join(ROOT, "assets", "icon.svg")
MANIFEST = os.path.join(ROOT, "plugin", ".claude-plugin", "plugin.json")
CEILING = 24576

STATUS_RE = re.compile(
    r"^Status: version `([0-9.]+)`, rendered `[0-9]{4}-[0-9]{2}-[0-9]{2}`, "
    r"`([0-9]+)` unittest cases and `([0-9]+)` bash suites\.$",
    re.M,
)
ICON_LINE = '<img src="assets/icon.svg" alt="" width="56" align="left">'
# Sibling plugin ids other than the provider; the provider is claude-code-session.
OTHER_SIBLINGS = re.compile(r"syrvis|claude-code-agents|agent-relay|claude-code-decisions", re.I)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


class StatusLine(unittest.TestCase):
    def test_once_per_file_matching_manifest_and_live_counts(self):
        with open(MANIFEST, encoding="utf-8") as f:
            version = json.load(f)["version"]
        # A fresh loader: discover() records its top-level dir on the loader.
        cases = unittest.TestLoader().discover(os.path.join(ROOT, "tests")).countTestCases()
        suites = len(glob.glob(os.path.join(ROOT, "tests", "*.sh")))
        for path in (SOURCE, README):
            with self.subTest(path=os.path.relpath(path, ROOT)):
                found = STATUS_RE.findall(read(path))
                self.assertEqual(len(found), 1, "one status line")
                self.assertEqual(found[0], (version, str(cases), str(suites)))

    def test_first_line_under_status_heading(self):
        for path in (SOURCE, README):
            with self.subTest(path=os.path.relpath(path, ROOT)):
                parts = read(path).split("\n## Status\n", 1)
                self.assertEqual(len(parts), 2, "no ## Status heading")
                after = parts[1]
                self.assertTrue(STATUS_RE.match(after.lstrip("\n").split("\n", 1)[0]))


class Icon(unittest.TestCase):
    def test_line_three_of_both_files(self):
        for path in (SOURCE, README):
            with self.subTest(path=os.path.relpath(path, ROOT)):
                self.assertEqual(read(path).split("\n")[2], ICON_LINE)

    def test_plain_svg(self):
        svg = read(ICON)
        self.assertIn('viewBox="0 0 64 64"', svg)
        self.assertIn("<title>respeak</title>", svg)
        self.assertIn('role="img"', svg)
        self.assertIn("aria-label=", svg)
        for banned in ("url(#", "Gradient", "<filter", "<script", "href="):
            self.assertNotIn(banned, svg)
        self.assertLess(len(svg.encode("utf-8")), 1500)
        self.assertFalse(os.path.exists(os.path.join(ROOT, "assets", "respeak-icon.svg")))


class Shape(unittest.TestCase):
    def test_source_under_ceiling(self):
        self.assertLessEqual(os.path.getsize(SOURCE), CEILING)

    def test_headings_equal(self):
        def heads(path):
            return [l for l in read(path).split("\n") if l.startswith("## ")]
        self.assertEqual(heads(SOURCE), heads(README))

    def test_references_linked(self):
        for path in (SOURCE, README):
            with self.subTest(path=os.path.relpath(path, ROOT)):
                self.assertTrue("(/docs/references.md)" in read(path), "no link to docs/references.md")

    def test_no_sibling_path_or_other_sibling(self):
        for path in (SOURCE, README):
            with self.subTest(path=os.path.relpath(path, ROOT)):
                text = read(path)
                self.assertFalse("../" in text, "a ../ path")
                hit = OTHER_SIBLINGS.search(text)
                self.assertIsNone(hit and hit.group(0))


if __name__ == "__main__":
    unittest.main()
