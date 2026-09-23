"""Tests for scripts/respeak-config.py — the layered configuration resolver.

Unit-level checks import the module (same style as test_measure_gate.py) and
call resolve() with an explicit env dict and walk_from, so nothing on the
developer's machine (a real ~/.claude/respeak/config.yaml, a stray
.respeak.yaml above the temp dir) leaks into a fixture. CLI-level checks
shell out with sys.executable, because the hooks and the skill call the
script, not a Python API. The examples/layered tree is pinned here so the
outcomes its README promises cannot drift.

Run: python3 -m unittest discover tests -v
"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
PLUGIN = os.path.join(REPO, "plugin")
RESOLVER = os.path.join(PLUGIN, "scripts", "respeak-config.py")
EXAMPLE = os.path.join(REPO, "examples", "layered")
EXAMPLE_PROJECT = os.path.join(EXAMPLE, "project")
EXAMPLE_CFGDIR = os.path.join(EXAMPLE, "home", ".claude")

_spec = importlib.util.spec_from_file_location("respeak_config", RESOLVER)
assert _spec is not None and _spec.loader is not None
rc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rc)


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(textwrap.dedent(text))


class Fixture:
    """A temp home (with CLAUDE_CONFIG_DIR) and a project under it."""

    def __init__(self):
        # realpath: the resolver reports symlink-resolved paths (/private/var on
        # macOS), so the fixture compares like with like
        self.root = os.path.realpath(tempfile.mkdtemp(prefix="respeak-layers-"))
        self.home = os.path.join(self.root, "home")
        self.cfgdir = os.path.join(self.home, ".claude")
        self.project = os.path.join(self.home, "code", "proj")
        os.makedirs(self.project)
        os.makedirs(os.path.join(self.cfgdir, "respeak"))

    def cleanup(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def env(self, **extra):
        e = {"CLAUDE_CONFIG_DIR": self.cfgdir, "HOME": self.home}
        e.update(extra)
        return e

    def resolve(self, target=None, project=None, overrides=None, env=None, walk_from=None):
        return rc.resolve(target=target or self.project, project=project or self.project,
                          plugin_root=PLUGIN, env=env or self.env(), overrides=overrides,
                          walk_from=walk_from or self.root)

    def user(self, text):
        write(os.path.join(self.cfgdir, "respeak", "config.yaml"), text)

    def proj(self, text):
        write(os.path.join(self.project, ".claude", "respeak", "config.yaml"), text)

    def local(self, text):
        write(os.path.join(self.project, ".claude", "respeak", "config.local.yaml"), text)

    def folder(self, rel, text, local=False):
        name = rc.FOLDER_LOCAL if local else rc.FOLDER_FILE
        write(os.path.join(self.project, rel, name), text)

    def doc(self, rel, text="# Doc\n\nThe cache is warm.\n"):
        p = os.path.join(self.project, rel)
        write(p, text)
        return p


def narrative(res, key):
    return rc.get_dotted(res.config, "narrative." + key)


class LayerPrecedence(unittest.TestCase):
    def setUp(self):
        self.fx = Fixture()
        self.addCleanup(self.fx.cleanup)

    def test_plugin_defaults_alone(self):
        res = self.fx.resolve()
        self.assertEqual(narrative(res, "default_mode"), "technical")
        self.assertEqual(narrative(res, "tech_level"), 3)
        self.assertEqual(narrative(res, "profile"), "peer-engineer")
        # the plugin layer's own profile: expands the fields the config
        # itself does not spell out
        self.assertEqual(narrative(res, "lexicon_access"), "expand-first-use")
        self.assertFalse(rc.get_dotted(res.config, "gate.enabled"))
        self.assertEqual(res.warnings, [])

    def test_userconfig_env_beats_plugin(self):
        env = self.fx.env(CLAUDE_PLUGIN_OPTION_DEFAULT_MODE="bluf",
                          CLAUDE_PLUGIN_OPTION_TECH_LEVEL="2",
                          CLAUDE_PLUGIN_OPTION_AUTO_NARRATIVE="true")
        res = self.fx.resolve(env=env)
        self.assertEqual(narrative(res, "default_mode"), "bluf")
        self.assertEqual(narrative(res, "tech_level"), 2)
        self.assertIs(narrative(res, "auto_narrative"), True)
        self.assertIn("userConfig", res.origins["narrative.default_mode"])

    def test_user_file_beats_userconfig_env(self):
        self.fx.user("narrative: {default_mode: eli5}\n")
        env = self.fx.env(CLAUDE_PLUGIN_OPTION_DEFAULT_MODE="bluf")
        res = self.fx.resolve(env=env)
        self.assertEqual(narrative(res, "default_mode"), "eli5")

    def test_project_beats_user_and_local_beats_project(self):
        self.fx.user("narrative: {default_mode: eli5, tech_level: 1}\n")
        self.fx.proj("narrative: {default_mode: bluf}\n")
        res = self.fx.resolve()
        self.assertEqual(narrative(res, "default_mode"), "bluf")
        self.assertEqual(narrative(res, "tech_level"), 1)  # untouched by project
        self.fx.local("narrative: {default_mode: technical}\n")
        res = self.fx.resolve()
        self.assertEqual(narrative(res, "default_mode"), "technical")

    def test_folder_nearest_wins(self):
        self.fx.folder("docs", "narrative: {tech_level: 2}\n")
        self.fx.folder("docs/exec", "narrative: {profile: exec}\n")
        deep = self.fx.doc("docs/exec/q.md")
        shallow = self.fx.doc("docs/y.md")
        res = self.fx.resolve(target=deep)
        self.assertEqual(narrative(res, "tech_level"), 1)
        self.assertEqual(narrative(res, "default_mode"), "bluf")
        res = self.fx.resolve(target=shallow)
        self.assertEqual(narrative(res, "tech_level"), 2)
        self.assertEqual(narrative(res, "default_mode"), "technical")

    def test_folder_local_beats_folder(self):
        self.fx.folder("docs", "narrative: {tech_level: 2}\n")
        self.fx.folder("docs", "narrative: {tech_level: 4}\n", local=True)
        res = self.fx.resolve(target=self.fx.doc("docs/a.md"))
        self.assertEqual(narrative(res, "tech_level"), 4)

    def test_ancestor_above_project_applies_below_project(self):
        write(os.path.join(self.fx.home, "code", ".respeak.yaml"),
              "narrative: {context_default: incident, tech_level: 2}\n")
        res = self.fx.resolve(target=self.fx.doc("a.md"))
        self.assertEqual(narrative(res, "context_default"), "incident")
        self.fx.proj("narrative: {context_default: routine}\n")
        res = self.fx.resolve(target=self.fx.doc("a.md"))
        self.assertEqual(narrative(res, "context_default"), "routine")
        self.assertEqual(narrative(res, "tech_level"), 2)  # ancestor still contributes

    def test_walk_from_limits_ancestors(self):
        write(os.path.join(self.fx.home, "code", ".respeak.yaml"), "narrative: {tech_level: 2}\n")
        res = self.fx.resolve(target=self.fx.doc("a.md"), walk_from=self.fx.project)
        self.assertEqual(narrative(res, "tech_level"), 3)

    def test_invocation_beats_everything(self):
        self.fx.folder("docs", "narrative: {default_mode: bluf}\n")
        res = self.fx.resolve(target=self.fx.doc("docs/a.md"),
                              overrides={"narrative": {"default_mode": "eli5"}})
        self.assertEqual(narrative(res, "default_mode"), "eli5")
        self.assertTrue(res.origins["narrative.default_mode"].startswith("invocation"))

    def test_respeak_config_env_files_beat_folders(self):
        extra = os.path.join(self.fx.root, "ci.yaml")
        write(extra, "gate: {fail_on: warn}\nnarrative: {tech_level: 4}\n")
        self.fx.folder("docs", "gate: {fail_on: none}\n")
        res = self.fx.resolve(target=self.fx.doc("docs/a.md"), env=self.fx.env(RESPEAK_CONFIG=extra))
        self.assertEqual(rc.get_dotted(res.config, "gate.fail_on"), "warn")
        self.assertEqual(narrative(res, "tech_level"), 4)

    def test_target_outside_project_keeps_project_layers_and_skips_its_folders(self):
        self.fx.proj("narrative: {default_mode: bluf}\n")
        self.fx.folder("", "narrative: {tech_level: 5}\n")  # project root folder file
        outside = os.path.join(self.fx.root, "elsewhere", "x.md")
        write(outside, "# x\n")
        res = self.fx.resolve(target=outside)
        self.assertEqual(narrative(res, "default_mode"), "bluf")
        self.assertEqual(narrative(res, "tech_level"), 3)
        kinds = [lay.kind for lay in res.applied]
        self.assertNotIn("folder", kinds)

    def test_missing_target_path_still_resolves_by_directory(self):
        self.fx.folder("out", "narrative: {default_mode: eli5}\n")
        res = self.fx.resolve(target=os.path.join(self.fx.project, "out", "not-yet-written.md"))
        self.assertEqual(narrative(res, "default_mode"), "eli5")


class MergeRules(unittest.TestCase):
    def setUp(self):
        self.fx = Fixture()
        self.addCleanup(self.fx.cleanup)

    def test_deep_merge_keeps_sibling_keys(self):
        self.fx.proj("narrative: {tone: {formality: 0.9}}\n")
        res = self.fx.resolve()
        tone = narrative(res, "tone")
        self.assertEqual(tone["formality"], 0.9)
        self.assertEqual(tone["directness"], 0.9)  # plugin default survives

    def test_append_lists_accumulate_and_dedupe(self):
        self.fx.user("gate: {allow: ['spine']}\n")
        self.fx.proj("gate: {allow: ['spine', 'load-bearing'], exclude: ['research/**']}\n")
        self.fx.folder("docs", "gate: {allow: ['delve']}\n")
        res = self.fx.resolve(target=self.fx.doc("docs/a.md"))
        self.assertEqual(rc.get_dotted(res.config, "gate.allow"), ["spine", "load-bearing", "delve"])
        self.assertEqual(rc.get_dotted(res.config, "gate.exclude"), ["research/**"])

    def test_other_lists_replace(self):
        self.fx.proj("style: {readability_metrics: [flesch_kincaid]}\n")
        res = self.fx.resolve()
        self.assertEqual(rc.get_dotted(res.config, "style.readability_metrics"), ["flesch_kincaid"])

    def test_project_only_keys_dropped_from_user_folder_and_scope(self):
        self.fx.user("gate: {enabled: true}\nshorthand: {ratification: auto}\n")
        self.fx.proj("scopes:\n  - paths: ['docs/**']\n    gate: {enabled: true, include: ['docs/**']}\n")
        self.fx.folder("docs", "gate: {enabled: true, exclude: ['x/**']}\nshorthand: {ratification: auto}\n")
        res = self.fx.resolve(target=self.fx.doc("docs/a.md"))
        self.assertFalse(rc.get_dotted(res.config, "gate.enabled"))
        self.assertEqual(rc.get_dotted(res.config, "gate.include"), ["**/*.md"])
        self.assertEqual(rc.get_dotted(res.config, "gate.exclude"), [])
        self.assertEqual(rc.get_dotted(res.config, "shorthand.ratification"), "human")
        dropped = [w for w in res.warnings if "project-only" in w]
        self.assertEqual(len(dropped), 7, res.warnings)

    def test_project_and_local_may_set_project_only_keys(self):
        self.fx.proj("gate: {enabled: true}\n")
        self.fx.local("shorthand: {legibility_floor: 0.7}\n")
        res = self.fx.resolve()
        self.assertTrue(rc.get_dotted(res.config, "gate.enabled"))
        self.assertEqual(rc.get_dotted(res.config, "shorthand.legibility_floor"), 0.7)
        self.assertEqual(res.warnings, [])

    def test_profile_expands_under_explicit_keys(self):
        self.fx.folder("docs", "narrative: {profile: exec, tech_level: 2}\n")
        res = self.fx.resolve(target=self.fx.doc("docs/a.md"))
        self.assertEqual(narrative(res, "default_mode"), "bluf")      # from exec
        self.assertEqual(narrative(res, "lexicon_access"), "forbidden")  # from exec
        self.assertEqual(narrative(res, "tech_level"), 2)             # explicit wins
        self.assertIn("(profile exec)", res.origins["narrative.default_mode"])

    def test_profile_defined_at_user_level_usable_in_a_folder(self):
        self.fx.user("profiles: {household: {tech_level: 2, default_mode: eli5, lexicon_access: forbidden}}\n")
        self.fx.folder("family", "narrative: {profile: household}\n")
        res = self.fx.resolve(target=self.fx.doc("family/a.md"))
        self.assertEqual(narrative(res, "default_mode"), "eli5")
        self.assertEqual(narrative(res, "tech_level"), 2)

    def test_unknown_profile_warns_and_changes_nothing(self):
        self.fx.folder("docs", "narrative: {profile: nobody}\n")
        res = self.fx.resolve(target=self.fx.doc("docs/a.md"))
        self.assertEqual(narrative(res, "default_mode"), "technical")
        self.assertTrue(any("not a known profile" in w for w in res.warnings))

    def test_unreadable_layer_is_skipped_with_warning(self):
        self.fx.folder("docs", "narrative: [not, a, mapping]\n")
        self.fx.folder("docs/deep", "narrative: {tech_level: 1\n")  # broken YAML
        res = self.fx.resolve(target=self.fx.doc("docs/deep/a.md"))
        self.assertEqual(narrative(res, "tech_level"), 3)
        self.assertTrue(any("unreadable" in w for w in res.warnings))


class Scopes(unittest.TestCase):
    def setUp(self):
        self.fx = Fixture()
        self.addCleanup(self.fx.cleanup)
        self.fx.proj("""\
            scopes:
              - paths: ["docs/**"]
                narrative: { tech_level: 2 }
              - paths: ["docs/exec/**", "reports/"]
                narrative: { profile: exec }
                gate: { fail_on: warn }
        """)

    def test_scopes_match_in_order_later_wins(self):
        res = self.fx.resolve(target=self.fx.doc("docs/exec/q.md"))
        self.assertEqual(narrative(res, "tech_level"), 1)
        self.assertEqual(narrative(res, "default_mode"), "bluf")
        self.assertEqual(rc.get_dotted(res.config, "gate.fail_on"), "warn")
        res = self.fx.resolve(target=self.fx.doc("docs/a.md"))
        self.assertEqual(narrative(res, "tech_level"), 2)
        self.assertEqual(rc.get_dotted(res.config, "gate.fail_on"), "error")
        res = self.fx.resolve(target=self.fx.doc("notes/a.md"))
        self.assertEqual(narrative(res, "tech_level"), 3)

    def test_trailing_slash_means_the_folder_and_its_contents(self):
        res = self.fx.resolve(target=self.fx.doc("reports/week.md"))
        self.assertEqual(narrative(res, "profile"), "exec")

    def test_directory_target_matches_scopes(self):
        os.makedirs(os.path.join(self.fx.project, "docs", "exec"), exist_ok=True)
        res = self.fx.resolve(target=os.path.join(self.fx.project, "docs", "exec"))
        self.assertEqual(narrative(res, "profile"), "exec")
        res = self.fx.resolve(target=self.fx.project)
        self.assertEqual(narrative(res, "tech_level"), 3)

    def test_folder_file_beats_scope(self):
        self.fx.folder("docs", "narrative: {tech_level: 4}\n")
        res = self.fx.resolve(target=self.fx.doc("docs/a.md"))
        self.assertEqual(narrative(res, "tech_level"), 4)

    def test_scope_applied_layers_are_listed(self):
        res = self.fx.resolve(target=self.fx.doc("docs/exec/q.md"))
        labels = [lay.label for lay in res.applied if lay.kind == "scope"]
        self.assertEqual(len(labels), 2)
        self.assertTrue(labels[0].endswith("#scopes[0]") and labels[1].endswith("#scopes[1]"))

    def test_malformed_scope_entries_warn(self):
        self.fx.folder("docs", "scopes:\n  - narrative: {tech_level: 1}\n  - paths: 3\n")
        res = self.fx.resolve(target=self.fx.doc("docs/a.md"))
        self.assertEqual(len([w for w in res.warnings if "scopes[" in w]), 2)


class UserScopes(unittest.TestCase):
    def setUp(self):
        self.fx = Fixture()
        self.addCleanup(self.fx.cleanup)

    def test_user_scopes_need_absolute_paths(self):
        target = self.fx.doc("docs/a.md")
        self.fx.user("scopes:\n  - paths: ['%s/**']\n    narrative: {tech_level: 5}\n"
                     "  - paths: ['docs/**']\n    narrative: {tech_level: 1}\n" % self.fx.project)
        res = self.fx.resolve(target=target)
        self.assertEqual(narrative(res, "tech_level"), 5)
        self.assertTrue(any("absolute or ~-prefixed" in w for w in res.warnings))

    def test_user_scope_sits_below_project_scope(self):
        target = self.fx.doc("docs/a.md")
        self.fx.user("scopes:\n  - paths: ['%s/**']\n    narrative: {tech_level: 5}\n" % self.fx.project)
        self.fx.proj("scopes:\n  - paths: ['docs/**']\n    narrative: {tech_level: 2}\n")
        res = self.fx.resolve(target=target)
        self.assertEqual(narrative(res, "tech_level"), 2)

    def test_mapping_key_is_never_clobbered_by_a_scalar(self):
        self.fx.folder("docs", "narrative: [not, a, mapping]\n")
        res = self.fx.resolve(target=self.fx.doc("docs/a.md"))
        self.assertEqual(narrative(res, "tech_level"), 3)
        self.assertTrue(any("is a mapping in a lower layer" in w for w in res.warnings))


class GlobSemantics(unittest.TestCase):
    def test_globs(self):
        m = rc.match_glob
        self.assertTrue(m("*.md", "a/b/c.md"))
        self.assertTrue(m("**/*.md", "a.md"))
        self.assertTrue(m("docs/**", "docs/a/b.md"))
        self.assertTrue(m("docs/**", "docs/"))
        self.assertFalse(m("docs/**", "docsx/a.md"))
        self.assertFalse(m("docs/**", ""))
        self.assertTrue(m("**", ""))
        self.assertTrue(m("docs/", "docs/a.md"))
        self.assertTrue(m("docs/*.md", "docs/a.md"))
        self.assertFalse(m("docs/*.md", "docs/sub/a.md"))
        self.assertTrue(m("docs/?.md", "docs/a.md"))
        self.assertFalse(m("docs/?.md", "docs/ab.md"))


class GateDecision(unittest.TestCase):
    def setUp(self):
        self.fx = Fixture()
        self.addCleanup(self.fx.cleanup)

    def test_off_by_default_and_user_cannot_enable(self):
        self.fx.user("gate: {enabled: true}\n")
        d = rc.gate_decision(self.fx.resolve(target=self.fx.doc("a.md")))
        self.assertFalse(d["applies"])
        self.assertIn("gate.enabled", d["reason"])

    def test_include_exclude_and_folder_fail_on(self):
        self.fx.proj("gate: {enabled: true, include: ['**/*.md'], exclude: ['notes/**']}\n")
        self.fx.folder("docs", "gate: {fail_on: warn}\n")
        d = rc.gate_decision(self.fx.resolve(target=self.fx.doc("docs/a.md")))
        self.assertTrue(d["applies"])
        self.assertEqual(d["fail_on"], "warn")
        self.assertEqual(d["rel_path"], "docs/a.md")
        d = rc.gate_decision(self.fx.resolve(target=self.fx.doc("a.md")))
        self.assertTrue(d["applies"])
        self.assertEqual(d["fail_on"], "error")
        d = rc.gate_decision(self.fx.resolve(target=self.fx.doc("notes/a.md")))
        self.assertFalse(d["applies"])
        self.assertIn("gate.exclude", d["reason"])
        d = rc.gate_decision(self.fx.resolve(target=self.fx.doc("a.txt")))
        self.assertFalse(d["applies"])

    def test_outside_project_never_applies(self):
        self.fx.proj("gate: {enabled: true}\n")
        outside = os.path.join(self.fx.root, "x.md")
        write(outside, "# x\n")
        d = rc.gate_decision(self.fx.resolve(target=outside))
        self.assertFalse(d["applies"])

    def test_bad_fail_on_falls_back_to_error(self):
        self.fx.proj("gate: {enabled: true, fail_on: loud}\n")
        res = self.fx.resolve(target=self.fx.doc("a.md"))
        d = rc.gate_decision(res)
        self.assertEqual(d["fail_on"], "error")
        self.assertTrue(any("fail_on" in w for w in res.warnings))

    def test_block_on_defaults_to_introduced(self):
        self.fx.proj("gate: {enabled: true}\n")
        res = self.fx.resolve(target=self.fx.doc("a.md"))
        d = rc.gate_decision(res)
        self.assertEqual(d["block_on"], "introduced")
        self.assertEqual(res.warnings, [])

    def test_any_layer_may_set_block_on(self):
        # same policy as fail_on: enforcement leniency is not project-only, so
        # a folder of pasted third-party text can ask for the whole-file check
        self.fx.proj("gate: {enabled: true}\n")
        self.fx.folder("docs", "gate: {block_on: any}\n")
        d = rc.gate_decision(self.fx.resolve(target=self.fx.doc("docs/a.md")))
        self.assertEqual(d["block_on"], "any")
        d = rc.gate_decision(self.fx.resolve(target=self.fx.doc("a.md")))
        self.assertEqual(d["block_on"], "introduced")
        self.fx.user("gate: {block_on: any}\n")
        d = rc.gate_decision(self.fx.resolve(target=self.fx.doc("a.md")))
        self.assertEqual(d["block_on"], "any")

    def test_bad_block_on_falls_back_to_introduced(self):
        self.fx.proj("gate: {enabled: true, block_on: everything}\n")
        res = self.fx.resolve(target=self.fx.doc("a.md"))
        d = rc.gate_decision(res)
        self.assertEqual(d["block_on"], "introduced")
        self.assertTrue(any("block_on" in w for w in res.warnings))


class ExampleTree(unittest.TestCase):
    """Pins the table in examples/layered/README.md."""

    def res(self, rel):
        env = {"CLAUDE_CONFIG_DIR": EXAMPLE_CFGDIR, "HOME": os.path.join(EXAMPLE, "home")}
        return rc.resolve(target=os.path.join(EXAMPLE_PROJECT, rel), project=EXAMPLE_PROJECT,
                          plugin_root=PLUGIN, env=env, walk_from=EXAMPLE)

    def check(self, rel, mode, tech, profile, formality, applies, fail_on):
        res = self.res(rel)
        d = rc.gate_decision(res)
        self.assertEqual((narrative(res, "default_mode"), narrative(res, "tech_level"),
                          narrative(res, "profile"), narrative(res, "tone")["formality"],
                          d["applies"], d["fail_on"]),
                         (mode, tech, profile, formality, applies, fail_on), rel)
        return res

    def test_readme_table(self):
        self.check("README.md", "technical", 3, "peer-engineer", 0.2, True, "error")
        self.check("docs/overview.md", "technical", 3, "peer-engineer", 0.2, True, "error")
        self.check("docs/exec/q3-summary.md", "bluf", 1, "exec", 0.8, True, "warn")
        self.check("docs/api/endpoints.md", "technical", 5, "author", 0.2, True, "error")
        self.check("reports/week-36.md", "bluf", 1, "exec", 0.2, True, "warn")
        res = self.check("notes/scratch.md", "technical", 5, "author", 0.2, False, "error")
        self.assertTrue(rc.get_dotted(res.config, "gate.enabled"))  # folder could not turn it off
        self.assertEqual(rc.get_dotted(res.config, "gate.allow"), ["spine", "load-bearing"])
        self.assertTrue(any("gate.enabled is project-only" in w for w in res.warnings))

    def test_user_file_wins_without_a_project(self):
        env = {"CLAUDE_CONFIG_DIR": EXAMPLE_CFGDIR, "HOME": os.path.join(EXAMPLE, "home")}
        nowhere = os.path.join(EXAMPLE, "home", "elsewhere")
        res = rc.resolve(target=nowhere, project=os.path.join(EXAMPLE, "no-such-project"),
                         plugin_root=PLUGIN, env=env, walk_from=EXAMPLE)
        self.assertEqual(narrative(res, "default_mode"), "bluf")
        self.assertEqual(narrative(res, "tech_level"), 2)


class CLI(unittest.TestCase):
    def setUp(self):
        self.fx = Fixture()
        self.addCleanup(self.fx.cleanup)
        self.env = dict(os.environ)
        # CLAUDE_CONFIG_DIR isolates the user layer; HOME stays real because
        # PyYAML may be installed in the interpreter's user site-packages.
        self.env["CLAUDE_CONFIG_DIR"] = self.fx.cfgdir
        self.env.pop("CLAUDE_PROJECT_DIR", None)
        self.env.pop("RESPEAK_CONFIG", None)
        # no session provider leaks in from the session running the suite
        self.env.pop("CLAUDE_CODE_SESSION_ID", None)
        self.env["XDG_STATE_HOME"] = os.path.join(self.fx.root, "state")
        for k in list(self.env):
            if k.startswith("CLAUDE_PLUGIN_OPTION_"):
                del self.env[k]

    def run_cli(self, *args):
        return subprocess.run([sys.executable, RESOLVER] + list(args) + ["--plugin-root", PLUGIN],
                              capture_output=True, text=True, env=self.env)

    def test_resolve_json_and_formats(self):
        self.fx.folder("docs", "narrative: {profile: exec}\n")
        doc = self.fx.doc("docs/a.md")
        common = ["--project", self.fx.project, "--for", doc, "--walk-from", self.fx.root]
        r = self.run_cli("resolve", "--format", "json", *common)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["narrative"]["default_mode"], "bluf")
        r = self.run_cli("resolve", "--format", "statusline", *common)
        self.assertEqual(r.stdout.strip(), "bluf/t1 exec @docs/.respeak.yaml")
        r = self.run_cli("resolve", "--format", "line", *common)
        self.assertIn("mode=bluf tech=1 profile=exec", r.stdout)
        r = self.run_cli("resolve", "--format", "yaml", "--mode", "eli5", "--set", "narrative.tech_level=4", *common)
        self.assertIn("default_mode: eli5", r.stdout)
        self.assertIn("tech_level: 4", r.stdout)

    def test_explain_lists_layers_and_origins(self):
        self.fx.proj("scopes:\n  - paths: ['docs/**']\n    narrative: {tech_level: 2}\n")
        self.fx.folder("docs", "narrative: {profile: exec}\ngate: {enabled: true}\n")
        doc = self.fx.doc("docs/a.md")
        r = self.run_cli("explain", "--project", self.fx.project, "--for", doc, "--walk-from", self.fx.root)
        self.assertEqual(r.returncode, 0, r.stderr)
        out = r.stdout
        self.assertIn("* plugin", out)
        self.assertIn("* project", out)
        self.assertIn("* scope          .claude/respeak/config.yaml#scopes[0]", out)
        self.assertIn("* folder         docs/.respeak.yaml", out)
        self.assertIn("user           %s (absent)" % os.path.join(self.fx.cfgdir, "respeak", "config.yaml"), out)
        self.assertIn("narrative.default_mode", out)
        self.assertIn("<- docs/.respeak.yaml (profile exec)", out)
        self.assertIn("gate.enabled is project-only; ignored", out)
        self.assertIn("gate: enabled=false", out)
        self.assertIn("block_on=introduced", out)

    def test_gate_subcommand_writes_config(self):
        self.fx.proj("gate: {enabled: true}\n")
        self.fx.folder("docs", "gate: {fail_on: warn, block_on: any}\n")
        doc = self.fx.doc("docs/a.md")
        out_cfg = os.path.join(self.fx.root, "resolved.yaml")
        r = self.run_cli("gate", "--project", self.fx.project, "--for", doc,
                         "--walk-from", self.fx.root, "--write-config", out_cfg)
        self.assertEqual(r.returncode, 0, r.stderr)
        d = json.loads(r.stdout)
        self.assertTrue(d["applies"])
        self.assertEqual(d["fail_on"], "warn")
        self.assertEqual(d["block_on"], "any")   # the gate hook reads it from here
        self.assertTrue(os.path.isfile(out_cfg))
        with open(out_cfg) as f:
            self.assertIn("fail_on: warn", f.read())

    def test_gate_committed_reads_the_project_file_only(self):
        # ADV6-1, ADV6-2: the CI verdict drops gate.* from every layer but the
        # plugin defaults and the project file (its scopes included), and says so.
        self.fx.proj("gate: {enabled: true}\n"
                     "scopes:\n  - paths: ['docs/**']\n    gate: {allow: ['x']}\n")
        write(os.path.join(self.fx.project, ".claude", "respeak", "config.local.yaml"),
              "gate: {block_on: any}\n")
        self.fx.folder("docs", "gate: {fail_on: none, allow: ['.*']}\n")
        env_cfg = os.path.join(self.fx.root, "env.yaml")
        write(env_cfg, "gate: {enabled: false}\n")
        self.env["RESPEAK_CONFIG"] = env_cfg
        doc = self.fx.doc("docs/a.md")
        out_cfg = os.path.join(self.fx.root, "resolved.yaml")
        common = ["--project", self.fx.project, "--for", doc, "--walk-from", self.fx.root,
                  "--set", "gate.fail_on=warn", "--write-config", out_cfg]
        d = json.loads(self.run_cli("gate", *common).stdout)
        self.assertFalse(d["applies"])            # the open form: RESPEAK_CONFIG turned it off
        self.assertNotIn("dropped", d)
        r = self.run_cli("gate", "--committed", *common)
        self.assertEqual(r.returncode, 0, r.stderr)
        d = json.loads(r.stdout)
        self.assertTrue(d["committed"])
        self.assertTrue(d["applies"])
        self.assertEqual((d["fail_on"], d["block_on"]), ("error", "introduced"))
        dropped = [x.rsplit(": ", 1)[1] for x in d["dropped"]]
        self.assertEqual(sorted(dropped), ["gate.allow", "gate.block_on", "gate.enabled",
                                           "gate.fail_on", "gate.fail_on"])
        self.assertTrue(any(x.startswith(env_cfg) for x in d["dropped"]))
        self.assertTrue(any("invocation" in x for x in d["dropped"]))
        with open(out_cfg) as f:
            g = rc.yaml.safe_load(f)["gate"]
        self.assertIn("x", g["allow"])             # the project scope's allow stands
        self.assertNotIn(".*", g["allow"])

    def test_validate_accepts_block_on_in_any_layer(self):
        folder = os.path.join(self.fx.project, "docs", ".respeak.yaml")
        write(folder, "gate: {block_on: any}\n")
        r = self.run_cli("validate", folder)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("[folder]: ok", r.stdout)
        self.assertNotIn("block_on", r.stdout)

    def test_validate_policy_and_shape(self):
        good = os.path.join(self.fx.project, "docs", ".respeak.yaml")
        write(good, "narrative: {profile: exec}\n")
        bad = os.path.join(self.fx.project, "notes", ".respeak.yaml")
        write(bad, "gate: {enabled: true}\nscopes:\n  - narrative: {tech_level: 1}\n")
        r = self.run_cli("validate", good)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("[folder]: ok", r.stdout)
        r = self.run_cli("validate", bad)
        self.assertEqual(r.returncode, 1)
        self.assertIn("project-only", r.stdout)
        self.assertIn("needs a `paths` list", r.stdout)
        user = os.path.join(self.fx.cfgdir, "respeak", "config.yaml")
        write(user, "scopes:\n  - paths: ['docs/**']\n    narrative: {tech_level: 1}\n")
        r = self.run_cli("validate", user)
        self.assertEqual(r.returncode, 1)
        self.assertIn("[user]", r.stdout)
        self.assertIn("absolute or ~-prefixed", r.stdout)
        r = self.run_cli("validate", os.path.join(PLUGIN, "config", "respeak.config.yaml"),
                         os.path.join(PLUGIN, "config", "project-seed.yaml"))
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_project_discovery_without_flag(self):
        self.fx.proj("narrative: {default_mode: bluf}\n")
        doc = self.fx.doc("docs/a.md")
        r = self.run_cli("resolve", "--for", doc, "--format", "line", "--walk-from", self.fx.root)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("mode=bluf", r.stdout)


if __name__ == "__main__":
    unittest.main()


# ---------------------------------------------------------------------------
# v0.4.1: regressions for the adversarial-review findings (docs/config-layers.md)
# ---------------------------------------------------------------------------

class Discovery(unittest.TestCase):
    """One project-root rule for every consumer."""

    def setUp(self):
        self.fx = Fixture()
        self.addCleanup(self.fx.cleanup)

    def test_user_file_is_never_a_project_file(self):
        # the headline recipe: a user file, a repo with .git and no project config
        self.fx.user("narrative: {default_mode: bluf}\ngate: {enabled: true, include: ['**/*.md']}\n"
                     "shorthand: {ratification: auto}\n")
        os.makedirs(os.path.join(self.fx.project, ".git"))
        doc = self.fx.doc("README.md")
        env = self.fx.env()
        res = rc.resolve(target=doc, project=None, plugin_root=PLUGIN, env=env, walk_from=self.fx.root)
        self.assertEqual(res.project, self.fx.project)          # the .git root, not $HOME
        self.assertIn(".git", res.project_how)
        self.assertEqual(narrative(res, "default_mode"), "bluf")  # tone from the user file applies
        self.assertFalse(rc.get_dotted(res.config, "gate.enabled"))
        self.assertEqual(rc.get_dotted(res.config, "shorthand.ratification"), "human")
        kinds = [lay.kind for lay in res.applied]
        self.assertEqual(kinds.count("project"), 0)
        self.assertFalse(rc.gate_decision(res)["applies"])

    def test_launch_dir_equal_to_home_does_not_promote_the_user_file(self):
        self.fx.user("gate: {enabled: true}\n")
        doc = self.fx.doc("a.md")
        for kw in ({"launch_dir": self.fx.home}, {"project": self.fx.home}):
            res = rc.resolve(target=doc, plugin_root=PLUGIN, env=self.fx.env(), walk_from=self.fx.root, **kw)
            self.assertFalse(rc.get_dotted(res.config, "gate.enabled"), kw)
            self.assertEqual([lay.kind for lay in res.applied].count("project"), 0, kw)
            self.assertTrue(any("not re-applied at project grade" in w for w in res.warnings), kw)
        env = self.fx.env(CLAUDE_PROJECT_DIR=self.fx.home)
        res = rc.resolve(target=doc, plugin_root=PLUGIN, env=env, walk_from=self.fx.root)
        self.assertFalse(rc.get_dotted(res.config, "gate.enabled"))

    def test_nearest_project_config_wins_for_every_consumer(self):
        # monorepo: outer project config + nested package config
        self.fx.proj("narrative: {default_mode: technical}\ngate: {enabled: true}\n")
        inner = os.path.join(self.fx.project, "pkg")
        write(os.path.join(inner, ".claude", "respeak", "config.yaml"), "narrative: {default_mode: bluf}\n")
        doc = self.fx.doc("pkg/a.md")
        hook_side = rc.resolve(target=doc, plugin_root=PLUGIN, walk_from=self.fx.root,
                               env=self.fx.env(CLAUDE_PROJECT_DIR=self.fx.project))
        cli_side = rc.resolve(target=doc, plugin_root=PLUGIN, walk_from=self.fx.root, env=self.fx.env())
        for res in (hook_side, cli_side):
            self.assertEqual(res.project, inner)
            self.assertEqual(narrative(res, "default_mode"), "bluf")
            self.assertFalse(rc.get_dotted(res.config, "gate.enabled"))  # the inner project never opted in
        # a file outside pkg/ still belongs to the outer project
        outer_doc = self.fx.doc("a.md")
        res = rc.resolve(target=outer_doc, plugin_root=PLUGIN, walk_from=self.fx.root, env=self.fx.env())
        self.assertEqual(res.project, self.fx.project)
        self.assertTrue(rc.gate_decision(res)["applies"])

    def test_parent_project_config_governs_a_repo_launched_below_it(self):
        # ~/src/.claude/respeak/config.yaml + session launched in ~/src/repo
        code = os.path.join(self.fx.home, "code")
        write(os.path.join(code, ".claude", "respeak", "config.yaml"), "gate: {enabled: true}\n")
        os.makedirs(os.path.join(self.fx.project, ".git"))
        doc = self.fx.doc("docs/x.md")
        for env in (self.fx.env(CLAUDE_PROJECT_DIR=self.fx.project), self.fx.env()):
            res = rc.resolve(target=doc, plugin_root=PLUGIN, walk_from=self.fx.root, env=env)
            self.assertEqual(res.project, code)
            self.assertTrue(rc.gate_decision(res)["applies"])

    def test_launch_dir_is_the_fallback_when_no_project_config_exists(self):
        doc = self.fx.doc("docs/x.md")
        res = rc.resolve(target=doc, plugin_root=PLUGIN, walk_from=self.fx.root, env=self.fx.env(),
                         launch_dir=self.fx.project)
        self.assertEqual(res.project, self.fx.project)
        self.assertIn("launch", res.project_how)
        # launched in a subdirectory of a repo with no config: that subdirectory is the project
        res = rc.resolve(target=doc, plugin_root=PLUGIN, walk_from=self.fx.root, env=self.fx.env(),
                         launch_dir=os.path.join(self.fx.project, "docs"))
        self.assertEqual(res.project, os.path.join(self.fx.project, "docs"))

    def test_symlinked_spellings_resolve_identically(self):
        self.fx.proj("gate: {enabled: true}\n")
        self.fx.folder("docs", "narrative: {profile: exec}\n")
        doc = self.fx.doc("docs/a.md")
        link = os.path.join(self.fx.root, "link")
        os.symlink(self.fx.home, link)
        via_link = os.path.join(link, "code", "proj", "docs", "a.md")
        combos = [(doc, self.fx.project), (via_link, self.fx.project),
                  (doc, os.path.join(link, "code", "proj")), (via_link, os.path.join(link, "code", "proj"))]
        for target, project in combos:
            res = rc.resolve(target=target, project=project, plugin_root=PLUGIN, walk_from=self.fx.root,
                             env=self.fx.env())
            d = rc.gate_decision(res)
            self.assertTrue(d["applies"], (target, project, d))
            self.assertEqual(d["rel_path"], "docs/a.md")
            self.assertEqual(narrative(res, "profile"), "exec")  # the folder file is found on either spelling

    def test_outside_target_keeps_ancestors_below_the_project(self):
        write(os.path.join(self.fx.home, "code", ".respeak.yaml"), "narrative: {default_mode: eli5}\n")
        self.fx.proj("narrative: {default_mode: technical, tech_level: 3}\n")
        outside = os.path.join(self.fx.home, "code", "other", "x.md")
        write(outside, "# x\n")
        res = self.fx.resolve(target=outside)
        self.assertEqual(narrative(res, "default_mode"), "technical")
        kinds = [lay.kind for lay in res.applied]
        self.assertLess(kinds.index("ancestor"), kinds.index("project"))
        # a .respeak.yaml in the outside directory itself is nearer than the project
        write(os.path.join(self.fx.home, "code", "other", ".respeak.yaml"), "narrative: {default_mode: bluf}\n")
        res = self.fx.resolve(target=outside)
        self.assertEqual(narrative(res, "default_mode"), "bluf")
        self.assertFalse(rc.gate_decision(res)["applies"])


class ProfilesAndGlobs(unittest.TestCase):
    def setUp(self):
        self.fx = Fixture()
        self.addCleanup(self.fx.cleanup)

    def test_partial_profile_override_in_the_same_layer_keeps_the_other_fields(self):
        self.fx.proj("profiles: {exec: {tech_level: 2}}\nnarrative: {profile: exec}\n")
        res = self.fx.resolve(target=self.fx.doc("a.md"))
        self.assertEqual(narrative(res, "default_mode"), "bluf")
        self.assertEqual(narrative(res, "tech_level"), 2)
        self.assertEqual(narrative(res, "lexicon_access"), "forbidden")
        # same outcome whichever layer carries the partial profile
        self.fx.proj("narrative: {profile: exec}\n")
        self.fx.user("profiles: {exec: {tech_level: 2}}\n")
        res = self.fx.resolve(target=self.fx.doc("a.md"))
        self.assertEqual((narrative(res, "default_mode"), narrative(res, "tech_level")), ("bluf", 2))

    def test_unknown_profile_leaves_no_trace(self):
        self.fx.folder("docs", "narrative: {profile: nobody, tech_level: 2}\n")
        res = self.fx.resolve(target=self.fx.doc("docs/a.md"))
        self.assertEqual(narrative(res, "profile"), "peer-engineer")  # the plugin default, not "nobody"
        self.assertEqual(narrative(res, "tech_level"), 2)             # the explicit key still applies

    def test_bare_name_scope_matches_the_directory_and_its_contents(self):
        self.fx.proj("scopes:\n  - paths: ['exec']\n    narrative: {profile: exec}\n")
        res = self.fx.resolve(target=self.fx.doc("docs/exec/q.md"))
        self.assertEqual(narrative(res, "profile"), "exec")
        res = self.fx.resolve(target=self.fx.doc("docs/executive/q.md"))
        self.assertEqual(narrative(res, "profile"), "peer-engineer")
        m = rc.match_glob
        self.assertTrue(m("exec", "docs/exec"))
        self.assertTrue(m("exec", "docs/exec/deep/q.md"))
        self.assertFalse(m("exec", "docs/exec.md"))

    def test_explicit_empty_include_covers_nothing(self):
        self.fx.proj("gate: {enabled: true, include: []}\n")
        d = rc.gate_decision(self.fx.resolve(target=self.fx.doc("a.md")))
        self.assertFalse(d["applies"])
        self.assertIn("gate.include", d["reason"])

    def test_gate_covers_markdown_extensions_only(self):
        self.fx.proj("gate: {enabled: true, include: ['**/*']}\n")
        for name, expect in (("a.md", True), ("a.markdown", True), ("a.mdx", True), ("a.txt", False), ("a.py", False)):
            d = rc.gate_decision(self.fx.resolve(target=self.fx.doc(name)))
            self.assertEqual(d["applies"], expect, name)
            if not expect:
                self.assertIn("Markdown", d["reason"])

    def test_set_parsing(self):
        ns = type("A", (), {})()
        ns.mode = ns.profile = ns.context = None
        ns.set = ["gate.allow=spine", "narrative.tone.formality=0.9", "narrative.auto_narrative=yes", "gate.include=docs/**"]
        ov = rc.parse_overrides(ns)
        self.assertEqual(ov["gate"]["allow"], ["spine"])
        self.assertEqual(ov["gate"]["include"], ["docs/**"])
        self.assertEqual(ov["narrative"]["tone"]["formality"], 0.9)
        self.assertEqual(ov["narrative"]["auto_narrative"], "yes")  # not the YAML-1.1 boolean

    def test_user_scope_written_through_a_symlink_still_matches(self):
        link = os.path.join(self.fx.root, "link")
        os.symlink(self.fx.home, link)
        self.fx.user("scopes:\n  - paths: ['%s/code/proj/**']\n    narrative: {tech_level: 5}\n" % link)
        res = self.fx.resolve(target=self.fx.doc("docs/a.md"))
        self.assertEqual(narrative(res, "tech_level"), 5)


class ExplainOutput(unittest.TestCase):
    def setUp(self):
        self.fx = Fixture()
        self.addCleanup(self.fx.cleanup)

    def test_warnings_precede_overrides_and_brief_is_short(self):
        self.fx.folder("docs", "narrative: {profile: exec}\ngate: {enabled: true}\n")
        res = self.fx.resolve(target=self.fx.doc("docs/a.md"))
        full = rc.fmt_explain(res, rc.gate_decision(res))
        self.assertLess(full.index("warnings:"), full.index("overrides (key"))
        brief = rc.fmt_brief(res, rc.gate_decision(res))
        self.assertLessEqual(len(brief.splitlines()), 8)
        self.assertIn("warning: docs/.respeak.yaml: gate.enabled is project-only; ignored", brief)
        self.assertIn("mode=bluf tech_level=1 profile=exec", brief)
        self.assertIn("(--project)", brief)
        self.assertIn("folder docs/.respeak.yaml", brief)


class CLIv041(unittest.TestCase):
    def setUp(self):
        self.fx = Fixture()
        self.addCleanup(self.fx.cleanup)
        self.env = dict(os.environ)
        self.env["CLAUDE_CONFIG_DIR"] = self.fx.cfgdir
        for k in ("CLAUDE_PROJECT_DIR", "RESPEAK_CONFIG"):
            self.env.pop(k, None)

    def run_cli(self, *args, **kw):
        env = dict(self.env); env.update(kw.get("env", {}))
        return subprocess.run([sys.executable, RESOLVER] + list(args) + ["--plugin-root", PLUGIN],
                              capture_output=True, text=True, env=env)

    def test_launch_dir_flag_and_env_agree(self):
        self.fx.proj("gate: {enabled: true}\n")
        doc = self.fx.doc("docs/a.md")
        a = self.run_cli("gate", "--for", doc, "--launch-dir", os.path.join(self.fx.project, "docs"), "--walk-from", self.fx.root)
        b = self.run_cli("gate", "--for", doc, "--walk-from", self.fx.root, env={"CLAUDE_PROJECT_DIR": os.path.join(self.fx.project, "docs")})
        self.assertEqual(a.returncode, 0, a.stderr)
        self.assertEqual(json.loads(a.stdout)["applies"], True)   # nearest project config beats the launch dir
        self.assertEqual(json.loads(a.stdout)["applies"], json.loads(b.stdout)["applies"])
        r = self.run_cli("explain", "--brief", "--for", doc, "--launch-dir", "", "--walk-from", self.fx.root)
        self.assertEqual(r.returncode, 0, r.stderr)               # an empty --launch-dir is "not given"
        self.assertIn("nearest .claude/respeak/config.yaml", r.stdout)


# ---------------------------------------------------------------------------
# v0.4.3: second re-break / regression round
# ---------------------------------------------------------------------------

def _case_variant(path):
    """A differently cased spelling of the same path on a case-insensitive
    filesystem, or None when the volume is case-sensitive."""
    head, tail = os.path.split(path)
    alt = os.path.join(head, tail.upper() if tail != tail.upper() else tail.lower())
    return alt if alt != path and os.path.exists(alt) and os.path.samefile(alt, path) else None


class V043Paths(unittest.TestCase):
    def setUp(self):
        self.fx = Fixture()
        self.addCleanup(self.fx.cleanup)

    def test_symlinked_config_dir_is_never_a_project(self):
        # dotfiles-managed ~/.claude -> dot/claude; the user file enables the gate
        real_dir = os.path.join(self.fx.home, "dot", "claude")
        write(os.path.join(real_dir, "respeak", "config.yaml"), "gate: {enabled: true}\nshorthand: {ratification: auto}\n")
        link = os.path.join(self.fx.home, "claude-link")
        os.symlink(real_dir, link)
        doc = self.fx.doc("docs/a.md")  # repo with no config, no .git
        env = {"CLAUDE_CONFIG_DIR": link, "CLAUDE_PROJECT_DIR": self.fx.project}
        res = rc.resolve(target=doc, plugin_root=PLUGIN, env=env, walk_from=self.fx.root)
        self.assertEqual(res.project, self.fx.project)
        self.assertFalse(rc.get_dotted(res.config, "gate.enabled"))
        self.assertEqual(rc.get_dotted(res.config, "shorthand.ratification"), "human")
        self.assertEqual([lay.kind for lay in res.applied].count("project"), 0)
        # and with the link's parent as the candidate project root (a session launched in ~)
        res = rc.resolve(target=doc, plugin_root=PLUGIN, env={"CLAUDE_CONFIG_DIR": link}, walk_from=self.fx.root,
                         launch_dir=self.fx.home)
        self.assertFalse(rc.get_dotted(res.config, "gate.enabled"))

    def test_symlink_inside_project_pointing_outside_is_still_gated(self):
        self.fx.proj("gate: {enabled: true}\n")
        outside = os.path.join(self.fx.root, "outside")
        write(os.path.join(outside, "ext.md"), "# x\n")
        os.symlink(os.path.join(outside, "ext.md"), os.path.join(self.fx.project, "ext.md"))
        res = self.fx.resolve(target=os.path.join(self.fx.project, "ext.md"))
        d = rc.gate_decision(res)
        self.assertTrue(d["applies"], d)
        self.assertEqual(d["rel_path"], "ext.md")
        # a symlinked directory too, and its folder file is read through the link
        shared = os.path.join(self.fx.root, "shared", "docs")
        write(os.path.join(shared, "n.md"), "# n\n")
        write(os.path.join(shared, ".respeak.yaml"), "narrative: {profile: exec}\n")
        os.symlink(shared, os.path.join(self.fx.project, "docs"))
        res = self.fx.resolve(target=os.path.join(self.fx.project, "docs", "n.md"))
        d = rc.gate_decision(res)
        self.assertTrue(d["applies"], d)
        self.assertEqual(d["rel_path"], "docs/n.md")
        self.assertEqual(narrative(res, "profile"), "exec")

    def test_case_variant_spelling_names_the_same_project(self):
        alt_project = _case_variant(self.fx.project)
        if not alt_project:
            self.skipTest("case-sensitive filesystem")
        self.fx.proj("gate: {enabled: true}\n")
        self.fx.folder("docs", "narrative: {profile: exec}\n")
        doc = self.fx.doc("docs/a.md")
        # --project spelled differently from the target
        res = rc.resolve(target=doc, project=alt_project, plugin_root=PLUGIN, env=self.fx.env(), walk_from=self.fx.root)
        d = rc.gate_decision(res)
        self.assertTrue(d["applies"], d)
        self.assertEqual(d["rel_path"], "docs/a.md")
        self.assertEqual(narrative(res, "profile"), "exec")
        # the user config dir spelled differently must still be excluded from discovery
        self.fx.user("gate: {enabled: true}\n")
        alt_home = _case_variant(self.fx.home)
        if alt_home:
            os.makedirs(os.path.join(self.fx.project, ".git"), exist_ok=True)
            plain = self.fx.doc("b.md")
            alt_doc = os.path.join(alt_home, "code", "proj", "b.md")
            res = rc.resolve(target=alt_doc, plugin_root=PLUGIN, env=self.fx.env(), walk_from=self.fx.root)
            self.assertNotEqual(rc.path_key(res.project), rc.path_key(self.fx.home))
            self.assertFalse(rc.get_dotted(res.config, "gate.enabled") and not
                             rc.get_dotted(res.config, "gate.include"))  # only the project could enable it
        # outside target with a case-variant project: ancestors stay below the project
        write(os.path.join(self.fx.home, "code", ".respeak.yaml"), "narrative: {default_mode: eli5}\n")
        self.fx.proj("narrative: {default_mode: technical}\ngate: {enabled: true}\n")
        outside = os.path.join(self.fx.home, "code", "other", "x.md")
        write(outside, "# x\n")
        res = rc.resolve(target=outside, project=alt_project, plugin_root=PLUGIN, env=self.fx.env(), walk_from=self.fx.root)
        self.assertEqual(narrative(res, "default_mode"), "technical")


class V043Merge(unittest.TestCase):
    def setUp(self):
        self.fx = Fixture()
        self.addCleanup(self.fx.cleanup)

    def test_bool_words_on_boolean_keys(self):
        self.fx.proj("gate: {enabled: true}\nnarrative: {auto_narrative: true}\n")
        doc = self.fx.doc("a.md")
        for word, expect in (("no", False), ("off", False), ("false", False), ("yes", True), ("on", True), ("0", False)):
            res = self.fx.resolve(target=doc, overrides={"gate": {"enabled": word}})
            self.assertIs(rc.get_dotted(res.config, "gate.enabled"), expect, word)
        res = self.fx.resolve(target=doc, overrides={"narrative": {"auto_narrative": "off"}})
        self.assertIs(narrative(res, "auto_narrative"), False)
        res = self.fx.resolve(target=doc, overrides={"gate": {"enabled": "maybe"}})
        self.assertIs(rc.get_dotted(res.config, "gate.enabled"), True)
        self.assertTrue(any("not a boolean spelling" in w for w in res.warnings))

    def test_null_profile_entry_does_not_delete_the_profile(self):
        self.fx.proj("profiles: {exec: null}\nnarrative: {profile: exec}\n")
        res = self.fx.resolve(target=self.fx.doc("a.md"))
        self.assertEqual(narrative(res, "default_mode"), "bluf")
        self.assertEqual(narrative(res, "tech_level"), 1)
        self.assertFalse(any("not a known profile" in w for w in res.warnings), res.warnings)
        self.assertTrue(any("is a mapping in a lower layer" in w for w in res.warnings))

    def test_non_string_profile_is_dropped_with_a_warning(self):
        self.fx.local("narrative: {profile: 123}\n")
        res = self.fx.resolve(target=self.fx.doc("a.md"))
        self.assertEqual(narrative(res, "profile"), "peer-engineer")
        self.assertTrue(any("not a known profile" in w for w in res.warnings))

    def test_set_glob_values_are_literal(self):
        ns = type("A", (), {})(); ns.mode = ns.profile = ns.context = None
        ns.set = ["gate.include=**/*.md", "gate.exclude=*.tmp.md", "gate.allow=[a-z"]
        ov = rc.parse_overrides(ns)
        self.assertEqual(ov["gate"]["include"], ["**/*.md"])
        self.assertEqual(ov["gate"]["exclude"], ["*.tmp.md"])
        self.assertEqual(ov["gate"]["allow"], ["[a-z"])


class V043CLI(unittest.TestCase):
    def setUp(self):
        self.fx = Fixture()
        self.addCleanup(self.fx.cleanup)
        self.env = dict(os.environ)
        self.env["CLAUDE_CONFIG_DIR"] = self.fx.cfgdir
        for k in ("CLAUDE_PROJECT_DIR", "RESPEAK_CONFIG"):
            self.env.pop(k, None)

    def run_cli(self, *args):
        return subprocess.run([sys.executable, RESOLVER] + list(args) + ["--plugin-root", PLUGIN],
                              capture_output=True, text=True, env=self.env)

    def test_empty_launch_dir_means_not_given(self):
        self.fx.proj("narrative: {default_mode: bluf}\n")
        doc = self.fx.doc("a.md")
        for extra in (["--launch-dir", ""], ["--launch-dir"]):
            r = self.run_cli("resolve", "--for", doc, "--format", "line", "--walk-from", self.fx.root, *extra)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("mode=bluf", r.stdout)
        r = self.run_cli("resolve", "--for", doc, "--launch-dir", "", "--mode", "eli5", "--format", "line", "--walk-from", self.fx.root)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("mode=eli5", r.stdout)

    def test_resolve_out_writes_the_file(self):
        doc = self.fx.doc("a.md")
        out = os.path.join(self.fx.root, "resolved.yaml")
        r = self.run_cli("resolve", "--for", doc, "--format", "yaml", "--out", out, "--walk-from", self.fx.root)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, "")
        with open(out) as f:
            self.assertIn("default_mode: technical", f.read())

    def test_validate_accepts_the_common_flags(self):
        f = os.path.join(self.fx.project, "docs", ".respeak.yaml")
        write(f, "narrative: {profile: exec}\n")
        r = self.run_cli("validate", "--launch-dir", self.fx.project, "--project", self.fx.project, f)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_set_glob_and_bool_words_via_cli(self):
        self.fx.proj("gate: {enabled: true}\n")
        doc = self.fx.doc("docs/a.md")
        r = self.run_cli("gate", "--for", doc, "--set", "gate.include=**/*.md", "--walk-from", self.fx.root)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        self.assertTrue(json.loads(r.stdout)["applies"])
        r = self.run_cli("gate", "--for", doc, "--set", "gate.enabled=no", "--walk-from", self.fx.root)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(json.loads(r.stdout)["enabled"])
