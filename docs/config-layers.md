# Layered configuration

Respeak resolves its configuration from layers, and the layer nearest the
file being written or rendered wins. A personal default in
`~/.claude/respeak/config.yaml`, a project baseline in a repo's
`.claude/respeak/config.yaml`, and a three-line `.respeak.yaml` in
`docs/exec/` compose into one effective configuration per target path. One
command shows the result and which layer decided each key:

```sh
bash "${CLAUDE_PLUGIN_ROOT}/scripts/respeak-config.sh" explain --for docs/exec/q3.md
```

This document is the contract. `scripts/respeak-config.py` implements it,
`tests/test_config_layers.py` pins it, and `examples/layered/` is a runnable
tree whose outcomes the tests check.

## Why layers

Tone depends on where the writing lives. The same repository holds an
executive brief and an API note; the same person reads BLUF at work and
writes household notes for a family that reads ELI5. Before v0.4 respeak had
exactly one override, `<project>/.claude/respeak/config.yaml`, so none of
that could be expressed without editing a shared file every time.

Claude Code already solves this shape for its own settings and context
files, so respeak copies the mechanisms rather than inventing new ones:

| Claude Code mechanism | Respeak analog |
| --- | --- |
| `~/.claude/settings.json` (user scope) | `~/.claude/respeak/config.yaml`, honouring `CLAUDE_CONFIG_DIR` |
| `.claude/settings.json` (project scope, shared) | `.claude/respeak/config.yaml` |
| `.claude/settings.local.json` (personal, gitignored) | `.claude/respeak/config.local.yaml` and `.respeak.local.yaml` |
| plugin `userConfig`, exported as `CLAUDE_PLUGIN_OPTION_*` | the three install-time knobs, one layer above the plugin defaults |
| `CLAUDE.md` in parent directories and in subdirectories | the `.respeak.yaml` walk from the filesystem root down to the target |
| `.claude/rules/*.md` with `paths:` frontmatter | `scopes:` entries with `paths:` globs |
| `--settings <file>` and managed settings | files named in `RESPEAK_CONFIG`, near the top of the stack |
| hooks receive `CLAUDE_PROJECT_DIR`, `cwd`, `tool_input.file_path`; the statusline receives `workspace.project_dir` | the launch directory is the fallback project root; the target path is what each consumer resolves for |
| nested `.claude/skills/` in a monorepo package apply to that package | a nested `.claude/respeak/config.yaml` is the project for the files under it |

## The layers

Lowest precedence first. "May set" is explained under
[What each layer may set](#what-each-layer-may-set).

| # | Layer | File | Edited by | In git | May set |
| --- | --- | --- | --- | --- | --- |
| 1 | plugin | `${CLAUDE_PLUGIN_ROOT}/config/respeak.config.yaml` | the plugin | plugin repo | everything |
| 2 | userConfig | `claude plugin install respeak --config default_mode=bluf` | you, at install | no | `default_mode`, `tech_level`, `auto_narrative` |
| 3 | user | `${CLAUDE_CONFIG_DIR:-~/.claude}/respeak/config.yaml` | you | your dotfiles | tone keys |
| 4 | ancestors | `<dir>/.respeak.yaml` in every directory above the project root, outermost first | you | no | tone keys |
| 5 | project | `<project>/.claude/respeak/config.yaml` | the project | yes | everything |
| 6 | project local | `<project>/.claude/respeak/config.local.yaml` | you | gitignored | everything |
| 7 | folders | `<dir>/.respeak.yaml` and `.respeak.local.yaml` from the project root down to the target's directory, nearest last | folder owners | yes / gitignored | tone keys |
| 8 | env | files listed in `RESPEAK_CONFIG` (colon-separated) | CI, one-off runs | no | everything |
| 9 | invocation | `--mode`, `--profile`, `--context`, `--set key=value`; `/respeak:respeak bluf` | the caller | no | everything |

`scopes:` entries are not a layer of their own. Each one is applied right
after the file that declares it, when one of its `paths` globs matches the
target. A scope in the project file therefore sits between 5 and 6 and
loses to `config.local.yaml`; a scope in a folder file sits with that
folder. Scopes may set tone keys only.

A file that is absent is skipped. A file that fails to parse, or whose top
level is not a mapping, is skipped with a warning that `explain` prints.

## Precedence and merge rules

**Nearest wins.** The stack is one walk from the filesystem root down to
the target's directory, with the user file before it and the invocation
after it. The project's two files sit at the project root's position in the
walk, so an ancestor `.respeak.yaml` in `~/src/` is below the project file
and a `.respeak.yaml` in `docs/exec/` is above it.

**Maps merge, scalars replace.** `narrative: {tone: {formality: 0.9}}` in a
folder file changes formality and leaves directness and confidence alone.
A mapping is never replaced by a scalar or a list: a layer that writes
`narrative: [a, b]` gets a warning and no effect.

**Lists replace, except two that append.** `gate.allow` and `gate.exclude`
accumulate across layers and deduplicate, so a user-level allow list for a
domain vocabulary composes with a project's. Every other list
(`style.readability_metrics`, `gate.include`, a mode's `checks`) is
replaced whole by the nearest layer that sets it.

**There is no unset.** A layer that wants the plugin default writes the
default value. `null` is a real value in this config
(`reading_level_grade: null` means no ceiling), so it cannot double as
"delete".

**`narrative.profile` is sugar, expanded where it is written.** When a
layer says `narrative: {profile: exec}`, the resolver looks up `exec` in
the profile table: `profiles:` as merged so far, deep-merged with any
`profiles:` the same layer defines. It fills in `tech_level`,
`default_mode`, `lexicon_access`, `reading_level_grade`, and `address`
underneath that layer's own explicit keys. So `narrative: {profile: exec,
tech_level: 2}` yields exec's BLUF mode with tech_level 2, and a layer that
refines one field of a shipped profile (`profiles: {exec: {tech_level:
2}}`) still gets the profile's other fields. An explicit key in a nearer
layer still wins over the expansion. The resolved `narrative.profile`
names the last profile applied, which is a label, not a guarantee that
every field still matches it. An unknown profile name is a warning; the
name is not recorded and the layer's other keys still apply.

**Scopes.** Any file may carry a `scopes:` list. Each entry needs `paths`
(a glob or list of globs) and the keys it overrides; entries are applied in
order, so later entries win, and each applies right after the file that
declares it. Globs are relative to the directory that owns the file: the
project root for the project files, the folder for a folder file. The user
file has no owning directory, so its scope paths must be absolute or
`~`-prefixed and are matched against the target's absolute path. A scope's
overlay may itself use `narrative.profile`; nested `scopes` are ignored
with a warning.

**Globs** are gitignore-flavoured. `**` matches any number of path
segments, including none; `*` matches within one segment; `?` matches one
character. A trailing `/` means the directory and everything in it
(`reports/` equals `reports/**`). A pattern with no `/` matches a file or
directory of that name at any depth, contents included: `*.md` equals
`**/*.md`, and `exec` matches `docs/exec/` and everything under it. When the target is a directory (the Stop
hook and the statusline resolve for the cwd) it is matched with a trailing
slash, so `docs/**` matches `docs/` but not the project root.

## What each layer may set

Two invariants from the architecture survive the layering. **The
translator proposes, config disposes, the human ratifies**: governance
stays in one git-reviewed file. **The gate is per-project opt-in**: the
corpus never silently gates someone else's repo. A key policy enforces
both.

| Keys | Allowed from | Why |
| --- | --- | --- |
| `gate.enabled`, `gate.include`, `gate.exclude` | plugin, project, project local, env, invocation | turning enforcement on and choosing which files it covers is a project decision; a stray folder file cannot flip it. The gate covers Markdown files only (`.md`, `.markdown`, `.mdx`, any letter case): `include` and `exclude` narrow within that set, and `explain` says "not a Markdown file" for anything else. The shipped `include` is `**/*.md`; list `**/*.mdx` or `**/*.markdown` to cover those too |
| `shorthand.*` | same | ratification mode, legibility floor, never-compress classes, and the lexicon path must not vary by folder or by user |
| `style.banned_phrases`, `style.replacements`, `style.rules` | same | corpus pointers are resources, not tone |
| `version`, `schema` | same | file identity |
| everything else (`narrative`, `modes`, `profiles`, `style` budgets and switches, `editorial_pass`, `data`, `gate.fail_on`, `gate.allow`) | any layer | tone, and per-file leniency |

A project-only key in a user, ancestor, folder, or scope layer is dropped
and reported once under `warnings:` by `explain`; `validate` on that file
exits 1 and names the key. `gate.fail_on` is deliberately open: a folder of
drafts can say `gate: {fail_on: none}` and the hook still runs there but
never blocks.

## The target path and the project root

Every consumer resolves for one path. The rule is "the thing being written
or rendered", so a folder's `.respeak.yaml` governs the files in it.

| Entry point | Target | Launch directory it passes |
| --- | --- | --- |
| PostToolUse gate hook (`respeak-gate.sh`) | `tool_input.file_path` | `CLAUDE_PROJECT_DIR` (exported to hooks) |
| `/respeak:respeak` skill | the source file when one is given, else the working directory | `${CLAUDE_PROJECT_DIR}` via `--launch-dir` |
| Stop hook auto-narrative (`stop-narrative.sh`) | the hook's `cwd` | `CLAUDE_PROJECT_DIR` |
| statusline (`statusline.sh`) | `workspace.current_dir` | `workspace.project_dir` via `--launch-dir` |
| headless render (`respeak-render.sh`) | `--out`, the file being produced, with `--mode` on top | `CLAUDE_PROJECT_DIR` when set |
| CLI | `--for PATH` (default: cwd) | `--launch-dir DIR`, else `CLAUDE_PROJECT_DIR` |

**One rule finds the project root for all of them**, so the tool that says
enforcement is on and the tool that enforces never disagree:

1. `--project DIR`, when given, verbatim.
2. The nearest ancestor of the target (its own directory included) holding
   `.claude/respeak/config.yaml`. In a monorepo a package's own file is the
   project for the files under it. A file in a parent directory, such as
   `~/src/.claude/respeak/config.yaml`, governs every repo below it, the
   way a parent `CLAUDE.md` does. The user config directory is never a
   project: `~/.claude/respeak/config.yaml` is the user layer and is not
   loaded a second time at project grade, even for a session launched in
   `~`.
3. The launch directory: `--launch-dir`, else `CLAUDE_PROJECT_DIR`, the
   directory where Claude Code was started. This is where a session with
   no respeak config at all lands, so `/respeak:init` seeds the file there.
4. The nearest ancestor holding `.git` or `.claude/`, again never `~`.

`explain` prints which rule chose the root next to `project:`. Paths are
compared after symlink resolution, and on macOS and Windows after case and
Unicode folding as well, so `/tmp` and `/private/tmp`, a `~/src` symlink,
and `~/Src/Proj` typed for `~/src/proj` all name the same project. A file
counts as inside the project when either its path as given or its resolved
path is under the root: a symlink inside the project that points elsewhere
is still the project's file and is still gated.

A target outside the project still gets the project layers (they are a
property of the session) but none of the project's folder files, and the
gate never applies to it. Directories above the project root keep their
place below it wherever the target lives; a `.respeak.yaml` in the
outsider's own directory chain, below their common ancestor, is nearer and
wins. A target that does not exist yet (`--out` of a render) resolves by
its directory.

## Worked examples

The tree in [`examples/layered/`](../examples/layered/) is a small project
plus a sample user file. Point `CLAUDE_CONFIG_DIR` at the sample home to
include the user layer:

```sh
export CLAUDE_CONFIG_DIR=$PWD/examples/layered/home/.claude
P=examples/layered/project
```

The files, trimmed to what matters:

```yaml
# home/.claude/respeak/config.yaml   (user layer)
narrative: { default_mode: bluf, tech_level: 2 }
profiles:
  household: { tech_level: 2, default_mode: eli5, lexicon_access: forbidden, reading_level_grade: 8, address: you }
scopes:
  - paths: ["~/src/some-repo/**"]
    narrative: { tone: { formality: 0.9, directness: 1.0 } }
gate: { allow: ["spine"] }

# project/.claude/respeak/config.yaml   (project layer)
narrative: { default_mode: technical, tech_level: 3 }
gate: { enabled: true, include: ["**/*.md"], exclude: ["notes/**"], fail_on: error, allow: ["load-bearing"] }
scopes:
  - paths: ["docs/**"]
    narrative: { profile: peer-engineer }
  - paths: ["docs/exec/**", "reports/**"]
    narrative: { profile: exec }
    gate: { fail_on: warn }

# project/.claude/respeak/config.local.yaml   (personal, gitignored)
narrative: { tone: { formality: 0.2 } }

# project/docs/exec/.respeak.yaml
narrative: { tone: { formality: 0.8 } }

# project/docs/api/.respeak.yaml
narrative: { profile: author }

# project/notes/.respeak.yaml
narrative: { profile: author }
gate: { enabled: false }      # ignored: project-only
```

What each file gets:

| Target | mode | tech_level | profile | formality | gate applies (fail_on) | decided by |
| --- | --- | --- | --- | --- | --- | --- |
| `README.md` | technical | 3 | peer-engineer | 0.2 | yes (error) | project; formality from config.local |
| `docs/overview.md` | technical | 3 | peer-engineer | 0.2 | yes (error) | scope `docs/**` |
| `docs/exec/q3-summary.md` | bluf | 1 | exec | 0.8 | yes (warn) | scope `docs/exec/**`; formality from the folder file |
| `docs/api/endpoints.md` | technical | 5 | author | 0.2 | yes (error) | folder file beats scope `docs/**` |
| `reports/week-36.md` | bluf | 1 | exec | 0.2 | yes (warn) | scope `docs/exec/**, reports/**` |
| `notes/scratch.md` | technical | 5 | author | 0.2 | no (excluded) | folder file; its `gate.enabled` is ignored |

`explain` for the executive summary (output of
`bash scripts/respeak-config.sh explain --project $P --for $P/docs/exec/q3-summary.md --walk-from $P`;
the user file shows under `<plugin>/` only because the sample home lives
inside the plugin checkout):

```
respeak config for docs/exec/q3-summary.md
project: <checkout>/examples/layered/project (--project)

layers, lowest precedence first (* = present and applied):
  * plugin         <plugin>/config/respeak.config.yaml
    userconfig     plugin userConfig CLAUDE_PLUGIN_OPTION_* (absent)
  * user           <plugin>/examples/layered/home/.claude/respeak/config.yaml
  * project        .claude/respeak/config.yaml
  * scope          .claude/respeak/config.yaml#scopes[0]
  * scope          .claude/respeak/config.yaml#scopes[1]
  * project-local  .claude/respeak/config.local.yaml
  * folder         docs/exec/.respeak.yaml
    invocation     invocation (--mode/--profile/--context/--set) (absent)
    (2 directories walked with no .respeak.yaml)

effective narrative: mode=bluf tech_level=1 profile=exec context=routine tone(f=0.8 d=0.9 c=0.8) auto_narrative=false lexicon_access=forbidden
gate: enabled=true fail_on=warn applies=true (matched gate.include and not gate.exclude)

overrides (key = value <- layer):
  gate.allow                    = ["spine", "load-bearing"] <- <plugin>/examples/layered/home/.claude/respeak/config.yaml + .claude/respeak/config.yaml
  gate.enabled                  = true                     <- .claude/respeak/config.yaml
  gate.exclude                  = ["notes/**"]             <- .claude/respeak/config.yaml
  gate.fail_on                  = warn                     <- .claude/respeak/config.yaml#scopes[1]
  gate.include                  = ["**/*.md"]              <- .claude/respeak/config.yaml
  narrative.address             = you                      <- .claude/respeak/config.yaml#scopes[1] (profile exec)
  narrative.default_mode        = bluf                     <- .claude/respeak/config.yaml#scopes[1] (profile exec)
  narrative.lexicon_access      = forbidden                <- .claude/respeak/config.yaml#scopes[1] (profile exec)
  narrative.profile             = exec                     <- .claude/respeak/config.yaml#scopes[1]
  narrative.reading_level_grade = 9                        <- .claude/respeak/config.yaml#scopes[1] (profile exec)
  narrative.tech_level          = 1                        <- .claude/respeak/config.yaml#scopes[1] (profile exec)
  narrative.tone.formality      = 0.8                      <- docs/exec/.respeak.yaml
  profiles.household            = {"tech_level": 2, "default_mode": "eli5", "lexicon_access": "forbidden", "reading_level_grade": 8, "address": "you"} <- <plugin>/examples/layered/home/.claude/respeak/config.yaml
  version                       = 3                        <- .claude/respeak/config.yaml
```

Reading it: the project's second scope made the folder `exec` (profile
expansion is marked `(profile exec)` on each field it filled), the folder's
own file raised formality, `config.local.yaml` lost on formality because
the folder file is nearer, and the user file's allow list appended to the
project's.

The other commands, on the same tree:

```
$ bash scripts/respeak-config.sh resolve --project $P --for $P/docs/api/endpoints.md --format statusline --walk-from $P
technical/t5 author @docs/api/.respeak.yaml
$ bash scripts/respeak-config.sh gate --project $P --for $P/reports/week-36.md --walk-from $P
{"applies": true, "enabled": true, "fail_on": "warn", "rel_path": "reports/week-36.md", "reason": "matched gate.include and not gate.exclude", "warnings": []}
$ bash scripts/respeak-config.sh validate $P/notes/.respeak.yaml
examples/layered/project/notes/.respeak.yaml [folder]: ERROR
  error: <checkout>/examples/layered/project/notes/.respeak.yaml: gate.enabled is project-only; ignored
$ bash scripts/respeak-config.sh explain --brief --project $P --for $P/notes/scratch.md --walk-from $P
respeak config for notes/scratch.md
project: <checkout>/examples/layered/project (--project)
layers applied: plugin, user <plugin>/examples/layered/home/.claude/respeak/config.yaml, project .claude/respeak/config.yaml, project-local .claude/respeak/config.local.yaml, folder notes/.respeak.yaml
effective narrative: mode=technical tech_level=5 profile=author context=routine tone(f=0.2 d=0.9 c=0.8) auto_narrative=false lexicon_access=inline
gate: enabled=true fail_on=error applies=false (matched by gate.exclude)
overrides: 13 key(s) set above the plugin defaults; `explain` without --brief lists them
warning: notes/.respeak.yaml: gate.enabled is project-only; ignored
```

### Recipes

**A personal default across every repo.** Nothing in any project changes.

```yaml
# ~/.claude/respeak/config.yaml
narrative:
  default_mode: bluf
  tech_level: 2
```

**One repo pins technical and turns the gate on.** `/respeak:init` seeds
this file sparse; add only what the project changes.

```yaml
# .claude/respeak/config.yaml
version: 3
narrative: { default_mode: technical, tech_level: 3 }
gate:
  enabled: true
  exclude: ["research/**"]
```

**Folder audiences.** Three files, three lines each, owned by the folders.

```yaml
# docs/exec/.respeak.yaml
narrative: { profile: exec }
# docs/api/.respeak.yaml
narrative: { profile: author }
# family/.respeak.yaml
narrative: { profile: household }   # defined once in ~/.claude/respeak/config.yaml
```

**The same, declared centrally.** One reviewable block in the project
file, the `.claude/rules` idiom.

```yaml
scopes:
  - paths: ["docs/**"]
    narrative: { profile: peer-engineer }
  - paths: ["docs/exec/", "reports/"]
    narrative: { profile: exec }
    gate: { fail_on: warn }
  - paths: ["drafts/"]
    gate: { fail_on: none }
```

**A personal override for one repo,** without touching the shared file:
`.claude/respeak/config.local.yaml` (gitignored by `/respeak:init`) at
project scope, or `.respeak.local.yaml` beside a folder file.

**A tone for a whole group of repos.** An ancestor file applies to every
project under it, tone keys only:

```yaml
# ~/src/.respeak.yaml
narrative: { context_default: routine }
style: { budgets: { emdash_per_1000_words: 2 } }
```

Or the same from the user file, keyed by absolute path:

```yaml
# ~/.claude/respeak/config.yaml
scopes:
  - paths: ["~/src/some-repo/**"]
    narrative: { tone: { formality: 0.9, directness: 1.0 } }
```

**CI.** The gate hook doubles as a command: `respeak-gate.sh --file PATH`
runs exactly what the PostToolUse hook runs for that file, so CI enforces
the same layers, the same `fail_on`, and the same Markdown-only contract
the editor session saw. A CI-only file on `RESPEAK_CONFIG` can harden the
verdict for the build. Use `find`, not `**`: bash 3.2 (the macOS default)
and GitHub Actions' default shell have no `globstar`, so `wiki/**/*.md`
silently matches one directory level there.

```sh
export RESPEAK_CONFIG=ci/respeak-ci.yaml        # e.g. gate: {fail_on: warn}
export RESPEAK_GATE_TRACE=1                     # say "pass" / "not applicable" per file
find wiki -name '*.md' -print0 | while IFS= read -r -d '' f; do
  bash scripts/respeak-gate.sh --file "$f" || exit 1
done
```

Without `CLAUDE_PROJECT_DIR` in the environment, the root is discovered
from each file (rule 2 above), so the checkout's own
`.claude/respeak/config.yaml` must carry `gate.enabled: true`.

**One render, one audience.** The invocation layer beats every file:
`/respeak:respeak eli5 notes/plan.md`, or headless
`respeak-render.sh --mode bluf --out docs/exec/q3.md ...`, where the
folder's tone applies and `--mode` sits on top of it.

## Inspecting and validating

| Command | Use |
| --- | --- |
| `respeak-config.sh explain [--for PATH]` | the layer stack (present and absent), which rule chose the project root, the effective narrative and gate, warnings, then every override with the layer that set it |
| `respeak-config.sh explain --brief [--for PATH]` | the same in a few lines: project, layers applied, effective narrative, gate, override count, warnings. The `/respeak:respeak` skill injects this at the top of every invocation |
| `respeak-config.sh resolve --for PATH --format yaml\|json [--out FILE]` | the full effective config, for `respeak-measure.py --config` or for a prompt; `--out` writes it without a shell redirect, which a skill's `allowed-tools` rule would not cover |
| `respeak-config.sh resolve --for PATH --format line\|statusline` | one-line summaries; the statusline form is `bluf/t1 exec @docs/exec/.respeak.yaml` |
| `respeak-config.sh gate --for FILE [--write-config PATH]` | the gate hook's decision as JSON (`applies`, `fail_on`, `reason`), optionally writing the resolved YAML |
| `respeak-config.sh validate FILE...` | parse, unknown top-level keys, scope shape, and key policy for the file's kind (guessed from its path, or `--kind`); exits 1 on a policy violation |
| `respeak-gate.sh --file PATH` | the hook's decision and verdict for one file, as an exit code (0 allow, 2 block); `RESPEAK_GATE_TRACE=1` adds a one-line reason on stderr |

Every command takes `--launch-dir DIR` (the directory Claude Code was
started in, the same role as `CLAUDE_PROJECT_DIR`; an empty value means
not given) and `--project DIR` to pin the root outright, used as resolved;
`validate` accepts both and ignores them. `--set key=value` parses the
value as a YAML scalar: `yes`, `no`, `on`, and `off` become booleans on a
boolean key and stay strings elsewhere, a value that is not YAML (a bare
glob such as `**/*.md`) is taken literally, and a scalar given for
`gate.allow`, `gate.exclude`, or `gate.include` becomes a one-item list.

The statusline segment shows the effective mode at a glance: `technical/t3`
means the plugin default applies; `bluf/t1 exec @docs/exec/.respeak.yaml`
names the layer that decided.

`--walk-from DIR` restricts the folder walk to directories at or below DIR;
the tests use it for determinism and CI can use it to ignore whatever sits
above a checkout.

## Session overrides

The layers say what respeak should do in a place. Two overrides say what it
does in the session you are in, without touching any file in the project.
The plugin manifest registers all three hooks for every installer; these
are how one session declines them.

| Override | Scope | Set by | Effect |
| --- | --- | --- | --- |
| session marker | one Claude Code session | `/respeak:off [gate]`, `/respeak:on [gate]` (`scripts/respeak-session.sh`) | `off`: every hook silent; `gate-off`: only the gate; `gate-on`: the gate runs as if `gate.enabled` were true |
| environment | one launch, or wherever the variable is exported | `RESPEAK_HOOKS=off`, `RESPEAK_GATE=off` or `RESPEAK_GATE=on` | same three effects |

Precedence: marker, then environment, then the layers. `RESPEAK_GATE=on`
and the `gate-on` marker apply the resolved project configuration with
`gate.enabled` forced true, so `include`, `exclude`, `fail_on`, and
`allow` still hold. The `--file` form of the gate has no session, so only
the environment applies to it (CI is the intended user).

Markers live under `${RESPEAK_CACHE_DIR:-${XDG_CACHE_HOME:-~/.cache}/respeak}/session/<session_id>`,
hold one word, and are swept when older than 24 hours, so a session that
crashed never leaves a silent hook behind. A marker with any other content
is ignored. The session id is the one Claude Code hands to hooks on stdin
and to skills as `CLAUDE_SESSION_ID`; without one, `/respeak:off` refuses
and points at the environment variables.

`respeak-config.sh explain` ends with a `session overrides:` line, so the
tool that shows the effective configuration also shows the override the
hooks saw. A durable personal preference is not a session override: put it
in `config.local.yaml`.

## Trust boundaries

- **A folder or user file cannot change enforcement or governance.** The
  key policy above is enforced in the resolver. The gate hook, the skill,
  and the headless renderer all see the same dropped keys.
- **Ancestor files above the project apply,** like parent-directory
  `CLAUDE.md` files. A `.respeak.yaml` in `~/src/` shapes tone for every
  repo under it; it still cannot enable the gate. `explain` lists it.
- **Personal files stay personal.** `/respeak:init` offers the two
  gitignore lines; the plugin repo's own `.gitignore` carries them.
- **A parent directory's `.claude/respeak/config.yaml` is a project file.**
  Whoever creates `~/src/.claude/respeak/config.yaml` has opted every repo
  below it into that file's gate settings, the way a parent `CLAUDE.md`
  applies to every repo below it. `explain` names the file next to
  `project:`; `/respeak:init` reports when the root it found is not the
  current directory.
- **Hooks fail open.** No PyYAML-capable python, a missing resolver, a
  resolver error, or a measure setup error means the gate allows; only a
  real style-gate verdict blocks. Setup errors include an unreadable or
  non-UTF-8 file, a corpus with the wrong shape or an invalid regex, and an
  invalid `gate.allow` regex; the measure script exits 2 for every failure
  that is not a verdict, uncaught exceptions included, because CPython's
  exit 1 for a traceback would otherwise read as a verdict.
  `RESPEAK_GATE_TRACE=1` makes the hook say on stderr which of those
  happened, and a test suite pins each case. The Stop hook has one layer
  that needs no YAML, the install-time `auto_narrative` knob, and honours
  it alone when the resolver cannot run. The scripts pick the first
  interpreter that can import PyYAML (`scripts/respeak-python.sh`;
  `RESPEAK_PYTHON` overrides) and parse hook JSON with the same one. A
  `python3` shim without PyYAML, or one that exits 127, used to make every
  hook a silent no-op.
- **The interpreter cache cannot be used to run arbitrary code.** It lives
  in `${XDG_CACHE_HOME:-~/.cache}/respeak/` (or `RESPEAK_CACHE_DIR`), a
  directory created `0700` that must be owned by the caller and not a
  symlink; the file must be a regular owner-owned file; and the cached
  name is honoured only if it is one of the fixed candidates
  (`python3`, `/usr/bin/python3`, the brew pythons). A tampered file can at
  worst select a different known interpreter. No usable directory means no
  cache, never a fallback to `/tmp`.

## Upgrading from v0.3

- **A project config seeded by v0.3 `/respeak:init` is a full copy of the
  plugin defaults.** It pins every key at project scope, so a user-level
  file never wins inside that project. Run `explain` there: every key it
  lists under `overrides` with `<- .claude/respeak/config.yaml` is pinned.
  Delete the keys the project did not mean to set, or replace the file
  with `config/project-seed.yaml` and re-add the project's own values.
- **The install-time userConfig knobs are now a layer.** They sit above
  the plugin defaults and below `~/.claude/respeak/config.yaml`, so a user
  file wins over `claude plugin install --config default_mode=bluf`.
- **`narrative.auto_narrative` moved into the config** (it was env-only).
  The Stop hook reads it through the resolver for the session's cwd, so a
  project or folder can turn milestone narratives on.
- **Refresh the installed copy.** The plugin cache is a snapshot: run
  `claude plugin update respeak` so the hooks load the resolver.
- **`${CLAUDE_PROJECT_DIR}` in skills needs Claude Code 2.1.196 or later.**
  On older versions the skill's `--launch-dir` is empty. The project root
  then comes from rule 2 or rule 4 above, which is still the answer the
  hook gives.
- **The plugin must be installed under a path without spaces.** The
  skills pre-approve their own scripts with `allowed-tools: Bash(<plugin
  root>/scripts/respeak-config.sh *)`, and Claude Code's Bash permission
  matcher (2.1.261) cannot match a command whose script path contains a
  space, quoted or escaped, with an absolute or a wildcard rule. Under
  such a root the `!` preamble fails its permission check and Claude Code
  aborts the invocation with zero turns; the hooks, which take no
  permission check, keep working. The default plugin cache path
  qualifies. The SessionStart hook says so when it sees a spaced root, and
  `/respeak:init` reports it.

## Design notes

**Borrowed, not invented.** Every layer maps to a Claude Code mechanism
(table above). The one place respeak departs is the folder file's name:
`.respeak.yaml` rather than a per-folder `.claude/` directory, because
Claude Code has no such convention and a dotfile per directory is what
`.editorconfig`, `.vale.ini`, and `.eslintrc` established.

**Rejected alternatives.**

- *Reusing `.claude/rules/*.md` frontmatter as the config carrier.* Rules
  are prose for the model; this config is data read by shell hooks, a
  statusline, and CI. The `paths:` idiom is borrowed as `scopes:` instead.
- *YAML `extends:`.* The directory walk is the inheritance; an explicit
  chain would let a folder reach sideways into another folder's file and
  break "nearest wins".
- *A user-level `.local` file.* The user file is already personal.
- *A top-level "managed" layer that projects cannot override.* Nothing
  needs it yet; `RESPEAK_CONFIG` covers CI. Add it as a layer between 9
  and 10 if an org-wide style guide ever has to win over projects.

**Cost.** The resolver itself is about 30 ms per call on a 2024 Mac
(PyYAML's C loader; one load per present file). Finding a PyYAML-capable
interpreter used to cost more than that, because a pyenv shim takes about
70 ms per probe, so `respeak-python.sh` caches the answer per `PATH` under
`~/.cache/respeak/` and re-validates it with one launch. Warm, a statusline refresh
is about 100 ms. A gate-hook call on a Markdown write is about 200 ms,
most of it the measure scan. Claude Code debounces statusline updates at
300 ms and cancels an in-flight script on the next trigger.

**Open.** The `schema:` pointer in the plugin config is still a promise;
`validate` checks shape and policy but not value types. A helper that
writes a folder file from a profile name (`respeak-config.sh init-folder
docs/exec --profile exec`) would remove the last bit of typing, and
`mode_select: compass` is scopable today but has no consumer. The
`respeak:respeak` agent has no Bash tool. When a caller hands it no
resolved block, it approximates the stack from the files it can read and
says so in its last line. A caller that wants the exact stack passes the
resolver's output, as the skill and the headless renderer do.
