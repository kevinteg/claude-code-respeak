"""Tests for scripts/respeak-verify-edit.py — the edit-safety invariants.

Each format gets at least one edit that MUST pass (prose/comment-only) and
several that MUST fail (meaning-carrying content touched).

Run: python3 -m unittest discover tests -v
"""
import importlib.util
import os
import unittest

_spec = importlib.util.spec_from_file_location(
    "verify_edit",
    os.path.join(os.path.dirname(__file__), "..", "scripts", "respeak-verify-edit.py"),
)
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
