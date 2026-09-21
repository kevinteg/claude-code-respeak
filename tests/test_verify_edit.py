"""Tests for scripts/respeak-verify-edit.py — the edit-safety invariants.

Each format gets at least one edit that MUST pass (prose/comment-only) and
several that MUST fail (meaning-carrying content touched).

Run: python3 -m unittest discover tests -v
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest

VERIFY_PATH = os.path.join(os.path.dirname(__file__), "..", "scripts", "respeak-verify-edit.py")

_spec = importlib.util.spec_from_file_location("verify_edit", VERIFY_PATH)
assert _spec is not None and _spec.loader is not None
ve = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ve)


class TestMarkdown(unittest.TestCase):
    BEFORE = """---
title: Demo
---
# Design — the pipeline

The plan is bold — we ship in 3 phases, and it leverages `spec_gen.py`
heavily. See [the doc](../design.md) and run:

```sh
demo ingest --budget 5
```

Latency stays under 250 ms across `retry_loop()`.
"""

    def test_prose_edit_passes(self):
        after = self.BEFORE.replace(
            "The plan is bold — we ship in 3 phases, and it leverages `spec_gen.py`\nheavily.",
            "The plan is bold. We ship in 3 phases, and it uses `spec_gen.py`\nheavily.",
        )
        self.assertEqual(ve.check_md(self.BEFORE, after), [])

    def test_changed_number_fails(self):
        after = self.BEFORE.replace("250 ms", "300 ms")
        self.assertTrue(any("numeric" in p for p in ve.check_md(self.BEFORE, after)))

    def test_changed_link_target_fails(self):
        after = self.BEFORE.replace("(../design.md)", "(../desing.md)")
        self.assertTrue(any("link targets" in p for p in ve.check_md(self.BEFORE, after)))

    def test_changed_fence_fails(self):
        after = self.BEFORE.replace("--budget 5", "--budget 6")
        problems = ve.check_md(self.BEFORE, after)
        self.assertTrue(any("fenced" in p for p in problems))

    def test_changed_heading_fails(self):
        after = self.BEFORE.replace("# Design — the pipeline", "# Design: the pipeline")
        self.assertTrue(any("headings" in p for p in ve.check_md(self.BEFORE, after)))

    def test_changed_inline_code_fails(self):
        after = self.BEFORE.replace("`retry_loop()`", "`retry_loop2()`")
        self.assertTrue(any("inline code" in p for p in ve.check_md(self.BEFORE, after)))

    def test_front_matter_change_fails(self):
        after = self.BEFORE.replace("title: Demo", "title: Demo2")
        self.assertTrue(any("front matter" in p for p in ve.check_md(self.BEFORE, after)))

    def test_link_text_change_passes(self):
        after = self.BEFORE.replace("[the doc](../design.md)", "[the design doc](../design.md)")
        self.assertEqual(ve.check_md(self.BEFORE, after), [])


class TestHeadingDetection(unittest.TestCase):
    """Anything MkDocs or CommonMark renders as a heading counts as one."""

    def test_wrapped_hash_number_becomes_a_heading(self):
        before = "We shipped the parts that came from order #33256. Plus the\nspares.\n"
        after = "We shipped the parts that came from order\n#33256. Plus the spares.\n"
        self.assertTrue(any("headings" in p for p in ve.check_md(before, after)))

    def test_escaped_hash_at_line_start_passes(self):
        before = "We shipped the parts that came from order #33256. Plus the\nspares.\n"
        after = "We shipped the parts that came from order\n\\#33256. Plus the spares.\n"
        self.assertEqual(ve.check_md(before, after), [])

    def test_hash_without_space_is_a_heading(self):
        before = "#33256 in progress\n\nBody with 3 items.\n"
        after = "#33257 in progress\n\nBody with 3 items.\n"
        self.assertTrue(any("headings" in p for p in ve.check_md(before, after)))

    def test_setext_heading_text_change_fails(self):
        before = "Release notes\n=============\n\nBody with 3 items.\n"
        after = "Release note\n=============\n\nBody with 3 items.\n"
        self.assertTrue(any("headings" in p for p in ve.check_md(before, after)))

    def test_setext_underline_length_may_change(self):
        before = "Release notes\n=============\n\nBody with 3 items.\n"
        after = "Release notes\n===\n\nBody with 3 items.\n"
        self.assertEqual(ve.check_md(before, after), [])

    def test_rule_after_a_blank_line_is_not_a_heading(self):
        before = "Intro text.\n\n---\n\nMore text about 3 things.\n"
        after = "Intro prose.\n\n---\n\nMore prose about 3 things.\n"
        self.assertEqual(ve.check_md(before, after), [])

    def test_hash_inside_a_fence_is_not_a_heading(self):
        before = "Body.\n\n```sh\n#33256\n```\n"
        after = "Prose.\n\n```sh\n#33256\n```\n"
        self.assertEqual(ve.check_md(before, after), [])


class TestBlockStructure(unittest.TestCase):
    """Prose that becomes a list, a quote, or a table is a restructure."""

    PROSE = "We serve 3 dishes: the soup, the roast, and the tart.\n"
    LIST = "We serve 3 dishes:\n\n- the soup\n- the roast\n- the tart\n"

    def test_prose_to_list_fails(self):
        problems = ve.check_md(self.PROSE, self.LIST)
        self.assertTrue(any(p.startswith("block structure changed") for p in problems))
        self.assertTrue(any("bullet items 0 -> 3" in p for p in problems))

    def test_prose_to_list_is_a_warning_under_restructure(self):
        hard, warnings = ve.partition_restructure(ve.check_md(self.PROSE, self.LIST))
        self.assertEqual(hard, [])
        self.assertTrue(any("block structure changed" in w for w in warnings))

    def test_wrapped_quote_marker_fails(self):
        before = "The report says the tool is safe > 90 percent of the time,\nwhich is enough.\n"
        after = "The report says the tool is safe\n> 90 percent of the time, which is enough.\n"
        self.assertTrue(any("blockquote lines 0 -> 1" in p for p in ve.check_md(before, after)))

    def test_wrapped_other_ordered_marker_passes(self):
        before = "The kiln holds 2 racks. Rack 1 takes the loaves and rack\n2. The lower rack takes the tins.\n"
        after = "The kiln holds 2 racks. Rack 1 takes the loaves and rack\n2. The lower rack holds the tins.\n"
        self.assertEqual(ve.check_md(before, after), [])

    def test_wrapped_one_marker_fails(self):
        before = "The kiln holds 2 racks, and the lower one is rack\nnumber 1. The tins go there.\n"
        after = "The kiln holds 2 racks, and the lower one is rack number\n1. The tins go there.\n"
        self.assertTrue(any("ordered items 0 -> 1" in p for p in ve.check_md(before, after)))

    def test_moving_paragraphs_passes(self):
        before = "## Beds\n\n- the north bed\n- the south bed\n\nWe water them on 2 days.\n"
        after = "## Beds\n\nWe water them on 2 days.\n\n- the north bed\n- the south bed\n"
        self.assertEqual(ve.check_md(before, after), [])


class TestCode(unittest.TestCase):
    BEFORE = """// This function basically leverages a robust retry — it's crucial.
const URL = "https://api.example.com/v1"; // 3 retries max
function retry(n: number) {
  /* We delve into the queue — draining it seamlessly over 250 ms. */
  return n <= 3 && fetch(URL);
}
"""

    def test_comment_edit_passes(self):
        after = self.BEFORE.replace(
            "// This function basically leverages a robust retry — it's crucial.",
            "// Retries the fetch. Gives up after the limit below.",
        ).replace(
            "/* We delve into the queue — draining it seamlessly over 250 ms. */",
            "/* Drains the queue within 250 ms. */",
        )
        self.assertEqual(ve.check_code(self.BEFORE, after), [])

    def test_code_change_fails(self):
        after = self.BEFORE.replace("n <= 3", "n <= 4")
        self.assertTrue(any("non-comment code" in p for p in ve.check_code(self.BEFORE, after)))

    def test_string_literal_change_fails(self):
        after = self.BEFORE.replace("api.example.com", "api.exmaple.com")
        self.assertTrue(any("non-comment code" in p for p in ve.check_code(self.BEFORE, after)))

    def test_number_in_comment_change_fails(self):
        after = self.BEFORE.replace("250 ms", "500 ms")
        self.assertTrue(any("numeric tokens in comments" in p for p in ve.check_code(self.BEFORE, after)))

    def test_url_slashes_in_string_not_treated_as_comment(self):
        # "https://..." inside a string must stay code, not comment
        after = self.BEFORE.replace('"https://api.example.com/v1"', '"https://api.example.com/v2"')
        self.assertTrue(any("non-comment code" in p for p in ve.check_code(self.BEFORE, after)))


class TestPython(unittest.TestCase):
    BEFORE = '''# Basically we leverage the cache here — it's seamless.
CACHE_TTL = 300  # seconds — crucial for perf


def get(key):
    """Fetch key. >>> get("a")"""
    return CACHE.get(key, None)
'''

    def test_comment_edit_passes(self):
        after = self.BEFORE.replace(
            "# Basically we leverage the cache here — it's seamless.",
            "# Serves reads from the cache.",
        ).replace("# seconds — crucial for perf", "# seconds")
        self.assertEqual(ve.check_py(self.BEFORE, after), [])

    def test_docstring_change_fails(self):
        after = self.BEFORE.replace('"""Fetch key. >>> get("a")"""', '"""Fetches the key."""')
        self.assertTrue(ve.check_py(self.BEFORE, after))

    def test_code_change_fails(self):
        after = self.BEFORE.replace("CACHE_TTL = 300", "CACHE_TTL = 600")
        self.assertTrue(ve.check_py(self.BEFORE, after))

    def test_hash_in_string_is_code(self):
        before = 'x = "#not a comment"\n'
        after = 'x = "#not a  comment"\n'
        self.assertTrue(ve.check_py(before, after))


class TestPythonAllowStrings(unittest.TestCase):
    """--allow-strings: the display text in a page generator may be edited."""

    BEFORE = '''"""Render the cards."""
LABELS = {"season": "Best in 3 seasons", "cost": "Costs %s per night"}


def render(rows):
    """Build the page. >>> render([])"""
    note = "See [the guide](../guide.md) and run `make site` for 2 runs."
    return "%d of %d rows" % (len(rows), 12), note, LABELS
'''

    OPTS = ve.Options(allow_strings=True)

    def test_string_edit_passes(self):
        after = self.BEFORE.replace(
            '"Best in 3 seasons"', '"At its best in 3 seasons"'
        ).replace(
            "See [the guide](../guide.md) and run `make site` for 2 runs.",
            "Read [the guide](../guide.md), then run `make site`; it takes 2 runs.",
        )
        self.assertEqual(ve.check_py(self.BEFORE, after, self.OPTS), [])

    def test_new_dict_entry_fails(self):
        after = self.BEFORE.replace(
            '"cost": "Costs %s per night"}',
            '"cost": "Costs %s per night", "gear": "Bring boots"}',
        )
        problems = ve.check_py(self.BEFORE, after, self.OPTS)
        self.assertTrue(any("python code changed" in p for p in problems))

    def test_lost_placeholder_fails(self):
        after = self.BEFORE.replace('"Costs %s per night"', '"Costs that much per night"')
        problems = ve.check_py(self.BEFORE, after, self.OPTS)
        self.assertTrue(any("%-placeholders" in p for p in problems))

    def test_changed_number_in_string_fails(self):
        after = self.BEFORE.replace('"Best in 3 seasons"', '"Best in 4 seasons"')
        problems = ve.check_py(self.BEFORE, after, self.OPTS)
        self.assertTrue(any("numbers" in p for p in problems))

    def test_changed_link_target_in_string_fails(self):
        after = self.BEFORE.replace("(../guide.md)", "(../handbook.md)")
        problems = ve.check_py(self.BEFORE, after, self.OPTS)
        self.assertTrue(any("link targets" in p for p in problems))

    def test_doctest_docstring_edit_fails(self):
        after = self.BEFORE.replace(
            '"""Build the page. >>> render([])"""', '"""Builds the page. >>> render([])"""'
        )
        problems = ve.check_py(self.BEFORE, after, self.OPTS)
        self.assertTrue(any("doctest" in p for p in problems))

    def test_plain_docstring_edit_passes(self):
        after = self.BEFORE.replace('"""Render the cards."""', '"""Renders the cards."""')
        self.assertEqual(ve.check_py(self.BEFORE, after, self.OPTS), [])

    def test_changed_call_fails(self):
        after = self.BEFORE.replace("len(rows)", "len(rows) + 1")
        self.assertTrue(ve.check_py(self.BEFORE, after, self.OPTS))

    def test_fstring_literal_edit_passes(self):
        before = 'def f(n, m):\n    return f"We walked {n} of the {m} trails, 2 of them twice."\n'
        after = 'def f(n, m):\n    return f"We walked {n} of the {m} trails; 2 were repeats."\n'
        self.assertEqual(ve.check_py(before, after, self.OPTS), [])

    def test_fstring_expression_change_fails(self):
        before = 'def f(n, m):\n    return f"We walked {n} of the {m} trails."\n'
        after = 'def f(n, m):\n    return f"We walked {m} of the {n} trails."\n'
        self.assertTrue(ve.check_py(before, after, self.OPTS))

    def test_without_the_flag_a_string_edit_still_fails(self):
        after = self.BEFORE.replace('"Best in 3 seasons"', '"At its best in 3 seasons"')
        self.assertTrue(ve.check_py(self.BEFORE, after))


class TestHtml(unittest.TestCase):
    BEFORE = """<div class="hero"><h1>We leverage synergy — seamlessly!</h1>
<p>Latency is 250 ms.</p>
<script>let n = 3;</script>
<pre>exact output 42</pre></div>
"""

    def test_text_edit_passes(self):
        after = self.BEFORE.replace(
            "We leverage synergy — seamlessly!", "We connect the two systems."
        )
        self.assertEqual(ve.check_html(self.BEFORE, after), [])

    def test_attribute_change_fails(self):
        after = self.BEFORE.replace('class="hero"', 'class="hero2"')
        self.assertTrue(any("skeleton" in p for p in ve.check_html(self.BEFORE, after)))

    def test_script_change_fails(self):
        after = self.BEFORE.replace("let n = 3;", "let n = 4;")
        self.assertTrue(any("script/style/pre/code" in p for p in ve.check_html(self.BEFORE, after)))

    def test_pre_change_fails(self):
        after = self.BEFORE.replace("exact output 42", "exact output 43")
        self.assertTrue(any("script/style/pre/code" in p for p in ve.check_html(self.BEFORE, after)))

    def test_text_number_change_fails(self):
        after = self.BEFORE.replace("250 ms", "50 ms")
        self.assertTrue(any("numeric" in p for p in ve.check_html(self.BEFORE, after)))


class TestYamlJson(unittest.TestCase):
    YB = "# crucial setting — do not touch\nretries: 3   # basically the max\n"

    def test_yaml_comment_edit_passes(self):
        after = self.YB.replace("# crucial setting — do not touch", "# retry ceiling")
        self.assertEqual(ve.check_yaml(self.YB, after), [])

    def test_yaml_value_change_fails(self):
        after = self.YB.replace("retries: 3", "retries: 4")
        self.assertTrue(ve.check_yaml(self.YB, after))

    def test_json_whitespace_passes(self):
        self.assertEqual(ve.check_json('{"a": 1}', '{\n  "a": 1\n}'), [])

    def test_json_value_change_fails(self):
        self.assertTrue(ve.check_json('{"a": 1}', '{"a": 2}'))


class TestProseKeys(unittest.TestCase):
    """--prose-keys: the display strings in front matter and yaml catalogs."""

    OPTS = ve.Options(prose_keys={"pitch", "best_window"})
    BEFORE = '''---
title: Cape Trail
pitch: "A 3 mile loop with the best view in the county."
best_window: April to June
distance_km: 5
---

# Cape Trail

The loop takes 2 hours.
'''

    def test_edited_pitch_passes(self):
        after = self.BEFORE.replace(
            '"A 3 mile loop with the best view in the county."',
            '"A 3 mile loop, and the county\'s best view."',
        )
        self.assertEqual(ve.check_md(self.BEFORE, after, self.OPTS), [])

    def test_dropped_number_fails(self):
        after = self.BEFORE.replace(
            '"A 3 mile loop with the best view in the county."',
            '"A short loop with the best view in the county."',
        )
        problems = ve.check_md(self.BEFORE, after, self.OPTS)
        self.assertTrue(any("numbers" in p for p in problems))

    def test_unlisted_key_change_fails(self):
        after = self.BEFORE.replace("title: Cape Trail", "title: The Cape Trail")
        problems = ve.check_md(self.BEFORE, after, self.OPTS)
        self.assertTrue(any("not a prose key" in p for p in problems))

    def test_quote_style_change_fails(self):
        after = self.BEFORE.replace(
            'pitch: "A 3 mile loop with the best view in the county."',
            "pitch: A 3 mile loop with the best view in the county.",
        )
        problems = ve.check_md(self.BEFORE, after, self.OPTS)
        self.assertTrue(any("quote style changed at pitch" in p for p in problems))

    def test_without_the_flag_front_matter_stays_byte_invariant(self):
        after = self.BEFORE.replace("in the county", "in the whole county")
        self.assertTrue(any(p == "front matter changed" for p in ve.check_md(self.BEFORE, after)))

    def test_body_is_still_checked(self):
        after = self.BEFORE.replace("The loop takes 2 hours.", "The loop takes 3 hours.")
        problems = ve.check_md(self.BEFORE, after, self.OPTS)
        self.assertTrue(any("numeric tokens" in p for p in problems))

    YAML = ("shows:\n"
            "  - name: Datanauts\n"
            "    blurb: A show about 3 kinds of data work.\n"
            "    feed: https://example.com/feed.xml\n")

    def test_yaml_star_narrative_edit_passes(self):
        after = self.YAML.replace(
            "blurb: A show about 3 kinds of data work.",
            "blurb: A show that covers 3 kinds of data work.",
        )
        self.assertEqual(ve.check_yaml(self.YAML, after, ve.Options(prose_keys="*")), [])

    def test_yaml_star_changed_key_fails(self):
        after = self.YAML.replace("blurb:", "summary:")
        problems = ve.check_yaml(self.YAML, after, ve.Options(prose_keys="*"))
        self.assertTrue(any("keys changed" in p for p in problems))

    def test_yaml_star_lost_url_fails(self):
        after = self.YAML.replace("https://example.com/feed.xml", "https://example.com/rss.xml")
        problems = ve.check_yaml(self.YAML, after, ve.Options(prose_keys="*"))
        self.assertTrue(any("URLs" in p for p in problems))

    def test_parse_prose_keys(self):
        self.assertIsNone(ve.parse_prose_keys(None))
        self.assertEqual(ve.parse_prose_keys("*"), "*")
        self.assertEqual(ve.parse_prose_keys("pitch, summary"), {"pitch", "summary"})


class TestRestructureMode(unittest.TestCase):
    def test_heading_change_relaxes_to_warning(self):
        before = "# Old title\n\nBody stays with 3 items.\n"
        after = "# New title\n\nBody stays with 3 items.\n"
        problems = ve.check_md(before, after)
        hard, warnings = ve.partition_restructure(problems)
        self.assertEqual(hard, [])
        self.assertTrue(any("headings" in w for w in warnings))

    def test_fence_change_stays_hard(self):
        before = "# T\n\n```sh\nrun --n 3\n```\n"
        after = "# T2\n\n```sh\nrun --n 4\n```\n"
        hard, warnings = ve.partition_restructure(ve.check_md(before, after))
        self.assertTrue(any("fenced" in p for p in hard))
        self.assertTrue(any("headings" in w for w in warnings))

    def test_number_change_stays_hard(self):
        before = "# T\n\nLatency is 250 ms.\n"
        after = "# T\n\nLatency is 300 ms.\n"
        hard, warnings = ve.partition_restructure(ve.check_md(before, after))
        self.assertTrue(any("numeric" in p for p in hard))
        self.assertEqual(warnings, [])

    def test_front_matter_change_relaxes(self):
        before = "---\ntitle: Old\n---\nBody.\n"
        after = "---\ntitle: New\n---\nBody.\n"
        hard, warnings = ve.partition_restructure(ve.check_md(before, after))
        self.assertEqual(hard, [])
        self.assertTrue(any("front matter" in w for w in warnings))


class TestDirs(unittest.TestCase):
    """--dirs: a rendered tree verified against its predecessor."""

    TREES = {
        "safe.md": ("# Trail\n\nIt basically takes 2 hours.\n",
                    "# Trail\n\nIt takes 2 hours.\n"),
        "broken.md": ("# Trail\n\nIt takes 2 hours.\n",
                      "# Trail\n\nIt takes 3 hours.\n"),
        "same.md": ("# Notes\n", "# Notes\n"),
        "photo.png": ("first bytes\n", "other bytes\n"),
        "sub/page.html": ("<p>We leverage 4 tools.</p>\n", "<p>We use 4 tools.</p>\n"),
    }

    def build(self, tmp):
        before, after = os.path.join(tmp, "before"), os.path.join(tmp, "after")
        for root, index in ((before, 0), (after, 1)):
            for name, texts in self.TREES.items():
                path = os.path.join(root, name)
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(texts[index])
        with open(os.path.join(before, "gone.md"), "w", encoding="utf-8") as fh:
            fh.write("# Gone\n")
        with open(os.path.join(after, "new.md"), "w", encoding="utf-8") as fh:
            fh.write("# New\n")
        return before, after

    def test_statuses(self):
        with tempfile.TemporaryDirectory() as tmp:
            before, after = self.build(tmp)
            rows = {r["path"]: r for r in ve.verify_dirs(before, after, ve.Options())}
        self.assertEqual(rows["safe.md"]["status"], "PASS")
        self.assertEqual(rows["broken.md"]["status"], "FAIL")
        self.assertTrue(any("numeric" in p for p in rows["broken.md"]["problems"]))
        self.assertEqual(rows["same.md"]["status"], "UNCHANGED")
        self.assertEqual(rows["photo.png"]["status"], "SKIP")
        self.assertEqual(rows[os.path.join("sub", "page.html")]["status"], "PASS")
        self.assertEqual(rows["gone.md"]["status"], "REMOVED")
        self.assertEqual(rows["new.md"]["status"], "ADDED")

    def test_cli_text_report_and_exit_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            before, after = self.build(tmp)
            r = subprocess.run([sys.executable, VERIFY_PATH, "--dirs", before, after],
                               capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        self.assertIn("FAIL     broken.md", r.stdout)
        self.assertIn("PASS     safe.md", r.stdout)
        self.assertIn("SKIP     photo.png", r.stdout)
        self.assertIn("ADDED    new.md", r.stdout)
        self.assertIn("REMOVED  gone.md", r.stdout)
        self.assertNotIn("same.md", r.stdout)
        self.assertIn("1 fail", r.stdout)

    def test_cli_json_is_a_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            before, after = self.build(tmp)
            r = subprocess.run([sys.executable, VERIFY_PATH, "--dirs", before, after, "--json"],
                               capture_output=True, text=True)
        rows = json.loads(r.stdout)
        self.assertIsInstance(rows, list)
        self.assertEqual({r["path"] for r in rows if r["status"] == "FAIL"}, {"broken.md"})

    def test_cli_passes_when_every_file_is_safe(self):
        with tempfile.TemporaryDirectory() as tmp:
            before, after = self.build(tmp)
            os.remove(os.path.join(after, "broken.md"))
            os.remove(os.path.join(before, "broken.md"))
            r = subprocess.run([sys.executable, VERIFY_PATH, "--dirs", before, after],
                               capture_output=True, text=True)
        self.assertEqual(r.returncode, 0)

    def test_flags_reach_every_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            before, after = self.build(tmp)
            r = subprocess.run([sys.executable, VERIFY_PATH, "--dirs", before, after,
                                "--allow-restructure", "--json"], capture_output=True, text=True)
            rows = {row["path"]: row for row in json.loads(r.stdout)}
        # The heading is untouched here, so --allow-restructure changes nothing;
        # what it proves is that the flag is accepted for a whole tree.
        self.assertEqual(rows["safe.md"]["status"], "PASS")

    def test_missing_tree_is_a_setup_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = subprocess.run([sys.executable, VERIFY_PATH, "--dirs", tmp,
                                os.path.join(tmp, "nope")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)

    def test_single_pair_still_works(self):
        with tempfile.TemporaryDirectory() as tmp:
            before = os.path.join(tmp, "b.md")
            after = os.path.join(tmp, "a.md")
            with open(before, "w", encoding="utf-8") as fh:
                fh.write("# T\n\nIt basically takes 2 hours.\n")
            with open(after, "w", encoding="utf-8") as fh:
                fh.write("# T\n\nIt takes 2 hours.\n")
            r = subprocess.run([sys.executable, VERIFY_PATH, before, after],
                               capture_output=True, text=True)
        self.assertEqual(r.returncode, 0)
        self.assertIn("PASS (md): edit is prose-only", r.stdout)


class TestDetect(unittest.TestCase):
    def test_detection(self):
        self.assertEqual(ve.detect("x.md"), "md")
        self.assertEqual(ve.detect("x.tsx"), "code")
        self.assertEqual(ve.detect("x.py"), "py")
        self.assertEqual(ve.detect("x.html"), "html")
        self.assertEqual(ve.detect("x.yml"), "yaml")
        self.assertEqual(ve.detect("x.json"), "json")
        self.assertIsNone(ve.detect("x.weird"))


if __name__ == "__main__":
    unittest.main()
