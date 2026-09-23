"""Tests for the session provider layer in scripts/respeak-config.py.

claude-code-session, when installed, writes a resolved file per session; the
resolver reads its `respeak` section as one tone-key layer between the folders
and $RESPEAK_CONFIG, accepted only from provider major SESSION_PROVIDER_MAJOR.
Every other case is an empty layer, at most one warning, never fatal.

Run: python3 -m unittest tests.test_provider_layer
"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
RESOLVER = os.path.join(REPO, "scripts", "respeak-config.py")

_spec = importlib.util.spec_from_file_location("respeak_config_provider", RESOLVER)
rc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rc)

SID = "sess-0001"
VERSION_OK = "%d.1.0" % rc.SESSION_PROVIDER_MAJOR
VERSION_BAD = "%d.4.2" % (rc.SESSION_PROVIDER_MAJOR - 1)


class ProviderLayer(unittest.TestCase):
    def setUp(self):
        self.root = os.path.realpath(tempfile.mkdtemp(prefix="respeak-provider-"))
        self.addCleanup(shutil.rmtree, self.root, True)
        self.home = os.path.join(self.root, "home")
        self.state = os.path.join(self.root, "state")
        self.project = os.path.join(self.home, "proj")
        os.makedirs(os.path.join(self.project, ".git"))
        os.makedirs(os.path.join(self.home, ".claude", "respeak"))
        self.doc = os.path.join(self.project, "a.md")
        open(self.doc, "w").close()

    def env(self, **extra):
        e = {"CLAUDE_CONFIG_DIR": os.path.join(self.home, ".claude"), "HOME": self.home,
             "XDG_STATE_HOME": self.state}
        e.update(extra)
        return e

    def write_resolved(self, body, sid=SID):
        d = os.path.join(self.state, "claude-code-session", "sessions", sid)
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, "resolved.json")
        with open(path, "w") as f:
            f.write(body if isinstance(body, str) else json.dumps(body))
        return path

    def resolved(self, version=VERSION_OK, respeak=None):
        return {"provider": {"plugin": "session", "version": version, "profile": "deep",
                             "resolved_at": "2026-09-22T12:00:00Z", "inputs": []},
                "respeak": respeak if respeak is not None
                else {"narrative": {"default_mode": "bluf", "tech_level": 2}}}

    def resolve(self, env=None, **kw):
        return rc.resolve(target=self.doc, plugin_root=REPO, env=env or self.env(),
                          walk_from=self.root, **kw)

    def test_accepted_file_is_a_layer(self):
        path = self.write_resolved(self.resolved())
        res = self.resolve(session_id=SID)
        self.assertEqual(rc.get_dotted(res.config, "narrative.default_mode"), "bluf")
        self.assertEqual(rc.get_dotted(res.config, "narrative.tech_level"), 2)
        self.assertEqual(res.origins["narrative.default_mode"], path + "#respeak")
        self.assertEqual(res.warnings, [])
        self.assertEqual(res.provider_line(),
                         "provider: claude-code-session %s profile deep" % VERSION_OK)
        kinds = [lay.kind for lay in res.layers]
        self.assertLess(kinds.index("session"), kinds.index("invocation"))

    def test_session_is_below_env_and_invocation(self):
        extra = os.path.join(self.root, "ci.yaml")
        with open(extra, "w") as f:
            f.write("narrative: {default_mode: technical}\n")
        self.write_resolved(self.resolved())
        res = self.resolve(session_id=SID, env=self.env(RESPEAK_CONFIG=extra))
        self.assertEqual(rc.get_dotted(res.config, "narrative.default_mode"), "technical")
        self.assertEqual(rc.get_dotted(res.config, "narrative.tech_level"), 2)
        res = self.resolve(session_id=SID, overrides={"narrative": {"tech_level": 5}})
        self.assertEqual(rc.get_dotted(res.config, "narrative.tech_level"), 5)

    def test_session_is_above_folders(self):
        with open(os.path.join(self.project, ".respeak.yaml"), "w") as f:
            f.write("narrative: {default_mode: eli5, tech_level: 4}\n")
        self.write_resolved(self.resolved())
        res = self.resolve(session_id=SID)
        self.assertEqual(rc.get_dotted(res.config, "narrative.default_mode"), "bluf")

    def test_session_is_tone_keys_only(self):
        self.write_resolved(self.resolved(respeak={"gate": {"enabled": True},
                                                   "narrative": {"default_mode": "bluf"}}))
        res = self.resolve(session_id=SID)
        self.assertEqual(rc.get_dotted(res.config, "narrative.default_mode"), "bluf")
        self.assertTrue(any("gate.enabled is project-only" in w for w in res.warnings))

    def test_wrong_major_is_an_empty_layer(self):
        self.write_resolved(self.resolved(version=VERSION_BAD))
        res = self.resolve(session_id=SID)
        self.assertEqual(rc.get_dotted(res.config, "narrative.default_mode"), "technical")
        self.assertNotIn("session", [lay.kind for lay in res.layers])
        self.assertEqual(len(res.warnings), 1)
        self.assertIn("is not major %d" % rc.SESSION_PROVIDER_MAJOR, res.warnings[0])
        self.assertEqual(res.provider_line(), "provider: none")

    def test_malformed_json_is_an_empty_layer(self):
        self.write_resolved("{not json")
        res = self.resolve(session_id=SID)
        self.assertEqual(rc.get_dotted(res.config, "narrative.default_mode"), "technical")
        self.assertEqual(len(res.warnings), 1)
        self.assertIn("unreadable", res.warnings[0])
        self.assertEqual(res.provider_line(), "provider: none")

    def test_absent_file_is_silent(self):
        res = self.resolve(session_id=SID)
        self.assertEqual(res.warnings, [])
        self.assertEqual(res.provider_line(), "provider: none")
        self.assertNotIn("session", [lay.kind for lay in res.layers])

    def test_no_session_id_is_silent(self):
        self.write_resolved(self.resolved())
        res = self.resolve()
        self.assertEqual(res.warnings, [])
        self.assertEqual(rc.get_dotted(res.config, "narrative.default_mode"), "technical")
        self.assertEqual(res.provider_line(), "provider: none")

    def test_session_id_from_the_environment(self):
        self.write_resolved(self.resolved())
        for var in rc.SESSION_ID_ENV:
            res = self.resolve(env=self.env(**{var: SID}))
            self.assertEqual(rc.get_dotted(res.config, "narrative.default_mode"), "bluf", var)
        # the pre-0.6.1 name alone is not read; --session wins over the environment
        old_name = "CLAUDE_CODE_SESSION_ID".replace("CODE_", "")
        res = self.resolve(env=self.env(**{old_name: SID}))
        self.assertEqual(res.provider_line(), "provider: none")
        res = self.resolve(session_id=SID, env=self.env(CLAUDE_CODE_SESSION_ID="other"))
        self.assertEqual(rc.get_dotted(res.config, "narrative.default_mode"), "bluf")

    def test_unsafe_session_id_is_refused(self):
        res = self.resolve(session_id="../escape")
        self.assertEqual(len(res.warnings), 1)
        self.assertIn("not a plain name", res.warnings[0])

    def test_accepted_without_a_respeak_section(self):
        body = self.resolved()
        del body["respeak"]
        self.write_resolved(body)
        res = self.resolve(session_id=SID)
        self.assertEqual(res.warnings, [])
        self.assertTrue(res.provider_line().startswith("provider: claude-code-session "))
        self.assertNotIn("session", [lay.kind for lay in res.layers])

    def test_file_is_never_written(self):
        path = self.write_resolved(self.resolved())
        def snapshot():
            with open(path) as f:
                return os.stat(path).st_mtime_ns, f.read()

        before = snapshot()
        self.resolve(session_id=SID)
        self.assertEqual(snapshot(), before)

    def test_explain_prints_the_provider_line(self):
        self.write_resolved(self.resolved())
        env = dict(os.environ)
        env.update(self.env())
        for var in rc.SESSION_ID_ENV + ("CLAUDE_PROJECT_DIR", "RESPEAK_CONFIG"):
            env.pop(var, None)

        def explain(*args):
            out = subprocess.run([sys.executable, RESOLVER, "explain", "--for", self.doc,
                                  "--plugin-root", REPO, "--walk-from", self.root] + list(args),
                                 capture_output=True, text=True, env=env)
            self.assertEqual(out.returncode, 0, out.stderr)
            return [l for l in out.stdout.splitlines() if l.startswith("provider: ")]

        self.assertEqual(explain("--session", SID),
                         ["provider: claude-code-session %s profile deep" % VERSION_OK])
        self.assertEqual(explain(), ["provider: none"])
        self.assertEqual(explain("--brief", "--session", SID),
                         ["provider: claude-code-session %s profile deep" % VERSION_OK])


if __name__ == "__main__":
    unittest.main()
