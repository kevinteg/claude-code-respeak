#!/usr/bin/env python3
"""respeak-config.py — resolve respeak's layered configuration for a path.

Usage:
  respeak-config.py resolve  [--project DIR] [--for PATH] [--format yaml|json|line|statusline]
                             [--mode M] [--profile P] [--context C] [--set key=value]...
                             [--session ID]
  respeak-config.py explain  [--project DIR] [--for PATH] [--mode ...] [--set ...] [--session ID]
  respeak-config.py gate     [--project DIR] --for FILE [--write-config PATH] [--session ID]
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
  9 session     the `respeak` section of claude-code-session's       tone keys
                resolved file (below), when present and accepted
 10 env         files listed in $RESPEAK_CONFIG (colon-separated)   everything
 11 invocation  --mode / --profile / --context / --set               everything

Nearest to the target wins. Maps deep-merge and scalars replace; lists
replace, except gate.allow and gate.exclude, which append. Project-only keys
(gate.enabled, gate.include, gate.exclude, shorthand.*, the style.* corpus
pointers, version, schema) are dropped with a warning when a user, ancestor,
folder, or scope layer sets them. `narrative.profile: NAME` in a layer expands
that profile's fields underneath the layer's own explicit keys.

The session layer is optional: claude-code-session, when installed, writes
${XDG_STATE_HOME:-~/.local/state}/claude-code-session/sessions/<id>/resolved.json;
<id> is --session, else $CLAUDE_CODE_SESSION_ID. The
file is accepted when provider.version has major SESSION_PROVIDER_MAJOR, and
never written here. Absent, unreadable, a wrong major or no id: an empty
layer and at most one warning; respeak behaves as it does alone.

The project root is found the same way for every consumer (hook, skill,
statusline, CLI): --project if given; else the nearest ancestor of the target
holding .claude/respeak/config.yaml (never the user config directory); else
--launch-dir / $CLAUDE_PROJECT_DIR (where Claude Code was started); else the
nearest ancestor holding .git or .claude/. All paths are compared after
symlink resolution. The gate covers Markdown files only (.md .markdown .mdx);
gate.include/exclude narrow within that set.

Exit codes: 0 ok; 1 validate found errors; 2 usage error or missing PyYAML.
"""
import argparse
import copy
import json
import os
import re
import sys
import unicodedata

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

# The CI verdict (`gate --committed`) reads every gate.* key from these kinds
# only: the plugin defaults and the committed project file, its scopes
# included. A folder file, an ignored local file, the user file, the session
# provider, RESPEAK_CONFIG and --set cannot move it (review ADV6-1, ADV6-2).
COMMITTED_GATE_KINDS = ("plugin", "project")

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

# What a gate verdict is measured against. `introduced` compares the write
# with the file as it was and blocks only on hits this edit added, so a
# document that already carries one (a banned term inside a heading, which
# the verifier holds invariant) stays editable; `any` blocks on every hit in
# the file. Any layer may set it, like fail_on.
BLOCK_ON_VALUES = ("introduced", "any")

# The style gate is a Markdown scanner; the hook's cheap pre-filter and the
# resolver's gate decision agree on exactly this set (docs/config-layers.md).
MARKDOWN_EXTS = (".md", ".markdown", ".mdx")

# The session provider (conventions section 3): claude-code-session's resolved
# file for this session, accepted only from the provider major this resolver
# understands. A change to the file's contract bumps that major.
SESSION_PROVIDER = "claude-code-session"
SESSION_PROVIDER_MAJOR = 2
SESSION_ID_ENV = ("CLAUDE_CODE_SESSION_ID",)
SESSION_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

# PyYAML's C loader parses the 230-line plugin config in a few milliseconds;
# the pure-Python one takes ~100 ms, which the statusline would pay per refresh.
_Loader = getattr(yaml, "CSafeLoader", yaml.SafeLoader)


def real(path):
    """Absolute path with symlinks resolved, so /tmp and /private/tmp (or a
    ~/src symlink) never make an in-project file look like an outsider."""
    return os.path.realpath(os.path.abspath(os.path.expanduser(path)))


# macOS (APFS/HFS+) and Windows filesystems are case-insensitive and treat
# NFC/NFD spellings as one name, but os.path.realpath canonicalises neither;
# comparisons fold both so "/Home/Alice/Proj" and "/home/alice/proj" are one
# directory there, while Linux keeps exact comparison.
CASE_INSENSITIVE_FS = sys.platform in ("darwin", "win32")


def fold(path):
    return unicodedata.normalize("NFC", path).casefold() if CASE_INSENSITIVE_FS else path


def path_key(path):
    """Comparison key: symlink-resolved and folded."""
    return fold(real(path))


def logical_depth(path, root):
    """Number of leading components of the path AS SPELLED that resolve to
    root (i.e. root is one of the spelled path's ancestors, symlinks followed
    only up to that ancestor), or None. A symlink inside the project that
    points outside it still names a file that lives in the project."""
    own = segs(os.path.abspath(os.path.expanduser(path)))
    rk = path_key(root)
    for n in range(len(own), -1, -1):
        prefix = os.sep + os.sep.join(own[:n])
        if path_key(prefix) == rk:
            return n
    return None


def segs(path):
    return [x for x in path.split(os.sep) if x]


def deep_merge(base, over):
    """Plain recursive merge of two mappings (maps merge, everything else
    replaces); used for the profile lookup table only."""
    out = copy.deepcopy(base) if isinstance(base, dict) else {}
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        elif isinstance(out.get(k), dict):
            continue  # a scalar/null never deletes a mapping; merge() warns for it
        else:
            out[k] = copy.deepcopy(v)
    return out


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


def _under(pk, rk):
    return pk[:len(rk)] == rk


def under_how(path, root):
    """'real' when the symlink-resolved path is under root, else 'logical'
    when one of the path's spelled ancestors resolves to root, else None."""
    rk = segs(path_key(root))
    if _under(segs(path_key(path)), rk):
        return "real"
    if logical_depth(path, root) is not None:
        return "logical"
    return None


def is_under(path, root):
    return under_how(path, root) is not None


def same_dir(a, b):
    return path_key(a) == path_key(b)


def rel_under(path, root):
    """Path relative to root ('' when equal) in the path's own spelling, or
    None when not under it."""
    how = under_how(path, root)
    if how is None:
        return None
    if how == "real":
        return "/".join(segs(real(path))[len(segs(path_key(root))):])
    own = segs(os.path.abspath(os.path.expanduser(path)))
    return "/".join(own[logical_depth(path, root):])


def common_ancestor(path, other):
    """The deepest directory shared by two paths, in `path`'s own spelling."""
    pk, ok = segs(path_key(path)), segs(path_key(other))
    n = 0
    while n < min(len(pk), len(ok)) and pk[n] == ok[n]:
        n += 1
    own = segs(os.path.abspath(os.path.expanduser(path)))
    return os.sep + os.sep.join(own[:n]) if n else os.sep


_glob_cache = {}


def glob_to_regex(pat):
    """gitignore-flavoured glob: ** = any depth (including none), * = within
    one segment, ? = one char, a trailing / = the directory and everything in
    it, and a pattern with no / matches a file or directory of that name at
    any depth (a directory match includes its contents)."""
    if pat in _glob_cache:
        return _glob_cache[pat]
    p = pat
    if p.endswith("/"):
        p += "**"
    if "/" not in p:
        p = "**/" + p + "/**"
    out, i = "", 0
    while i < len(p):
        if p.startswith("**/", i):
            out += "(?:.*/)?"
            i += 3
        elif p.startswith("/**", i) and i + 3 == len(p):
            out += "(?:/.*)?"
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


def real_glob_prefix(pat):
    """Resolve symlinks in the literal directory prefix of an absolute or
    ~-prefixed glob (everything before the first segment holding a glob
    character), so a user-level scope written as /tmp/x/** matches targets
    the resolver reports as /private/tmp/x/... ."""
    pat = os.path.expanduser(pat)
    segs = pat.split("/")
    lit = []
    for seg in segs:
        if any(c in seg for c in "*?["):
            break
        lit.append(seg)
    rest = segs[len(lit):]
    prefix = "/".join(lit) or "/"
    if os.path.exists(prefix):
        prefix = os.path.realpath(prefix)
    return "/".join([prefix.rstrip("/")] + rest) if rest else prefix


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
    __slots__ = ("kind", "label", "path", "data", "base", "present", "grade")

    def __init__(self, kind, label, path=None, data=None, base=None, present=None, grade=None):
        self.kind = kind
        self.grade = grade or kind  # the kind of the file a scope or profile layer came from
        self.label = label
        self.path = path
        self.data = data
        self.base = base            # directory a scope's relative paths hang off
        self.present = (data is not None) if present is None else present


class Resolution:
    def __init__(self, config, origins, warnings, layers, applied, project, target, plugin_root,
                 project_how="", launch_dir=None, provider=None):
        self.config = config
        self.origins = origins      # dotted leaf key -> label of the layer that set it
        self.warnings = warnings
        self.layers = layers        # every candidate file layer, in precedence order
        self.applied = applied      # layers that contributed, scopes included, in order
        self.project = project
        self.project_how = project_how  # how the project root was chosen (for explain)
        self.target = target
        self.plugin_root = plugin_root
        self.launch_dir = launch_dir
        self.provider = provider    # the accepted session provider block, or None
        self.dropped = None         # gate keys --committed dropped, as "<layer>: <key>"

    def provider_line(self):
        p = self.provider
        if not p:
            return "provider: none"
        return "provider: %s %s profile %s" % (SESSION_PROVIDER, p.get("version"), p.get("profile") or "(none)")

    def plugin_label(self):
        return self.layers[0].label if self.layers else ""

    def short(self, label):
        """Display form of a label or path: files inside the project become
        project-relative, the plugin root becomes <plugin>, home becomes ~.
        Works on joined labels ("a + b") and suffixed ones ("a#scopes[1]")."""
        if not label:
            return ""
        out = label
        home = real(os.path.expanduser("~"))
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
        home = real(os.path.expanduser("~"))
        if home and home != os.sep and (path == home or path.startswith(home + os.sep)):
            return "~" + path[len(home):]
        return path


def load_yaml_file(path, warnings):
    """A mapping, {} for an empty file, or None (absent / unreadable / not a
    mapping, the last two with a warning)."""
    try:
        with open(path) as f:
            data = yaml.load(f, Loader=_Loader)
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


def user_config_dir(env):
    return real(env.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude"))


def is_user_root(d, cfgdir):
    """True when treating d as a project would load the USER file
    (<cfgdir>/respeak/config.yaml) at project grade: with the default
    ~/.claude that is $HOME itself. Compared after symlink resolution and
    case folding, so a dotfiles-managed ~/.claude symlink or a differently
    cased spelling of $HOME cannot smuggle the user file in."""
    user_file = path_key(os.path.join(cfgdir, "respeak", "config.yaml"))
    return (path_key(os.path.join(d, PROJECT_REL)) == user_file
            or path_key(os.path.join(d, ".claude")) == path_key(cfgdir))


def find_project(explicit, env, target, launch_dir=None):
    """(project root or None, how). One rule for every consumer:
    1. --project, verbatim;
    2. the nearest ancestor of the target holding .claude/respeak/config.yaml
       (a nested one wins in a monorepo; a parent one governs every repo
       below it, like a parent CLAUDE.md), never the user config directory;
    3. --launch-dir / $CLAUDE_PROJECT_DIR, where Claude Code was started;
    4. the nearest ancestor holding .git or .claude/ (again never $HOME)."""
    cfgdir = user_config_dir(env)
    if explicit:
        return real(explicit), "--project"
    d = target if os.path.isdir(target) else os.path.dirname(target)
    chain = list(reversed(ancestors(d)))          # nearest first
    for a in chain:
        if not is_user_root(a, cfgdir) and os.path.isfile(os.path.join(a, PROJECT_REL)):
            return real(a), "nearest " + PROJECT_REL
    launch = launch_dir or env.get("CLAUDE_PROJECT_DIR")
    if launch:
        return real(launch), "launch directory (CLAUDE_PROJECT_DIR)"
    for a in chain:
        if is_user_root(a, cfgdir):
            continue
        if os.path.isdir(os.path.join(a, ".git")) or os.path.isdir(os.path.join(a, ".claude")):
            return real(a), "nearest .git or .claude/"
    return None, "none found"


def tdir_anchor(tdir, project):
    """The ancestor of tdir (in tdir's own spelling) that IS the project root."""
    for d in ancestors(tdir):
        if same_dir(d, project):
            return d
    return project


def project_layers(project, warnings, cfgdir):
    if is_user_root(project, cfgdir):
        warnings.append("project root %s is the user config directory; the user file is not "
                        "re-applied at project grade" % project)
        return []
    return [
        file_layer("project", os.path.join(project, PROJECT_REL), project, warnings),
        file_layer("project-local", os.path.join(project, PROJECT_LOCAL_REL), project, warnings),
    ]


def session_state_path(session_id, env):
    state = env.get("XDG_STATE_HOME") or os.path.join(
        env.get("HOME") or os.path.expanduser("~"), ".local", "state")
    return os.path.join(state, SESSION_PROVIDER, "sessions", session_id, "resolved.json")


def session_layer(session_id, env, warnings):
    """The session provider's layer and its provider block.

    Returns (Layer or None, provider dict or None). Every failure is an empty
    layer with at most one warning; the file is read, never written."""
    if not session_id:
        for var in SESSION_ID_ENV:
            if env.get(var):
                session_id = env[var]
                break
    if not session_id:
        return None, None
    if not SESSION_ID_RE.match(session_id):
        warnings.append("session id %r is not a plain name; session layer ignored" % session_id)
        return None, None
    path = session_state_path(session_id, env)
    if not os.path.isfile(path):
        return None, None
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        warnings.append("%s: unreadable (%s); ignored" % (path, str(e).splitlines()[0]))
        return None, None
    provider = data.get("provider") if isinstance(data, dict) else None
    if not isinstance(provider, dict):
        warnings.append("%s: no provider block; ignored" % path)
        return None, None
    version = str(provider.get("version") or "")
    major = version.lstrip("v").split(".", 1)[0]
    if not major.isdigit() or int(major) != SESSION_PROVIDER_MAJOR:
        warnings.append("%s: provider.version %r is not major %d; ignored"
                        % (path, version, SESSION_PROVIDER_MAJOR))
        return None, None
    section = data.get("respeak")
    if section is not None and not isinstance(section, dict):
        warnings.append("%s: the respeak section is not a mapping; ignored" % path)
        section = None
    label = "%s#respeak" % path
    return Layer("session", label, path=path, data=section or None, base=None), provider


def build_stack(project, target, plugin_root, env, overrides, walk_from, warnings, session=None):
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
    cfgdir = user_config_dir(env)
    layers.append(file_layer("user", os.path.join(cfgdir, "respeak", "config.yaml"), None, warnings))

    # 4-8. the walk from the filesystem root down to the target's directory;
    #      the project's own files sit at the project root's position. For a
    #      target outside the project they sit right after the deepest
    #      directory common to both, so a .respeak.yaml above the project
    #      root stays below the project wherever the target lives.
    tdir = target if os.path.isdir(target) else os.path.dirname(target)
    in_project = project is not None and is_under(tdir, project)
    anchor = None
    if project:
        anchor = tdir_anchor(tdir, project) if in_project else common_ancestor(tdir, project)
        if anchor == os.sep and not same_dir(anchor, project) and os.sep not in (tdir[:1],):
            layers.extend(project_layers(project, warnings, cfgdir))  # nothing in common
            anchor = None
    walk_root = real(walk_from) if walk_from else None
    for d in ancestors(tdir):
        at_anchor = anchor is not None and same_dir(d, anchor)
        if at_anchor and in_project:
            layers.extend(project_layers(project, warnings, cfgdir))
        if not (walk_root and not is_under(d, walk_root)):
            kind = "folder" if (project and in_project and is_under(d, project)) else "ancestor"
            layers.append(file_layer(kind, os.path.join(d, FOLDER_FILE), d, warnings))
            layers.append(file_layer(kind + "-local", os.path.join(d, FOLDER_LOCAL), d, warnings))
        if at_anchor and not in_project:
            layers.extend(project_layers(project, warnings, cfgdir))

    # 9. the session provider's resolved file, when one was accepted
    if session is not None and session.present:
        layers.append(session)

    # 10. extra files from the environment (CI, one-off runs)
    for p in (env.get("RESPEAK_CONFIG") or "").split(":"):
        p = p.strip()
        if not p:
            continue
        p = real(p)
        lay = file_layer("env", p, os.path.dirname(p), warnings)
        if not lay.present:
            warnings.append("RESPEAK_CONFIG: %s not found; ignored" % p)
        layers.append(lay)

    # 11. invocation
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


def merge(dst, src, prefix, layer, origins, warnings, dropped=None):
    for k, v in src.items():
        key = "%s.%s" % (prefix, k) if prefix else str(k)
        if not key_allowed(key, layer.kind):
            warnings.append("%s: %s is project-only; ignored" % (layer.label, key))
            continue
        if (dropped is not None and layer.grade not in COMMITTED_GATE_KINDS
                and (key.startswith("gate.") or (key == "gate" and not isinstance(v, dict)))):
            dropped.append("%s: %s" % (layer.label, key))
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
            merge(dst[k], v, key, layer, origins, warnings, dropped)
            continue
        if isinstance(dst.get(k), dict):
            warnings.append("%s: %s is a mapping in a lower layer but %s here; ignored"
                            % (layer.label, key, "null" if v is None else type(v).__name__))
            continue
        if isinstance(dst.get(k), bool) and isinstance(v, str):
            # --set gate.enabled=no must not turn the gate ON: a string on a
            # boolean key is read as a boolean spelling or refused.
            word = v.strip().lower()
            if word in ("true", "yes", "on", "1"):
                v = True
            elif word in ("false", "no", "off", "0"):
                v = False
            else:
                warnings.append("%s: %s is a boolean but %r is not a boolean spelling; ignored"
                                % (layer.label, key, v))
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
            full = target + ("/" if is_dir else "")
            if match_glob(real_glob_prefix(pat), full):
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


def apply_layer(cfg, origins, layer, data, target, warnings, applied, dropped=None):
    data = dict(data)
    scopes = data.pop("scopes", None)

    # `narrative.profile: NAME` expands the profile underneath this layer's
    # own explicit keys, using the profiles merged so far plus this layer's.
    narrative = data.get("narrative")
    prof = narrative.get("profile") if isinstance(narrative, dict) else None
    if prof is not None:
        # the lookup table is the profiles merged so far deep-merged with this
        # layer's own `profiles:` — the same table `resolve` will report
        profiles = deep_merge(cfg.get("profiles") or {},
                              data.get("profiles") if isinstance(data.get("profiles"), dict) else {})
        p = profiles.get(prof) if isinstance(prof, str) else None
        if isinstance(p, dict):
            expanded = {"narrative": {k: v for k, v in p.items() if k in PROFILE_KEYS}}
            sub = Layer(layer.kind, "%s (profile %s)" % (layer.label, prof), base=layer.base,
                        grade=layer.grade)
            merge(cfg, expanded, "", sub, origins, warnings, dropped)
        else:
            warnings.append("%s: narrative.profile %r is not a known profile; ignored" % (layer.label, prof))
            narrative = dict(narrative)
            narrative.pop("profile")
            data["narrative"] = narrative

    merge(cfg, data, "", layer, origins, warnings, dropped)
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
        sub = Layer("scope", "%s#scopes[%d]" % (layer.label, i), base=layer.base, data=overlay,
                    grade=layer.grade)
        apply_layer(cfg, origins, sub, overlay, target, warnings, applied, dropped)


def resolve(target=None, project=None, plugin_root=None, env=None, overrides=None, walk_from=None,
            launch_dir=None, session_id=None, committed=False):
    env = os.environ if env is None else env
    warnings = []
    given = os.path.abspath(os.path.expanduser(target or os.getcwd()))
    target = real(given)
    plugin_root = real(plugin_root or env.get("CLAUDE_PLUGIN_ROOT") or DEFAULT_PLUGIN_ROOT)
    launch_dir = real(launch_dir) if launch_dir else None
    project, how = find_project(project, env, given, launch_dir)
    if project and under_how(target, project) is None and under_how(given, project) == "logical":
        # e.g. proj/ext.md -> /elsewhere/ext.md: the file the tool wrote lives
        # in the project, so resolve for the spelling that says so
        target = given
    session, provider = session_layer(session_id, env, warnings)
    layers = build_stack(project, target, plugin_root, env, overrides or {}, walk_from, warnings,
                         session=session)
    if not layers[0].present:
        warnings.append("plugin defaults not found at %s" % layers[0].path)
    config, origins, applied = {}, {}, []
    dropped = [] if committed else None
    for layer in layers:
        if layer.present:
            apply_layer(config, origins, layer, layer.data, target, warnings, applied, dropped)
    res = Resolution(config, origins, warnings, layers, applied, project, target, plugin_root,
                     project_how=how, launch_dir=launch_dir, provider=provider)
    res.dropped = dropped
    return res


# --------------------------------------------------------------------------
# gate decision
# --------------------------------------------------------------------------

def gate_decision(res):
    g = res.config.get("gate") or {}
    fail_on = g.get("fail_on") or "error"
    if fail_on not in FAIL_ON_VALUES:
        res.warnings.append("gate.fail_on %r is not one of %s; using error" % (fail_on, "/".join(FAIL_ON_VALUES)))
        fail_on = "error"
    block_on = g.get("block_on") or "introduced"
    if block_on not in BLOCK_ON_VALUES:
        res.warnings.append("gate.block_on %r is not one of %s; using introduced"
                            % (block_on, "/".join(BLOCK_ON_VALUES)))
        block_on = "introduced"
    out = {"applies": False, "enabled": bool(g.get("enabled")), "fail_on": fail_on,
           "block_on": block_on, "rel_path": None, "reason": ""}
    if not out["enabled"]:
        out["reason"] = "gate.enabled is not true in the project config"
        return out
    if not res.project or os.path.isdir(res.target):
        out["reason"] = "no project, or target is a directory"
        return out
    if not res.target.lower().endswith(MARKDOWN_EXTS):
        out["reason"] = "not a Markdown file (the gate covers %s)" % ", ".join(MARKDOWN_EXTS)
        return out
    rel = rel_under(res.target, res.project)
    if rel is None:
        out["reason"] = "target is outside the project"
        return out
    out["rel_path"] = rel
    include = g.get("include")
    if include is None:
        include = ["**/*.md"]
    elif not isinstance(include, list):
        include = [include]
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


def fmt_brief(res, gate=None):
    """The short form for a skill preamble: everything a model needs to
    decide, nothing it has to page through."""
    L = ["respeak config for %s" % res.short(res.target)]
    L.append("project: %s (%s)" % (res.short_abs(res.project) if res.project else "(none found)", res.project_how))
    L.append(res.provider_line())
    present = []
    for lay in res.layers:
        if lay.present:
            present.append("%s %s" % (lay.kind, res.short(lay.label)) if lay.kind not in ("plugin", "userconfig")
                           else lay.kind)
            for a in res.applied:
                if a.kind == "scope" and a.label.startswith(lay.label + "#"):
                    present.append("scope %s" % res.short(a.label[len(lay.label):]))
    L.append("layers applied: " + ", ".join(present))
    s = summary(res)
    tone = get_dotted(res.config, "narrative.tone", {}) or {}
    L.append("effective narrative: mode=%s tech_level=%s profile=%s context=%s tone(f=%s d=%s c=%s) auto_narrative=%s"
             % (s["mode"], s["tech"], s["profile"], s["context"], tone.get("formality"), tone.get("directness"),
                tone.get("confidence"), str(s["auto_narrative"]).lower()))
    lex = get_dotted(res.config, "narrative.lexicon_access")
    if lex:
        L[-1] += " lexicon_access=%s" % lex
    if gate is not None:
        L.append("gate: enabled=%s fail_on=%s block_on=%s applies=%s (%s)"
                 % (str(gate["enabled"]).lower(), gate["fail_on"], gate["block_on"],
                    str(gate["applies"]).lower(), gate["reason"]))
    else:
        L.append("gate: %s" % s["gate"])
    plugin = res.plugin_label()
    n_over = len([k for k, v in res.origins.items() if not v.startswith(plugin) and not k.startswith("profiles.")])
    L.append("overrides: %d key(s) set above the plugin defaults; `explain` without --brief lists them" % n_over)
    for w in res.warnings:
        L.append("warning: %s" % res.short(w))
    return "\n".join(L)


def fmt_explain(res, gate=None):
    L = []
    L.append("respeak config for %s" % res.short(res.target))
    L.append("project: %s (%s)" % (res.short_abs(res.project) if res.project else "(none found)", res.project_how))
    L.append(res.provider_line())
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
        L.append("gate: enabled=%s fail_on=%s block_on=%s applies=%s (%s)"
                 % (str(gate["enabled"]).lower(), gate["fail_on"], gate["block_on"],
                    str(gate["applies"]).lower(), gate["reason"]))
    else:
        L.append("gate: %s" % s["gate"])
    if res.warnings:
        L.append("")
        L.append("warnings:")
        for w in res.warnings:
            L.append("  %s" % res.short(w))
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
    return "\n".join(L)


# --------------------------------------------------------------------------
# validate
# --------------------------------------------------------------------------

def guess_kind(path, env):
    path = real(path)
    base = os.path.basename(path)
    if base in (FOLDER_FILE, FOLDER_LOCAL):
        return "folder"
    norm = path.replace(os.sep, "/")
    if norm.endswith("config/respeak.config.yaml"):
        return "plugin"
    cfgdir = user_config_dir(env)
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
        k = k.strip()
        val = parse_set_value(v)
        if k in APPEND_LISTS + ("gate.include",) and not isinstance(val, list) and val is not None:
            val = [val]
        set_dotted(ov, k, val)
    return ov


def parse_set_value(raw):
    """YAML scalar parsing for --set, minus the YAML 1.1 surprise that turns
    yes/no/on/off into booleans."""
    s = raw.strip()
    if s == "":
        return None
    if s.lower() in ("yes", "no", "on", "off"):
        return s
    try:
        return yaml.load(s, Loader=_Loader)
    except yaml.YAMLError:
        return s  # a bare glob such as **/*.md is not YAML; take it literally


def add_common(p):
    p.add_argument("--project", default=None, help="project root (default: $CLAUDE_PROJECT_DIR, else discovered)")
    p.add_argument("--for", dest="target", default=None, help="file or directory the config is for (default: cwd)")
    p.add_argument("--plugin-root", default=None, help="plugin root (default: $CLAUDE_PLUGIN_ROOT, else this checkout)")
    p.add_argument("--walk-from", default=None, help="only look for .respeak.yaml at or below this directory")
    p.add_argument("--launch-dir", nargs="?", const="", default=None,
                   help="where Claude Code was started (the fallback project root; same role as "
                        "$CLAUDE_PROJECT_DIR); an empty value means not given")
    p.add_argument("--mode", choices=("eli5", "bluf", "technical"), default=None)
    p.add_argument("--profile", default=None)
    p.add_argument("--context", choices=("incident", "routine", "celebration"), default=None)
    p.add_argument("--set", action="append", default=[], metavar="KEY=VALUE")
    p.add_argument("--session", default=None, metavar="ID",
                   help="session id for claude-code-session's resolved file "
                        "(default: $CLAUDE_CODE_SESSION_ID)")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="respeak-config", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("resolve", help="print the effective configuration")
    add_common(p)
    p.add_argument("--format", choices=("yaml", "json", "line", "statusline"), default="yaml")
    p.add_argument("--out", default=None, help="write the output to this file instead of stdout")

    p = sub.add_parser("explain", help="show every layer and which one set each override")
    add_common(p)
    p.add_argument("--brief", action="store_true", help="a few lines: project, layers, effective narrative, gate, warnings")

    p = sub.add_parser("gate", help="decide whether the style gate applies to --for")
    add_common(p)
    p.add_argument("--write-config", default=None, help="also write the resolved config (YAML) here")
    p.add_argument("--committed", action="store_true",
                   help="the CI verdict: gate.* keys from the plugin defaults and the project file "
                        "with its scopes only; every other layer's are dropped and listed in `dropped`")

    p = sub.add_parser("validate", help="check config files for shape and policy")
    p.add_argument("files", nargs="+")
    p.add_argument("--plugin-root", default=None)
    p.add_argument("--project", default=None, help=argparse.SUPPRESS)      # accepted for symmetry
    p.add_argument("--launch-dir", nargs="?", const="", default=None, help=argparse.SUPPRESS)
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
                  env=env, overrides=overrides, walk_from=args.walk_from,
                  launch_dir=args.launch_dir or None, session_id=args.session or None,
                  committed=getattr(args, "committed", False))

    if args.cmd == "resolve":
        if args.format == "yaml":
            text = yaml.safe_dump(res.config, sort_keys=False, default_flow_style=False)
        elif args.format == "json":
            text = json.dumps(res.config, indent=2) + "\n"
        elif args.format == "line":
            text = fmt_line(res) + "\n"
        else:
            text = fmt_statusline(res) + "\n"
        if args.out:
            with open(args.out, "w") as f:
                f.write(text)
        else:
            sys.stdout.write(text)
        for w in res.warnings:
            sys.stderr.write("respeak-config: %s\n" % w)
        return 0

    if args.cmd == "explain":
        gate = gate_decision(res) if not os.path.isdir(res.target) else None
        print(fmt_brief(res, gate) if args.brief else fmt_explain(res, gate))
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
        if args.committed:
            decision["committed"] = True
            decision["dropped"] = res.dropped
        print(json.dumps(decision))
        return 0
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as e:  # noqa: BLE001 — a usage/setup problem, never a traceback (exit 2)
        sys.stderr.write("respeak-config: %s: %s\n" % (type(e).__name__, e))
        sys.exit(2)
