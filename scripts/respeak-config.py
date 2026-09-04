#!/usr/bin/env python3
"""respeak-config.py — resolve respeak's layered configuration for a path.

Usage:
  respeak-config.py resolve  [--project DIR] [--for PATH] [--format yaml|json|line|statusline]
                             [--mode M] [--profile P] [--context C] [--set key=value]...
  respeak-config.py explain  [--project DIR] [--for PATH] [--mode ...] [--set ...]
  respeak-config.py gate     [--project DIR] --for FILE [--write-config PATH]
  respeak-config.py validate FILE... [--kind plugin|user|project|folder]

The contract, with worked examples, is docs/config-layers.md. In one screen:

  layer         file                                               may set
  1 plugin      ${CLAUDE_PLUGIN_ROOT}/config/respeak.config.yaml   everything
  2 userConfig  CLAUDE_PLUGIN_OPTION_{DEFAULT_MODE,TECH_LEVEL,      narrative.default_mode,
                AUTO_NARRATIVE} (claude plugin install --config)    .tech_level, .auto_narrative
  3 user        ${CLAUDE_CONFIG_DIR:-~/.claude}/respeak/config.yaml tone keys
  4 ancestors   <dir>/.respeak.yaml above the project root          tone keys
  5 project     <project>/.claude/respeak/config.yaml               everything
  6 local       <project>/.claude/respeak/config.local.yaml         everything
  7 scopes      `scopes:` entries of any file above whose `paths`   tone keys
                match the target, applied right after their file
  8 folders     <dir>/.respeak.yaml (+ .respeak.local.yaml) from     tone keys
                the project root down to the target, nearest last
  9 env         files listed in $RESPEAK_CONFIG (colon-separated)   everything
 10 invocation  --mode / --profile / --context / --set               everything

Nearest to the target wins. Maps deep-merge and scalars replace; lists
replace, except gate.allow and gate.exclude, which append. Project-only keys
(gate.enabled, gate.include, gate.exclude, shorthand.*, the style.* corpus
pointers, version, schema) are dropped with a warning when a user, ancestor,
folder, or scope layer sets them. `narrative.profile: NAME` in a layer expands
that profile's fields underneath the layer's own explicit keys.

Exit codes: 0 ok; 1 validate found errors; 2 usage error or missing PyYAML.
"""
import argparse
import copy
import json
import os
import re
import sys

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.stderr.write(
        "respeak-config: PyYAML is required (python3 -m pip install pyyaml); "
        "scripts/respeak-config.sh picks an interpreter that has it\n")
    sys.exit(2)

FOLDER_FILE = ".respeak.yaml"
FOLDER_LOCAL = ".respeak.local.yaml"
PROJECT_REL = os.path.join(".claude", "respeak", "config.yaml")
PROJECT_LOCAL_REL = os.path.join(".claude", "respeak", "config.local.yaml")
DEFAULT_PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Keys only a project-grade layer may set. Anything under these dotted
# prefixes is dropped (with a warning) from user, ancestor, folder, and scope
# layers: turning the gate on and choosing which files it covers is a
# project decision, and shorthand governance must stay reviewable in one
# git-tracked file. Corpus pointers are resources, not tone.
PROJECT_ONLY = (
    "version", "schema",
    "gate.enabled", "gate.include", "gate.exclude",
    "shorthand",
    "style.banned_phrases", "style.replacements", "style.rules",
)
PROJECT_KINDS = {"plugin", "project", "project-local", "env", "invocation"}
CANONICAL_KINDS = ("plugin", "userconfig", "user", "project", "project-local", "invocation")

# Lists that accumulate across layers instead of replacing.
APPEND_LISTS = ("gate.allow", "gate.exclude")

# Fields a profile contributes when a layer says `narrative.profile: NAME`.
PROFILE_KEYS = ("tech_level", "default_mode", "lexicon_access",
                "reading_level_grade", "address")

USERCONFIG_ENV = (
    ("CLAUDE_PLUGIN_OPTION_DEFAULT_MODE", "narrative.default_mode"),
    ("CLAUDE_PLUGIN_OPTION_TECH_LEVEL", "narrative.tech_level"),
    ("CLAUDE_PLUGIN_OPTION_AUTO_NARRATIVE", "narrative.auto_narrative"),
)

KNOWN_TOP_KEYS = {"version", "schema", "editorial_pass", "data", "narrative",
                  "profiles", "modes", "style", "gate", "shorthand", "scopes"}

FAIL_ON_VALUES = ("none", "warn", "error")


# --------------------------------------------------------------------------
# small path + glob helpers
# --------------------------------------------------------------------------

def ancestors(d):
    """['/', '/a', '/a/b'] for '/a/b' (outermost first)."""
    d = os.path.abspath(d)
    out = []
    while True:
        out.append(d)
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    return list(reversed(out))


def is_under(path, root):
    path, root = os.path.abspath(path), os.path.abspath(root)
    try:
        return os.path.commonpath([path, root]) == root
    except ValueError:
        return False


def rel_under(path, root):
    """Path relative to root ('' when equal), or None when not under it."""
    if not is_under(path, root):
        return None
    rel = os.path.relpath(os.path.abspath(path), os.path.abspath(root))
    return "" if rel == "." else rel.replace(os.sep, "/")


_glob_cache = {}


def glob_to_regex(pat):
    """gitignore-flavoured glob: ** = any depth (including none), * = within
    one segment, ? = one char, a trailing / = the directory and everything in
    it, and a pattern with no / matches at any depth."""
    if pat in _glob_cache:
        return _glob_cache[pat]
    p = pat
    if p.endswith("/"):
        p += "**"
    if "/" not in p:
        p = "**/" + p
    out, i = "", 0
    while i < len(p):
        if p.startswith("**/", i):
            out += "(?:.*/)?"
            i += 3
        elif p.startswith("**", i):
            out += ".*"
            i += 2
        elif p[i] == "*":
            out += "[^/]*"
            i += 1
        elif p[i] == "?":
            out += "[^/]"
            i += 1
        else:
            out += re.escape(p[i])
            i += 1
    rx = re.compile("^" + out + "$")
    _glob_cache[pat] = rx
    return rx


def match_glob(pat, path):
    return bool(glob_to_regex(pat).match(path))


def set_dotted(d, key, value):
    parts = key.split(".")
    for p in parts[:-1]:
        d = d.setdefault(p, {})
        if not isinstance(d, dict):
            raise ValueError("%s: not a mapping" % key)
    d[parts[-1]] = value


def get_dotted(d, key, default=None):
    for p in key.split("."):
        if not isinstance(d, dict) or p not in d:
            return default
        d = d[p]
    return d


def coerce_env(key, raw):
    if key.endswith("tech_level"):
        v = float(raw)
        return int(v) if v.is_integer() else v
    if key.endswith("auto_narrative"):
        return str(raw).strip().lower() in ("1", "true", "yes", "on")
    return raw


# --------------------------------------------------------------------------
# layers
# --------------------------------------------------------------------------

class Layer:
    __slots__ = ("kind", "label", "path", "data", "base", "present")

    def __init__(self, kind, label, path=None, data=None, base=None, present=None):
        self.kind = kind
        self.label = label
        self.path = path
        self.data = data
        self.base = base            # directory a scope's relative paths hang off
        self.present = (data is not None) if present is None else present


class Resolution:
    def __init__(self, config, origins, warnings, layers, applied, project, target, plugin_root):
        self.config = config
        self.origins = origins      # dotted leaf key -> label of the layer that set it
        self.warnings = warnings
        self.layers = layers        # every candidate file layer, in precedence order
        self.applied = applied      # layers that contributed, scopes included, in order
        self.project = project
        self.target = target
        self.plugin_root = plugin_root

    def plugin_label(self):
        return self.layers[0].label if self.layers else ""

    def short(self, label):
        """Display form of a label or path: files inside the project become
        project-relative, the plugin root becomes <plugin>, home becomes ~.
        Works on joined labels ("a + b") and suffixed ones ("a#scopes[1]")."""
        if not label:
            return ""
        out = label
        home = os.path.expanduser("~")
        if self.project:
            out = out.replace(self.project + os.sep, "")
        if self.plugin_root:
            out = out.replace(self.plugin_root + os.sep, "<plugin>" + os.sep)
        if home and home != os.sep:
            out = out.replace(home + os.sep, "~" + os.sep)
            if out == home:
                out = "~"
        return out

    def short_abs(self, path):
        """Display form of a directory that should stay absolute (home -> ~)."""
        if not path:
            return ""
        home = os.path.expanduser("~")
        if home and home != os.sep and (path == home or path.startswith(home + os.sep)):
            return "~" + path[len(home):]
        return path


def load_yaml_file(path, warnings):
    """A mapping, {} for an empty file, or None (absent / unreadable / not a
    mapping, the last two with a warning)."""
    try:
        with open(path) as f:
            data = yaml.safe_load(f)
    except FileNotFoundError:
        return None
    except Exception as e:  # noqa: BLE001 — any parse/IO failure means "skip this layer"
        warnings.append("%s: unreadable (%s); ignored" % (path, str(e).splitlines()[0]))
        return None
    if data is None:
        return {}
    if not isinstance(data, dict):
        warnings.append("%s: top level is not a mapping; ignored" % path)
        return None
    return data


def file_layer(kind, path, base, warnings):
    data = load_yaml_file(path, warnings) if os.path.isfile(path) else None
    return Layer(kind, path, path=path, data=data, base=base)


def find_project(explicit, env, target):
    if explicit:
        return os.path.abspath(explicit)
    if env.get("CLAUDE_PROJECT_DIR"):
        return os.path.abspath(env["CLAUDE_PROJECT_DIR"])
    d = target if os.path.isdir(target) else os.path.dirname(target)
    chain = list(reversed(ancestors(d)))          # nearest first
    for a in chain:
        if os.path.isfile(os.path.join(a, PROJECT_REL)):
            return a
    for a in chain:
        if os.path.isdir(os.path.join(a, ".git")) or os.path.isdir(os.path.join(a, ".claude")):
            return a
    return None


def project_layers(project, warnings):
    return [
        file_layer("project", os.path.join(project, PROJECT_REL), project, warnings),
        file_layer("project-local", os.path.join(project, PROJECT_LOCAL_REL), project, warnings),
    ]


def build_stack(project, target, plugin_root, env, overrides, walk_from, warnings):
    layers = []

    # 1. plugin defaults
    layers.append(file_layer("plugin", os.path.join(plugin_root, "config", "respeak.config.yaml"),
                             plugin_root, warnings))

    # 2. plugin userConfig, exported by Claude Code as env vars
    uc, set_vars = {}, []
    for var, key in USERCONFIG_ENV:
        raw = env.get(var)
        if raw is None or raw == "":
            continue
        try:
            set_dotted(uc, key, coerce_env(key, raw))
            set_vars.append(var)
        except ValueError:
            warnings.append("%s=%r is not a valid value; ignored" % (var, raw))
    layers.append(Layer("userconfig",
                        ("plugin userConfig (%s)" % ", ".join(v[len("CLAUDE_PLUGIN_OPTION_"):] for v in set_vars))
                        if set_vars else "plugin userConfig CLAUDE_PLUGIN_OPTION_*",
                        data=uc if set_vars else None))

    # 3. user file
    cfgdir = env.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")
    layers.append(file_layer("user", os.path.join(cfgdir, "respeak", "config.yaml"), None, warnings))

    # 4-8. the walk from the filesystem root down to the target's directory;
    #      the project's own files sit at the project root's position.
    tdir = target if os.path.isdir(target) else os.path.dirname(target)
    in_project = project is not None and is_under(tdir, project)
    if project and not in_project:
        layers.extend(project_layers(project, warnings))
    walk_root = os.path.abspath(walk_from) if walk_from else None
    for d in ancestors(tdir):
        if project and in_project and os.path.abspath(d) == os.path.abspath(project):
            layers.extend(project_layers(project, warnings))
        if walk_root and not is_under(d, walk_root):
            continue
        kind = "folder" if (project and in_project and is_under(d, project)) else "ancestor"
        layers.append(file_layer(kind, os.path.join(d, FOLDER_FILE), d, warnings))
        layers.append(file_layer(kind + "-local", os.path.join(d, FOLDER_LOCAL), d, warnings))

    # 9. extra files from the environment (CI, one-off runs)
    for p in (env.get("RESPEAK_CONFIG") or "").split(":"):
        p = p.strip()
        if not p:
            continue
        p = os.path.abspath(os.path.expanduser(p))
        lay = file_layer("env", p, os.path.dirname(p), warnings)
        if not lay.present:
            warnings.append("RESPEAK_CONFIG: %s not found; ignored" % p)
        layers.append(lay)

    # 10. invocation
    layers.append(Layer("invocation", "invocation (--mode/--profile/--context/--set)",
                        data=overrides if overrides else None))
    return layers


# --------------------------------------------------------------------------
# merge
# --------------------------------------------------------------------------

def key_allowed(key, kind):
    if kind in PROJECT_KINDS:
        return True
    return not any(key == p or key.startswith(p + ".") for p in PROJECT_ONLY)


def merge(dst, src, prefix, layer, origins, warnings):
    for k, v in src.items():
        key = "%s.%s" % (prefix, k) if prefix else str(k)
        if not key_allowed(key, layer.kind):
            warnings.append("%s: %s is project-only; ignored" % (layer.label, key))
            continue
        if key in APPEND_LISTS and isinstance(v, list):
            cur = dst.get(k)
            cur = list(cur) if isinstance(cur, list) else []
            added = [item for item in v if item not in cur]
            cur.extend(added)
            dst[k] = cur
            if added:
                prev = origins.get(key)
                origins[key] = ("%s + %s" % (prev, layer.label)) if prev and len(cur) > len(added) else layer.label
            elif key not in origins:
                origins[key] = layer.label
            continue
        if isinstance(v, dict):
            if not isinstance(dst.get(k), dict):
                dst[k] = {}
                for o in [o for o in origins if o == key or o.startswith(key + ".")]:
                    del origins[o]
            merge(dst[k], v, key, layer, origins, warnings)
            continue
        if isinstance(dst.get(k), dict):
            warnings.append("%s: %s is a mapping in a lower layer but %s here; ignored"
                            % (layer.label, key, "null" if v is None else type(v).__name__))
            continue
        dst[k] = copy.deepcopy(v)
        for o in [o for o in origins if o.startswith(key + ".")]:
            del origins[o]
        origins[key] = layer.label


def scope_matches(patterns, layer, target, warnings, idx):
    is_dir = os.path.isdir(target)
    for pat in patterns:
        if not isinstance(pat, str) or not pat:
            warnings.append("%s#scopes[%d]: paths entries must be strings; skipped %r" % (layer.label, idx, pat))
            continue
        if layer.base is None:
            # user-level (or otherwise unrooted) file: absolute or ~ paths only
            if not (pat.startswith("/") or pat.startswith("~")):
                warnings.append("%s#scopes[%d]: paths at this level must be absolute or ~-prefixed: %r; skipped"
                                % (layer.label, idx, pat))
                continue
            full = os.path.abspath(target) + ("/" if is_dir else "")
            if match_glob(os.path.expanduser(pat), full):
                return True
        else:
            rel = rel_under(target, layer.base)
            if rel is None:
                continue
            if is_dir and rel:
                rel += "/"
            if match_glob(pat, rel):
                return True
    return False


def apply_layer(cfg, origins, layer, data, target, warnings, applied):
    data = dict(data)
    scopes = data.pop("scopes", None)

    # `narrative.profile: NAME` expands the profile underneath this layer's
    # own explicit keys, using the profiles merged so far plus this layer's.
    narrative = data.get("narrative")
    prof = narrative.get("profile") if isinstance(narrative, dict) else None
    if isinstance(prof, str):
        profiles = dict(cfg.get("profiles") or {})
        if isinstance(data.get("profiles"), dict):
            profiles.update(data["profiles"])
        p = profiles.get(prof)
        if isinstance(p, dict):
            expanded = {"narrative": {k: v for k, v in p.items() if k in PROFILE_KEYS}}
            sub = Layer(layer.kind, "%s (profile %s)" % (layer.label, prof), base=layer.base)
            merge(cfg, expanded, "", sub, origins, warnings)
        else:
            warnings.append("%s: narrative.profile %r is not a known profile; ignored" % (layer.label, prof))

    merge(cfg, data, "", layer, origins, warnings)
    applied.append(layer)

    if scopes is None:
        return
    if not isinstance(scopes, list):
        warnings.append("%s: scopes must be a list; ignored" % layer.label)
        return
    for i, s in enumerate(scopes):
        if not isinstance(s, dict) or "paths" not in s:
            warnings.append("%s#scopes[%d]: needs a `paths` list; skipped" % (layer.label, i))
            continue
        paths = s["paths"]
        if isinstance(paths, str):
            paths = [paths]
        if not isinstance(paths, list):
            warnings.append("%s#scopes[%d]: paths must be a list; skipped" % (layer.label, i))
            continue
        overlay = {k: v for k, v in s.items() if k != "paths"}
        if "scopes" in overlay:
            warnings.append("%s#scopes[%d]: nested scopes are not supported; ignored" % (layer.label, i))
            overlay.pop("scopes")
        if not scope_matches(paths, layer, target, warnings, i):
            continue
        sub = Layer("scope", "%s#scopes[%d]" % (layer.label, i), base=layer.base, data=overlay)
        apply_layer(cfg, origins, sub, overlay, target, warnings, applied)


def resolve(target=None, project=None, plugin_root=None, env=None, overrides=None, walk_from=None):
    env = os.environ if env is None else env
    warnings = []
    target = os.path.abspath(target or os.getcwd())
    plugin_root = os.path.abspath(plugin_root or env.get("CLAUDE_PLUGIN_ROOT") or DEFAULT_PLUGIN_ROOT)
    project = find_project(project, env, target)
    layers = build_stack(project, target, plugin_root, env, overrides or {}, walk_from, warnings)
    if not layers[0].present:
        warnings.append("plugin defaults not found at %s" % layers[0].path)
    config, origins, applied = {}, {}, []
    for layer in layers:
        if layer.present:
            apply_layer(config, origins, layer, layer.data, target, warnings, applied)
    return Resolution(config, origins, warnings, layers, applied, project, target, plugin_root)


# --------------------------------------------------------------------------
# gate decision
# --------------------------------------------------------------------------

def gate_decision(res):
    g = res.config.get("gate") or {}
    fail_on = g.get("fail_on") or "error"
    if fail_on not in FAIL_ON_VALUES:
        res.warnings.append("gate.fail_on %r is not one of %s; using error" % (fail_on, "/".join(FAIL_ON_VALUES)))
        fail_on = "error"
    out = {"applies": False, "enabled": bool(g.get("enabled")), "fail_on": fail_on,
           "rel_path": None, "reason": ""}
    if not out["enabled"]:
        out["reason"] = "gate.enabled is not true in the project config"
        return out
    if not res.project or os.path.isdir(res.target):
        out["reason"] = "no project, or target is a directory"
        return out
    rel = rel_under(res.target, res.project)
    if rel is None:
        out["reason"] = "target is outside the project"
        return out
    out["rel_path"] = rel
    include = g.get("include") or ["**/*.md"]
    exclude = g.get("exclude") or []
    included = any(match_glob(p, rel) for p in include if isinstance(p, str))
    excluded = any(match_glob(p, rel) for p in exclude if isinstance(p, str))
    if not included:
        out["reason"] = "not matched by gate.include"
    elif excluded:
        out["reason"] = "matched by gate.exclude"
    else:
        out["applies"] = True
        out["reason"] = "matched gate.include and not gate.exclude"
    return out


# --------------------------------------------------------------------------
# output formats
# --------------------------------------------------------------------------

def summary(res):
    n = res.config.get("narrative") or {}
    g = res.config.get("gate") or {}
    origin = res.origins.get("narrative.default_mode", "")
    is_default = (not origin) or origin.startswith(res.plugin_label())
    return {
        "mode": n.get("default_mode"),
        "tech": n.get("tech_level"),
        "profile": n.get("profile"),
        "context": n.get("context_default"),
        "auto_narrative": bool(n.get("auto_narrative")),
        "gate": ("on:%s" % (g.get("fail_on") or "error")) if g.get("enabled") else "off",
        "from": "" if is_default else re.sub(r" \(profile [^)]*\)$", "", res.short(origin)),
    }


def fmt_line(res):
    s = summary(res)
    parts = ["%s=%s" % (k, ("" if v is None else str(v).lower() if isinstance(v, bool) else v))
             for k, v in s.items() if k != "from"]
    parts.append("from=%s" % (s["from"] or "plugin-default"))
    return " ".join(parts)


def fmt_statusline(res):
    s = summary(res)
    out = "%s/t%s" % (s["mode"] or "?", s["tech"] if s["tech"] is not None else "?")
    if s["profile"]:
        out += " %s" % s["profile"]
    if s["from"]:
        out += " @%s" % s["from"]
    return out


def fmt_explain(res, gate=None):
    L = []
    L.append("respeak config for %s" % res.short(res.target))
    L.append("project: %s" % (res.short_abs(res.project) if res.project else "(none found)"))
    L.append("")
    L.append("layers, lowest precedence first (* = present and applied):")
    applied_labels = {a.label: a for a in res.applied}
    skipped = 0
    for lay in res.layers:
        if lay.present:
            L.append("  * %-14s %s" % (lay.kind, res.short(lay.label)))
            for a in res.applied:
                if a.kind == "scope" and a.label.startswith(lay.label + "#"):
                    L.append("  * %-14s %s" % ("scope", res.short(a.label)))
        elif lay.kind in CANONICAL_KINDS:
            L.append("    %-14s %s (absent)" % (lay.kind, res.short(lay.label)))
        else:
            skipped += 1
    if skipped:
        L.append("    (%d director%s walked with no %s)" % (skipped // 2, "y" if skipped // 2 == 1 else "ies", FOLDER_FILE))
    del applied_labels
    L.append("")
    s = summary(res)
    tone = get_dotted(res.config, "narrative.tone", {}) or {}
    L.append("effective narrative: mode=%s tech_level=%s profile=%s context=%s tone(f=%s d=%s c=%s) auto_narrative=%s"
             % (s["mode"], s["tech"], s["profile"], s["context"],
                tone.get("formality"), tone.get("directness"), tone.get("confidence"),
                str(s["auto_narrative"]).lower()))
    lex = get_dotted(res.config, "narrative.lexicon_access")
    if lex:
        L[-1] += " lexicon_access=%s" % lex
    if gate is not None:
        L.append("gate: enabled=%s fail_on=%s applies=%s (%s)"
                 % (str(gate["enabled"]).lower(), gate["fail_on"], str(gate["applies"]).lower(), gate["reason"]))
    else:
        L.append("gate: %s" % s["gate"])
    plugin = res.plugin_label()
    overrides = []
    seen_profiles = set()
    for k, lab in sorted(res.origins.items()):
        if lab.startswith(plugin):
            continue
        if k.startswith("profiles."):
            # one line per profile, not one per field
            pk = ".".join(k.split(".")[:2])
            if pk in seen_profiles:
                continue
            seen_profiles.add(pk)
            k = pk
        overrides.append((k, lab))
    L.append("")
    if overrides:
        L.append("overrides (key = value <- layer):")
        width = max(len(k) for k, _ in overrides)
        for k, lab in overrides:
            val = get_dotted(res.config, k)
            if isinstance(val, (bool, list, dict)) or val is None:
                val = json.dumps(val)
            L.append("  %-*s = %-24s <- %s" % (width, k, val, res.short(lab)))
    else:
        L.append("overrides: none (plugin defaults throughout)")
    if res.warnings:
        L.append("")
        L.append("warnings:")
        for w in res.warnings:
            L.append("  %s" % res.short(w))
    return "\n".join(L)


# --------------------------------------------------------------------------
# validate
# --------------------------------------------------------------------------

def guess_kind(path, env):
    base = os.path.basename(path)
    if base in (FOLDER_FILE, FOLDER_LOCAL):
        return "folder"
    norm = path.replace(os.sep, "/")
    if norm.endswith("config/respeak.config.yaml"):
        return "plugin"
    cfgdir = env.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")
    if norm.endswith(".claude/respeak/config.local.yaml"):
        return "project-local"
    if norm.endswith(".claude/respeak/config.yaml"):
        return "user" if is_under(path, cfgdir) else "project"
    return "project"


def validate_file(path, kind, env, plugin_root=None):
    """Returns (errors, warnings) for one file."""
    errors, warnings, notes = [], [], []
    path = os.path.abspath(path)
    if not os.path.isfile(path):
        return ["%s: not found" % path], []
    data = load_yaml_file(path, notes)
    if data is None:
        return notes or ["%s: unreadable" % path], []
    for k in data:
        if k not in KNOWN_TOP_KEYS:
            warnings.append("%s: unknown top-level key %r" % (path, k))
    layer_kind = {"folder": "folder", "user": "user", "plugin": "plugin",
                  "project": "project", "project-local": "project-local"}[kind]
    base = None if kind == "user" else os.path.dirname(path)
    lay = Layer(layer_kind, path, path=path, data=data, base=base)
    # Dry-merge on top of the plugin defaults (so the shipped profiles are
    # known and type mismatches surface); scopes are checked separately below
    # because a dry run's target matches none of them.
    merge_warnings = []
    cfg, origins, applied = {}, {}, []
    if kind != "plugin":
        defaults = load_yaml_file(os.path.join(plugin_root or DEFAULT_PLUGIN_ROOT,
                                               "config", "respeak.config.yaml"), [])
        if defaults:
            apply_layer(cfg, origins, Layer("plugin", "plugin defaults", data=defaults),
                        defaults, os.path.dirname(path), [], [])
    apply_layer(cfg, origins, lay, data, os.path.dirname(path), merge_warnings, applied)
    scopes = data.get("scopes")
    if isinstance(scopes, list):
        for i, s in enumerate(scopes):
            if not isinstance(s, dict) or "paths" not in s:
                errors.append("%s#scopes[%d]: needs a `paths` list" % (path, i))
                continue
            paths = s["paths"] if isinstance(s["paths"], list) else [s["paths"]]
            for p in paths:
                if not isinstance(p, str) or not p:
                    errors.append("%s#scopes[%d]: paths entries must be non-empty strings" % (path, i))
                elif kind == "user" and not (p.startswith("/") or p.startswith("~")):
                    errors.append("%s#scopes[%d]: user-level paths must be absolute or ~-prefixed: %r" % (path, i, p))
            overlay = {k: v for k, v in s.items() if k != "paths"}
            sub_w = []
            merge({}, overlay, "", Layer("scope", "%s#scopes[%d]" % (path, i)), {}, sub_w)
            errors.extend(w for w in sub_w if "project-only" in w)
    elif scopes is not None:
        errors.append("%s: scopes must be a list" % path)
    for w in merge_warnings:
        if "project-only" in w:
            errors.append(w)
        elif "not a known profile" in w:
            warnings.append(w + " (profiles from lower layers are not visible to validate)")
        elif w not in errors:
            warnings.append(w)
    return sorted(set(errors)), warnings


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def parse_overrides(args):
    ov = {}
    if getattr(args, "mode", None):
        set_dotted(ov, "narrative.default_mode", args.mode)
    if getattr(args, "profile", None):
        set_dotted(ov, "narrative.profile", args.profile)
    if getattr(args, "context", None):
        set_dotted(ov, "narrative.context_default", args.context)
    for item in getattr(args, "set", None) or []:
        if "=" not in item:
            raise SystemExit("respeak-config: --set expects key=value, got %r" % item)
        k, v = item.split("=", 1)
        set_dotted(ov, k.strip(), yaml.safe_load(v) if v.strip() else None)
    return ov


def add_common(p):
    p.add_argument("--project", default=None, help="project root (default: $CLAUDE_PROJECT_DIR, else discovered)")
    p.add_argument("--for", dest="target", default=None, help="file or directory the config is for (default: cwd)")
    p.add_argument("--plugin-root", default=None, help="plugin root (default: $CLAUDE_PLUGIN_ROOT, else this checkout)")
    p.add_argument("--walk-from", default=None, help="only look for .respeak.yaml at or below this directory")
    p.add_argument("--mode", choices=("eli5", "bluf", "technical"), default=None)
    p.add_argument("--profile", default=None)
    p.add_argument("--context", choices=("incident", "routine", "celebration"), default=None)
    p.add_argument("--set", action="append", default=[], metavar="KEY=VALUE")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="respeak-config", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("resolve", help="print the effective configuration")
    add_common(p)
    p.add_argument("--format", choices=("yaml", "json", "line", "statusline"), default="yaml")

    p = sub.add_parser("explain", help="show every layer and which one set each override")
    add_common(p)

    p = sub.add_parser("gate", help="decide whether the style gate applies to --for")
    add_common(p)
    p.add_argument("--write-config", default=None, help="also write the resolved config (YAML) here")

    p = sub.add_parser("validate", help="check config files for shape and policy")
    p.add_argument("files", nargs="+")
    p.add_argument("--plugin-root", default=None)
    p.add_argument("--kind", choices=("plugin", "user", "project", "project-local", "folder"), default=None)

    args = ap.parse_args(argv)
    env = os.environ

    if args.cmd == "validate":
        total_errors = 0
        for f in args.files:
            kind = args.kind or guess_kind(os.path.abspath(f), env)
            errors, warnings = validate_file(f, kind, env, args.plugin_root or env.get("CLAUDE_PLUGIN_ROOT"))
            total_errors += len(errors)
            status = "ERROR" if errors else ("ok (with warnings)" if warnings else "ok")
            print("%s [%s]: %s" % (f, kind, status))
            for e in errors:
                print("  error: %s" % e)
            for w in warnings:
                print("  warn:  %s" % w)
        return 1 if total_errors else 0

    try:
        overrides = parse_overrides(args)
    except ValueError as e:
        sys.stderr.write("respeak-config: %s\n" % e)
        return 2
    res = resolve(target=args.target, project=args.project, plugin_root=args.plugin_root,
                  env=env, overrides=overrides, walk_from=args.walk_from)

    if args.cmd == "resolve":
        if args.format == "yaml":
            sys.stdout.write(yaml.safe_dump(res.config, sort_keys=False, default_flow_style=False))
        elif args.format == "json":
            print(json.dumps(res.config, indent=2))
        elif args.format == "line":
            print(fmt_line(res))
        else:
            print(fmt_statusline(res))
        for w in res.warnings:
            sys.stderr.write("respeak-config: %s\n" % w)
        return 0

    if args.cmd == "explain":
        gate = gate_decision(res) if not os.path.isdir(res.target) else None
        print(fmt_explain(res, gate))
        return 0

    if args.cmd == "gate":
        if not args.target:
            sys.stderr.write("respeak-config gate: --for FILE is required\n")
            return 2
        decision = gate_decision(res)
        if args.write_config:
            with open(args.write_config, "w") as f:
                yaml.safe_dump(res.config, f, sort_keys=False, default_flow_style=False)
        decision["warnings"] = res.warnings
        print(json.dumps(decision))
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
