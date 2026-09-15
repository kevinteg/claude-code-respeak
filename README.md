<img src="assets/respeak-icon.svg" alt="" width="56" align="left">

# respeak

Two-lane communication for AI agent swarms in Claude Code: let the agents
talk in governed shorthand, and give every human a narrative worth reading.

## The problem

Put two people in a room and have them describe the same abstract picture to
each other, over and over. In Clark and Wilkes-Gibbs' classic experiment they
start at about forty words ("the one that looks like a person kneeling with
an arm out..."). They finish, six rounds later, at two: "the skater." That
compression is automatic and useful. A follow-on line of research (Garrod's
graphical-convention studies) measured its cost. Outsiders shown the evolved
signs struggle to interpret them, because the meaning has moved out of the
signs and into the pair's shared history.

Agent swarms do the same thing. A long-running session develops
abbreviations, back-references, and codewords, because every token of
inter-agent traffic is taxed twice. It spends context window, and attention
cost grows quadratically with sequence length. Compression pressure is
structural. Left alone, the swarm's dialect gets cheaper for the agents and
more alien to you. The person supervising the work becomes the outsider
in that experiment, permanently.

Today you get two bad choices. Force the agents to write prose, and you pay
the attention tax on every message, forever. Let the dialect drift, and you
lose the ability to audit your own automation. When Facebook's 2017
negotiation bots drifted out of English, the researchers' fix was to reward
staying in English. That restored legibility by giving up the compression.

## What respeak does

Respeak splits the traffic instead of compromising one channel, and connects
the two lanes with a feedback loop. Our research pass found tools that
compress (Caveman, LLMLingua), tools that narrate (PagerDuty Advance,
LangSmith Insights), and one protocol with the right economics (Oxford's
Agora). It found none that close this loop. The full landscape review is in
[`research/synthesis/solutions-and-media.md`](research/synthesis/solutions-and-media.md).

The **machine lane** stays efficient. Agents may use any shorthand that is
*ratified* in a lexicon file; everything else gets written out in full. To be
clear about the mechanism: nothing intercepts agent traffic. The lane works
by convention plus context. Every session loads a digest of the ratified
lexicon, via a CLAUDE.md import you accept at setup. In projects that ran
`/respeak:init`, a session-start hook also states the lexicon version as
fact.

The governance model comes from the shorthand systems that survived a
century of expert use: aviation phraseology, brevity codes, Q codes. Entries
are proposed, ratified, or retired, never silently edited. Some content may
never be compressed at all: error messages, security findings, user quotes,
numbers with units. Medicine keeps a "do not use" abbreviation list because
compression harmed patients. The `never_compress` config block copies that
pattern, including recording *why* each class is banned.

The **human lane** reads well. A translator subagent renders the swarm's work
as a narrative in one of three modes:

| Mode | Contract |
| --- | --- |
| `eli5` | One idea per sentence, one analogy at most, and the analogy is repaid: the next sentence says the real thing. |
| `bluf` | Sentence one is the result, decision, or ask, with owner and deadline. A manager can forward it unedited. |
| `technical` | Conclusion first, then evidence as `file:line`, then open questions. Technical readers get no fluff; they resent it most. |

Every mode passes the same style gates. There are 234 banned phrases across
22 categories: the catalog of AI tells, from `delve` to `load-bearing`. Each
entry carries a severity, and is marked `owner-preference` where it rests on
taste rather than research. The gates also include 60 replacement rules and
sentence and paragraph budgets taken from Simplified Technical English and
federal plain-language standards. They also include tone axes documented as
behavior tables.

The config's standing rule: a field that maps to no observable behavior gets
deleted. The `warmth` axis already died this way and was replaced by Radical
Candor's three checkable switches.

The **loop** is where the two lanes meet. While translating, the agent
tallies unratified shorthand it had to decode and files proposal entries. It
prefers whichever variant of a convention reads closest to plain English.
A human ratifies. Over a long session the swarm's dialect drifts toward
needing less translation, because the librarian keeps nudging it there.
Nobody fights the optimization, and nobody gets locked out of it.

## Does it work?

One field test so far (2026-08-31, n=1): the translator ran a technical-mode
editorial pass over a 4,000-word internal design document. That document
cannot be published, so treat these numbers as sizing evidence, not a
benchmark. Reproduce the method on your own documents with the scanner
and verifier below.

| Metric | Before | After |
| --- | --- | --- |
| Banned phrases (error severity) | 3 | 0 |
| Banned phrases (warn severity) | 9 | 1 (a deliberate, documented keep) |
| Em-dashes per 1000 words | 19.9 | 3.1 |
| Average sentence length | 32.1 words | 24.5 words |
| Headings, links, code, numbers changed | n/a | zero (`respeak-verify-edit.py` passes) |

The part worth reading the diff for was judgment. The pass kept "a genuine
platform gap" because the corpus bans `genuinely`, not `genuine`. It kept
the author's own contract wording that merely resembled a banned pattern.
And it kept table-cell dashes that carry real value breaks. Numbers are as
measured with the corpus of that date.

## Is an edit safe?

Style edits to real files must be provably meaning-preserving, so the repo
ships a format-aware verifier and a test suite for it:

```sh
python3 scripts/respeak-verify-edit.py <before> <after>   # exit 0 = safe
python3 -m unittest discover tests                        # edit-safety, measure/gate, config layers
bash tests/test_gate_hook.sh                                # gate hook end-to-end (bash, not unittest)
bash tests/test_hooks.sh                                    # Stop hook + statusline end-to-end
bash tests/test_overrides.sh                                # session overrides + the hooks.json event pin
bash tests/test_report_env.sh                               # /respeak:report environment footer
```

| Format | An edit may change | Invariant (checked) |
| --- | --- | --- |
| `.md` | prose | headings/anchors, link and image targets, fenced code, inline code spans, numbers, front matter, admonition types |
| `.ts .tsx .js .jsx .c .go .java .rs` | comments only | all code and string literals byte-identical; numbers even inside comments |
| `.py` | `#` comments only | code and docstrings (docstrings can carry doctests) |
| `.html` | text nodes | tag skeleton and attributes; `script/style/pre/code` byte-identical |
| `.yaml .json` | comments / whitespace | parsed data, deep equality |

Passes allowed to restructure (`editorial_pass: restructure: apply`) are for
when the caller owns relinking, as in a whole-wiki run. For those,
`--allow-restructure` downgrades heading, admonition-type, and front-matter
changes to reported warnings. Link targets, code, and numbers stay hard
failures.

The scanner is local and free:

```sh
python3 scripts/respeak-measure.py path/to/doc.md
```

## Enforcement

The field test above measured after the fact. In practice every style gate
was still a prose instruction to the model, and nothing ran the scanner
against what actually shipped. A rendered set of pages went out with error-
and warn-severity hits and an em-dash density several times the budget.
Separately, the "the spine" metaphor rule false-positived on literal
networking prose ("spine switches"), because the corpus had no exceptions
for the literal sense. The banned term was also present in the *source*
brief, so it propagated into every page rendered from it. This section
closes both gaps.

**The gate hook** (`scripts/respeak-gate.sh`) is a `PostToolUse` hook on
`Write|Edit` (`hooks/hooks.json`) that runs `respeak-measure.py` against any
Markdown file a tool call just wrote. By default that means `.md`;
`.markdown` and `.mdx` count too when `gate.include` lists them. On a
failing report, it blocks the tool result with exit code 2 and puts the
report on stderr. Claude Code feeds that back to the model as a correctable
error. Setup problems (no PyYAML, a corrupt corpus, an unreadable file)
never block: the hook fails open, and `RESPEAK_GATE_TRACE=1` says so on
stderr.

It is **opt-in per project**: it does nothing unless the project layer
(`<project>/.claude/respeak/config.yaml` or its gitignored
`config.local.yaml`) sets `gate.enabled: true`. A user-level file or a
folder `.respeak.yaml` cannot turn it on. They can, though, soften `fail_on`
and add `allow` regexes for their own files (see "Where the tone comes
from"). For one session, `/respeak:off gate` silences it and `/respeak:on gate` runs it where it is off (see "Turning respeak off for a session").
Configure it there:

```yaml
gate:
  enabled: true
  include: ["**/*.md"]     # globs, relative to the project dir
  exclude: ["research/**"] # never gated
  fail_on: error            # none | warn | error
  allow: []                 # regexes — see "Exceptions and allow" below
```

**`--fail-on`**: `respeak-measure.py --fail-on {none,error,warn}`. `none`
(default) only reports: the pre-enforcement behavior. `error` exits 1 if
any document has a banned-phrase error hit. `warn` also trips on
warn-severity hits, density-tier hits, or a budget failure. Exit 2 is
reserved for usage/IO errors. `--json` now emits a list, one entry per
document, so one call can gate a whole tree:

```sh
python3 scripts/respeak-measure.py wiki/**/*.md --fail-on error
```

**Budgets** (`style.budgets` in `respeak.config.yaml`, read via
`--config`) are `emdash_per_1000_words`, `warn_phrases_per_1000_words`,
`avg_sentence_words`, and `max_sentence_words`. The second of those
is checked against the corpus's `tier: density` hits, the common-but-excess
words that flag on density, not per occurrence. Each is measured and
reported PASS/FAIL; a FAIL counts as a warn-level hit for `--fail-on`.

**Exceptions and allow** are two escape hatches at different scopes. A
corpus entry's own `exceptions:` (list of regexes) is scoped to that rule
and ships with the corpus. This is the actual fix for the "spine switches"
false positive. The project-banned `the spine` metaphor rule now exempts
literal networking senses (`spine switch`, `leaf-spine`, `spine1`, `spine
ASN`, a spine peering/draining/reflecting, …). So a networking-heavy doc
keeps the metaphor ban without losing the literal term.

`gate.allow` (project config) is scoped to one project. It skips a rule
entirely for that project's runs, for a domain term the shared
`exceptions:` list doesn't cover yet. Treat `allow` as a stopgap: file the
missing exception upstream rather than leaving a project-local silence as
the permanent fix.

**Verify-then-relay** closes the input-side gap. The `respeak:respeak`
skill no longer relays a rendered narrative on trust. It writes the agent's
output to a temp file and runs `respeak-measure.py --fail-on error` against
it. On failure, it sends the report back to the agent for a rewrite, up to
2 rounds, before relaying.

The `respeak:respeak` agent itself now runs an **input gate** first: it
scans the source material for project-banned terms before rendering. So a
banned term in a brief cannot propagate into the output even when asked to
preserve the source's wording. A passing render reports `gate: N banned
terms removed from source` when it removed any.

**Headless rendering** (`scripts/respeak-render.sh`) runs the same
verify-then-relay loop for the API lane, where there is no interactive
skill to do it. That means CI, or a swarm's own automation. It drives
Claude Code's print mode (`claude -p`) with the system prompt built from
`agents/respeak.md`, read-only tools, and the resolved configuration. Then
it gates and retries the same way the skill does. `RESPEAK_RENDER_CMD`
substitutes any runner that accepts the same flags; `RESPEAK_RENDER_MODEL`
picks the model:

```sh
scripts/respeak-render.sh --mode technical \
  --source notes/draft.md --out docs/guide/03-lesson.md --max-rounds 2
```

**CI usage**: the hook is also a command. `scripts/respeak-check.sh` runs
it over every Markdown file git knows about, tracked or new, with the layers
and verdict an editor session would see. With `--verify <ref>` it also requires every edit since
that ref to be meaning-invariant. This repository runs it on its own docs;
`CLAUDE.md` states the procedure a session here follows.

```sh
bash scripts/respeak-check.sh --verify origin/main   # exit 1 on a block or a changed invariant
bash scripts/respeak-gate.sh --file docs/guide.md    # one file: the hook's verdict as an exit code
```

**Upgrading**: the installed copy under `~/.claude/plugins/cache` is a
snapshot, not a live link. After pulling a change here (corpus, gate hook,
or manifest), run `claude plugin update respeak` (or reinstall). That way
the `PostToolUse` gate hook and corpus edits actually load.

## Install

Prerequisites: Claude Code ≥ 2.1.196, a plugin path without spaces, bash
3.2 or newer, and a python3 (3.9 or newer) with PyYAML. The Claude Code floor
is for `${CLAUDE_PROJECT_DIR}` in skills; older 2.1 works with discovery
alone. The plugin path must have no spaces: Claude Code's
permission matcher cannot pre-approve a script under one, so the skills
would abort. Hooks are unaffected. You also need the GitHub CLI (`gh`), but
only if you use `/respeak:report`.

The scripts pick the first interpreter that can import PyYAML (`python3`,
`/usr/bin/python3`, the brew pythons; override with `RESPEAK_PYTHON`) and
cache the answer per `PATH`. So a pyenv shim without PyYAML on PATH neither
disables the hooks nor taxes every call. If none has it: `python3 -m pip install pyyaml`.

The translator runs as a Sonnet subagent in its own context window, so each
translation costs one subagent invocation proportional to the source
material. The swarm's context never pays for wordsmithing.

Install from GitHub (these write to your `~/.claude` config):

```sh
claude plugin marketplace add kevinteg/claude-code-respeak
claude plugin install respeak@respeak
# optionally: --config default_mode=bluf --config tech_level=2
```

Or try it for one session from a local checkout, which changes nothing
persistent (`RESPEAK_SRC` is wherever you keep source):

```sh
git clone https://github.com/kevinteg/claude-code-respeak "$RESPEAK_SRC"
claude --plugin-dir "$RESPEAK_SRC"
```

Translation works at once in any repository. The lexicon, the style gate,
and a project baseline need a one-time setup per project:

```
/respeak:init
```

This creates `.claude/respeak/`: a sparse project config that states only
what the project changes, the lexicon, and proposals. It generates the
ratified-lexicon digest and shows the effective configuration stack. It
also offers, never forces, three integrations. The first is gitignore
entries for the personal `*.local.yaml` overrides. The second is the
one-line CLAUDE.md import that makes every session load the digest. The
third is a statusline segment showing `mode/tech_level [@deciding file] · lexicon version · pending proposals`.

## Use

```
/respeak:respeak bluf                 # translate this session's latest outcome
/respeak:respeak eli5 notes/plan.md   # translate a file for a newcomer
```

Or say it: "explain that last change to my manager," "give me the ELI5,"
"make this readable." The skill infers the mode from the audience you name.
Every translation opens with a `📣 respeak · <mode>` line, so you can tell
the translator's voice from the agent's own. The milestone narrative from
the Stop hook carries the same marker.

**Ratifying shorthand**, day to day: the translator writes proposals to
`.claude/respeak/proposals/<term>.yaml`. Review one; if you accept it, move
the entry into `.claude/respeak/lexicon.yaml` with `status: ratified`, then
regenerate the digest so sessions pick it up:

```sh
bash scripts/render-lexicon-digest.sh
```

Both files are ordinary git-tracked YAML, so ratification can ride your
normal code review.

**Turning respeak off for a session.** The manifest declares what the
plugin can do; configuration and these overrides decide what it does right
now. Nothing here edits a file in your project.

```
/respeak:off            # every respeak hook stays quiet this session
/respeak:off gate       # only the style gate
/respeak:on             # back to what the configuration says
/respeak:on gate        # run the gate this session even where it is off
```

The same from the shell, for one launch: `RESPEAK_HOOKS=off claude`, or
`RESPEAK_GATE=off claude` (or `=on`). A session marker outranks the
environment, the environment outranks configuration, and
`respeak-config.sh explain` ends with the override in force. A durable
personal preference belongs in the gitignored
`.claude/respeak/config.local.yaml`; turning the whole plugin off is
`claude plugin disable respeak@respeak`.

**Reporting a bug or asking for a feature:**

```
/respeak:report                         # kind, title, body, one at a time
/respeak:report bug "gate blocks .mdx"  # kind and title preset
```

It files a GitHub issue against this repository with the GitHub CLI. The
body is your text plus an environment footer (plugin version and commit,
Claude Code version, python and PyYAML state, OS). Nothing from your
project is attached unless you pass `--include-content` and confirm each
named file after seeing exactly what would be posted.

Every report gets a privacy pass before you see the final body. Names,
addresses, hosts, home paths, organizations, and anything token-shaped are
replaced with neutral placeholders. You confirm nothing privileged remains
before it posts. Without `gh`, or signed out, it prints the finished body
for you to paste. The skill pre-approves only `gh auth status` and `gh issue create`.

## The knobs

Everything a human should be able to turn lives in
[`config/respeak.config.yaml`](config/respeak.config.yaml), the plugin
defaults that every nearer layer overrides (next section). Tone axes and
tech levels map to the behavior tables in
[`corpus/style/tone-mapping.md`](corpus/style/tone-mapping.md).

- Tone axes: formality, directness, confidence, each with per-band behavior.
- `tech_level` 1–5, plus audience profiles (`exec`, `peer-engineer`,
  `author`) that set lexicon access: `forbidden`, `expand-first-use`, or
  `inline`. Only the `author` profile, level 5, ever sees raw shorthand:
  jargon is licensed by membership, and a reader who ratifies the lexicon is
  a member.
- Per-mode budgets: sentence caps (20 words BLUF, 25 technical, per the
  standards), paragraph caps, metaphor budgets, structure checks like BLUF's
  delete test.
- Shorthand governance covers ratification mode, legibility floor, entry
  cap, minimum edit distance between terms, review cadence, and the
  never-compress classes. It also reserves repair words (`CORRECTION`,
  `SAY-AGAIN`, `UNVERIFIED`) that no one may repurpose.
- Bottom-line-first for existing docs (`editorial_pass`): every in-place
  pass runs a buried-lede test. A reader who stops at the first paragraph
  must know the outcome and whether to keep reading. On failure, `advise`
  mode reports a structure advisory (proposed order plus a drafted lead
  paragraph) without moving a thing. `apply` mode may reorder and retitle,
  for callers who own relinking.
- Data visibility (`data`): four or more homogeneous items render as a
  table, never prose. The decision column leads. The summary or verdict row
  comes before detail rows. Outliers get named in a sentence above the
  table. eli5 is the exception: it states the one comparison the reader
  cares about.

## Where the tone comes from

Tone depends on where the writing lives. An executive brief under
`docs/exec/` and an API note under `docs/api/` in the same repo have
different readers. One person's default across every repo differs from a
project's default for one of them. Respeak resolves its configuration the
way Claude Code resolves settings and CLAUDE.md files: from layers, and the
layer nearest the target wins.

| Layer | File | Typical use |
| --- | --- | --- |
| plugin defaults | `config/respeak.config.yaml` in the plugin | the shipped contract |
| plugin userConfig | `claude plugin install respeak --config default_mode=bluf` | a quick personal default |
| user | `~/.claude/respeak/config.yaml` | your default across every repo, plus profiles you define |
| project | `.claude/respeak/config.yaml` | the project's baseline; the only place the gate turns on |
| project local | `.claude/respeak/config.local.yaml` (gitignored) | your personal override for one repo |
| scopes | `scopes:` entries with `paths:` globs inside any file above, applied right after that file | central, path-keyed overrides, like `.claude/rules` |
| folder | `.respeak.yaml` in any folder from the project root down | a folder's own audience |
| invocation | `/respeak:respeak bluf`, `--mode`, `--set` | this one render |
| session | `/respeak:off`, `/respeak:on [gate]`, `RESPEAK_HOOKS`, `RESPEAK_GATE` | hooks on or off for this session; outranks every file |

A folder file is three lines:

```yaml
# docs/exec/.respeak.yaml
narrative:
  profile: exec        # bluf, tech_level 1, no shorthand
```

Folder and user files may set tone (`narrative`, `modes`, `style` budgets,
`profiles`, `gate.fail_on`, `gate.allow`). They may not enable the gate,
choose which files it covers, or touch shorthand governance. Those keys are
project-only, and they are dropped with a warning anywhere else. So a stray
file in a subfolder cannot switch enforcement on or off for a repo.

Every consumer, the gate hook included, finds the project root the same
way. It looks for the nearest `.claude/respeak/config.yaml` above the file
(a package's own in a monorepo, a parent directory's for every repo below
it). Failing that, it uses the directory Claude Code was launched in, then
the nearest `.git`. The user file under `~/.claude` is never mistaken for a
project file. See what applies to a file, which rule chose the root, and
which layer decided each key:

```sh
bash "${CLAUDE_PLUGIN_ROOT}/scripts/respeak-config.sh" explain --for docs/exec/q3.md
```

The contract, the merge rules, and worked examples are in
[`docs/config-layers.md`](docs/config-layers.md). A runnable example tree
with its outcomes pinned by the test suite is in
[`examples/layered/`](examples/layered/).

## What can go wrong

The design's own risk register
([`research/synthesis/design-principles.md`](research/synthesis/design-principles.md)
§4) puts translator error near the top. The human lane is your window, and
a confident wrong BLUF is worse than shorthand. The mitigations are the
`never_compress` passthrough (error text, quotes, and numbers survive any
rewrite verbatim) and the facts-before-stories and delete-test checks. Two
more mitigations are the `UNVERIFIED` fence for speculation and practice. In
the field test we read the full diff before trusting it, and the verifier
exists so that reading is cheap. Treat translated narratives the way you
treat any report: spot-check against the evidence it cites.

## Status (v0.5.1)

Every surface below works today.

| Surface | State |
|---|---|
| Translator subagent and its three modes (eli5, bluf, technical) | Working |
| Style gates and corpus (banned phrases, replacements, tone mapping) | Working |
| Buried-lede test with structure advisories, plus the data-rendering contract | Working |
| Lexicon proposal flow | Working |
| Skills and agent: `respeak:respeak` (verify-then-relay loop), `/respeak:init`, `/respeak:report`, `/respeak:off` and `/respeak:on` (also `RESPEAK_HOOKS`/`RESPEAK_GATE` env overrides) | Working |
| Hooks: SessionStart lexicon status (projects that ran init), PostToolUse style gate (opt-in; `--fail-on`, budgets, `gate.allow`), Stop milestone-narrative nudge (off by default) | Working |
| Statusline script | Working |
| Measure and verify tools, with bash end-to-end suites and unittest coverage | Working |
| Headless renderer: `respeak-render.sh` wraps `claude -p` | Working |
| Configuration resolver: `respeak-config.sh resolve\|explain\|gate\|validate` (read by every hook, skill, statusline, and the headless renderer; expands audience profiles) | Working |

The config declares governance rules no script checks yet, and two pieces of tooling are still ahead:

- Lexicon entry cap (150 terms)
- Edit-distance check between near-neighbor shorthand (minimum distance 2)
- Usage-based expiry (180 days unused)
- Auto-ratification gate (5 clean uses required)
- Fresh-decoder legibility audits (30-day cadence)
- `respeak compile`: emits the corpus as a Vale style package for CI (already RE2-safe for it)
- A display-only translation hook: plain English on screen, shorthand in the transcript

See CHANGELOG.md for what each version changed and why.

## Layout

```
.claude-plugin/            manifest + marketplace + userConfig
.claude/respeak/           this repo's own respeak layer: the human-lane scope, the lexicon digest
CLAUDE.md                  how a session in this repo writes and checks the docs
agents/respeak.md          the translator (Sonnet, isolated context window)
skills/respeak/            /respeak:respeak — the translation entry point
skills/init/               /respeak:init — per-project setup
skills/off/ skills/on/     /respeak:off and /respeak:on — hooks off or on for this session
skills/report/             /respeak:report — file an issue upstream (gh; privacy by default)
hooks/hooks.json           session-start lexicon status (respeak projects only); optional
                           milestone narrative; opt-in PostToolUse style gate on Write/Edit;
                           all three honor the session overrides
scripts/                   config resolver (respeak-config.py + .sh), measure, verify-edit,
                           gate hook, headless render, statusline, lexicon digest renderer,
                           PyYAML-aware interpreter finder (respeak-python.sh, respeak-py.sh),
                           issue-report environment footer (report-env.sh), session
                           overrides (respeak-override.sh, respeak-session.sh), the CI
                           check over tracked docs (respeak-check.sh)
tests/                     edit-safety + measure/gate + config-layer suites (markdown, code,
                           py, html, yaml, json), bash end-to-end suites for the gate hook,
                           the Stop hook, the statusline, the session overrides, the report
                           footer, and the CI check
config/respeak.config.yaml the influence surface (plugin defaults, lowest layer)
config/project-seed.yaml   the sparse file /respeak:init drops into a project
corpus/                    banned phrases, replacements, lexicon, style maps
docs/architecture.md       the design, with resolved questions
docs/config-layers.md      the layered configuration contract, with examples
examples/layered/          a runnable project tree the config tests pin
research/                  11 source studies, 4 synthesis passes
assets/respeak-icon.svg    the megaphone
CHANGELOG.md               what changed in each version
LICENSE                    MIT
```

The design decisions are argued, with citations, in
[`research/synthesis/design-principles.md`](research/synthesis/design-principles.md):
twelve principles and five named risks. This README was itself edited by
the translator's editorial pass, and every edit was verified
meaning-invariant with `respeak-verify-edit.py`. The bundled scanner reports
zero error and warn hits on it, and every budget passes except the
sentence-length cap, which the scanner trips on wide table rows.

## References

The sources behind each design concept. All were fetched and read during the
research runs (2026-08-31); the eleven distilled source studies live in
[`research/sources/`](research/sources/).

**Why swarms drift into shorthand (linguistics of convention)**

- Clark & Wilkes-Gibbs, *Referring as a collaborative process*: conceptual
  pacts; 40 words become "the skater" in six rounds.
  <https://en.wikipedia.org/wiki/Conceptual_pact>
- Clark & Brennan, grounding and common ground: why the reader's decoding
  effort counts in the cost. <https://en.wikipedia.org/wiki/Grounding_in_communication>
- Pickering & Garrod, interactive alignment: entrainment is automatic, so
  drift needs no decision. <https://en.wikipedia.org/wiki/Interactive_alignment>
- Garrod et al., experimental semiotics: evolved signs go opaque to
  outsiders. <https://en.wikipedia.org/wiki/Experimental_semiotics>
- Zipf's law of abbreviation: frequent forms shorten.
  <https://en.wikipedia.org/wiki/Brevity_law>
- Piantadosi, Tily & Gibson (PNAS 2011): word length tracks information
  content; never compress high-surprisal content.
  <https://www.pnas.org/doi/10.1073/pnas.1012551108>

**Governed shorthand in the wild (the lexicon model)**

- Multiservice tactical brevity codes: the governed-dictionary pattern.
  <https://en.wikipedia.org/wiki/Multiservice_tactical_brevity_code>
- Ham radio Q codes: central ratification and deprecation.
  <https://en.wikipedia.org/wiki/Q_code>
- Medical abbreviation bans: compression rolled back after it caused harm;
  the model for `never_compress`.
  <https://en.wikipedia.org/wiki/List_of_abbreviations_used_in_medical_prescriptions>

**Machine-lane prior art (compression and agent communication)**

- Lewis et al. 2017, the FAIR negotiation agents: "no reward to sticking to
  English"; legibility must be a reward channel.
  <https://arxiv.org/abs/1706.05125>
- Agora protocol (Oxford): frequency-tiered agent communication, the
  lexicon's economics. <https://arxiv.org/abs/2410.11905>
- LLMLingua / LLMLingua-2: per-message statistical compression and its
  legibility cost. <https://github.com/microsoft/LLMLingua>,
  <https://arxiv.org/abs/2310.05736>, <https://arxiv.org/abs/2403.12968>
- TOON: 42.6% fewer tokens than JSON at higher accuracy, under a versioned
  spec; the governance template. <https://github.com/toon-format/toon>
- SynthLang: an evolving glyph lexicon, with no legibility signal.
  <https://github.com/ruvnet/SynthLang>
- DroidSpeak: the sub-linguistic extreme respeak argues against.
  <https://arxiv.org/abs/2411.02820>
- GibberLink: the announced mode-switch precedent.
  <https://github.com/PennyroyalTea/gibberlink>
- Caveman: token-efficiency proxy; "verified savings" as the burden of
  proof. <https://caveman.so/>

**The AI-tell corpus (evidence for the banned phrases)**

- Wikipedia, *Signs of AI writing*: the editor-maintained tell catalog.
  <https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing>
- Kobak et al., excess vocabulary in LLM-era text: effect sizes for `delve`
  and family. <https://arxiv.org/abs/2406.07016>
- AntiSlop sampler: generation-time slop suppression and its phrase corpus.
  <https://github.com/sam-paech/antislop-sampler>

**Style as data (the config and CI path)**

- Vale: styles as versioned YAML packages, the compile target.
  <https://vale.sh/>
- Mailchimp content style guide: voice constant, tone varies by reader
  state. <https://styleguide.mailchimp.com/>
- Google developer documentation style guide.
  <https://developers.google.com/style>
- Diátaxis: document modes keyed to reader need, the analogy for
  eli5/bluf/technical. <https://diataxis.fr/>

**Communication standards (the mode contracts)**

- US federal plain-language guidelines: verbs over nominalizations, reader-
  first structure. <https://www.plainlanguage.gov/guidelines/>
- GOV.UK style guide: "cannot, not can't"; numbered steps for processes.
  <https://www.gov.uk/guidance/style-guide/a-to-z-of-gov-uk-style>
- ASD-STE100 Simplified Technical English: the sentence caps.
  <https://www.asd-ste100.org/>
- BLUF (bottom line up front): answer first, and the delete test.
  <https://en.wikipedia.org/wiki/BLUF_(communication)>
- Barbara Minto, the Pyramid Principle: grouped, MECE, answer-first
  argument. <https://en.wikipedia.org/wiki/Barbara_Minto>
- Radical Candor (Kim Scott): the checkable feedback switches.
  <https://www.radicalcandor.com/blog/what-is-radical-candor/>
- Crucial Conversations: facts before stories; contrasting statements.
  <https://cruciallearning.com/crucial-conversations-book/>

**The substrate (Anthropic engineering + Claude Code)**

- *Writing effective tools for agents*: the ResponseFormat precedent for
  mode parameters.
  <https://www.anthropic.com/engineering/writing-tools-for-agents>
- *Effective context engineering for AI agents*: the attention-budget
  argument for the machine lane.
  <https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents>
- *Effective harnesses for long-running agents*: structured registries
  resist drift; the lexicon's file-format lesson.
  <https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents>
- Claude Code docs (skills, subagents, hooks, plugins): the integration
  surfaces. <https://code.claude.com/docs>

## License

[MIT](LICENSE). Copyright (c) 2026 Kevin Tegtmeier.

Third-party material: the research notes summarize published sources under
their own terms, with links. The catalog of AI-writing tells condensed in
[`research/sources/deai-language-landscape.md`](research/sources/deai-language-landscape.md)
§1 derives from Wikipedia's
["Signs of AI writing"](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)
by Wikipedia contributors (CC BY-SA 4.0); that section is available under
the same license. Some banned-phrase categories were informed by the
[antislop-sampler](https://github.com/sam-paech/antislop-sampler) project
(Apache-2.0); no code or text from it is included.
