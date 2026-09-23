# respeak

<img src="assets/icon.svg" alt="" width="56" align="left">

respeak is a Claude Code plugin for two-lane communication in agent swarms.
Agents write to each other in governed shorthand, and every person gets a
narrative written for them.

## Why it exists

A household runs several Claude Code plugins in unattended relay runs, where
one session hands its work to the next. Agents that write to each other
spend context on every token, so the pressure to compress is structural.
They drift into shorthand, and the person supervising the run becomes the
outsider.

Two people describing the same abstract picture start at about forty words
and finish, six rounds later, at two ("the skater"). Outsiders cannot read
the evolved signs, because the meaning lives in the pair's shared history.
Forcing prose on agents pays the attention cost on every message. Letting
the dialect drift gives up auditing your own automation.

respeak takes both lanes. Agents use ratified shorthand to spend less
context, and every person reads a narrative in their own mode. A feedback
loop joins the lanes, and a style gate holds the human lane to its rules.

## What respeak does

The **machine lane**: agents may use shorthand *ratified* in a lexicon file
and write everything else in full. Nothing intercepts traffic; every session
loads a digest of the lexicon through a CLAUDE.md import. Entries are
proposed, ratified, or retired, never silently edited, as in aviation
phraseology and Q codes. The `never_compress` block keeps error messages,
security findings, user quotes, and numbers with units verbatim.

The **human lane**: a translator subagent renders the work in one of three
modes:

| Mode | Contract |
| --- | --- |
| `eli5` | One idea per sentence, one analogy at most, and the analogy is repaid: the next sentence says the real thing. |
| `bluf` | Sentence one is the result, decision, or ask, with owner and deadline. A manager can forward it unedited. |
| `technical` | Conclusion first, then evidence as `file:line`, then open questions. Technical readers get no fluff; they resent it most. |

Every mode passes the same style gates. There are 234 banned phrases across
22 categories (AI tells, from `delve` to `load-bearing`), each with a
severity, and 60 replacement rules. Sentence and paragraph budgets come
from Simplified Technical English and plain-language standards. Tone axes are behavior
tables, and a config field with no observable behavior is deleted.

The **loop**: while translating, the agent files proposals for unratified
shorthand it had to decode, preferring the variant closest to plain English.
A human ratifies, and the dialect drifts toward needing less translation.

## Does it work?

One field test (2026-08-31, n=1): a technical-mode editorial pass over a
4,000-word internal design document. Treat the numbers as sizing evidence,
not a benchmark.

| Metric | Before | After |
| --- | --- | --- |
| Banned phrases (error severity) | 3 | 0 |
| Banned phrases (warn severity) | 9 | 1 (a deliberate, documented keep) |
| Em-dashes per 1000 words | 19.9 | 3.1 |
| Average sentence length | 32.1 words | 24.5 words |
| Headings, links, code, numbers changed | n/a | zero (`respeak-verify-edit.py` passes) |

The pass kept "a genuine platform gap" because the corpus bans `genuinely`,
not `genuine`.

## Install

Prerequisites: Claude Code ≥ 2.1.196, a plugin path without spaces, bash
3.2 or newer, and a python3 (3.9 or newer) with PyYAML; `/respeak:report`
also needs `gh`. The scripts pick the first interpreter that imports PyYAML
(override with `RESPEAK_PYTHON`). The translator runs as a Sonnet subagent
in its own context window, so the swarm's context never pays for it.

Install from GitHub (these write to your `~/.claude` config):

```sh
claude plugin marketplace add kevinteg/claude-code-respeak
claude plugin install respeak@claude-code-respeak
# optionally: --config default_mode=bluf --config tech_level=2
```

The marketplace was named `respeak` before 0.6.1. If you added it under
that name, remove it, then add and install again:

```sh
claude plugin marketplace remove respeak
claude plugin marketplace add kevinteg/claude-code-respeak
claude plugin install respeak@claude-code-respeak
```

From a checkout, `make install` adds the marketplace when it is absent and
updates it when it already points at the checkout. It never removes a
registration from another source; it prints the two commands instead and
exits 2. `make doctor` prints one line per check: python, claude,
marketplace, plugin, provider, config.

```sh
make install
make doctor
```

To try it for one session from a checkout, changing nothing persistent:

```sh
git clone https://github.com/kevinteg/claude-code-respeak "$RESPEAK_SRC"
claude --plugin-dir "$RESPEAK_SRC/plugin"
```

Translation works at once. The lexicon, the gate, and a project baseline
need a one-time setup per project:

```
/respeak:init
```

It creates `.claude/respeak/`, generates the lexicon digest, and offers the
CLAUDE.md import, gitignore entries for `*.local.yaml`, and a statusline
segment. After pulling a change, run `claude plugin update respeak`: the
installed copy under `~/.claude/plugins/cache` is a snapshot.

## Commands and skills

| Command | What it does |
| --- | --- |
| `/respeak:respeak` | Translate the session's latest outcome or a file into `eli5`, `bluf`, or `technical`. |
| `/respeak:init` | Set up the project: state dirs, a sparse config, the lexicon and its digest. |
| `/respeak:off` | Silence the respeak hooks for this session; with `gate`, only the style gate. |
| `/respeak:on` | Undo `/respeak:off`; with `gate`, run the gate this session even where it is off. |
| `/respeak:report` | File a bug, feature request, documentation note, or question on GitHub. |
| `respeak:respeak` agent | The translator subagent the skill and natural-language asks reach. |

```
/respeak:respeak bluf                   # translate this session's latest outcome
/respeak:respeak eli5 notes/plan.md     # translate a file for a newcomer
/respeak:init                           # one-time project setup
/respeak:off gate                       # only the style gate goes quiet
/respeak:on gate                        # trial the gate for this session
/respeak:report bug "gate blocks .mdx"  # kind and title preset
```

Or say it: "explain that last change to my manager." Every translation
opens with a `📣 respeak · <mode>` line. For one launch,
`RESPEAK_HOOKS=off claude` or `RESPEAK_GATE=off claude` does what
`/respeak:off` does. `/respeak:report` files the issue with `gh`, with an
environment footer and a privacy pass you confirm; project files attach
only with `--include-content`.

The scripts a reader runs, all under `plugin/scripts/`:

```sh
python3 plugin/scripts/respeak-measure.py path/to/doc.md           # the scanner, local and free
python3 plugin/scripts/respeak-verify-edit.py <before> <after>     # exit 0 = the edit changed only prose
bash plugin/scripts/respeak-check.sh --verify origin/main          # the gate over every doc, as CI runs it
bash plugin/scripts/respeak-config.sh explain --for docs/exec/q3.md
bash plugin/scripts/render-lexicon-digest.sh                       # after ratifying a proposal
```

`respeak-verify-edit.py` proves a style edit meaning-preserving. In `.md`
it holds headings, block structure, link and image targets, fenced code,
inline code, numbers, and front matter byte-identical. In code files it
opens comments only. Proposals land in
`.claude/respeak/proposals/<term>.yaml`. To accept one, move it into
`.claude/respeak/lexicon.yaml` with `status: ratified` and regenerate the
digest.

## Enforcement

**The gate hook** (`plugin/scripts/respeak-gate.sh`) is a `PostToolUse`
hook on `Write|Edit` (`plugin/hooks/hooks.json`). It measures each Markdown
file a tool call wrote and blocks a failing report with exit code 2, which
Claude Code returns to the model as a correctable error. Setup problems
never block. It is **opt-in per project**: only the project layer sets
`gate.enabled: true`. `gate.block_on: introduced` blocks only on hits the
write added; `block_on: any` judges the whole file.

```yaml
gate:
  enabled: true
  include: ["**/*.md"]     # globs, relative to the project dir
  exclude: ["research/**"] # never gated
  fail_on: error            # none | warn | error
  block_on: introduced      # introduced | any — which hits are this write's business
  allow: []                 # regexes that skip a rule for this project
```

**The scanner** counts prose only: code, blockquotes, front matter, HTML
comments, and URLs are dropped, and each list item or table row is its own
unit. `--fail-on {none,error,warn}` sets the exit; `--baseline BASE`
reports `[new N, pre-existing M]` per rule; `--config` carries the
project's `style.budgets` and `gate.allow`.

**CI.** `plugin/scripts/respeak-check.sh` runs the gate over every Markdown
file git knows about, from the committed configuration only. `--verify
<ref>` also proves each edit since the ref meaning-invariant, and a block
or a changed invariant exits 1.

## Where the tone comes from

Configuration resolves from layers, and the layer nearest the target wins:

| Layer | File | Typical use |
| --- | --- | --- |
| plugin defaults | `config/respeak.config.yaml` in the plugin | the shipped contract |
| plugin userConfig | `claude plugin install respeak --config default_mode=bluf` | a quick personal default |
| user | `~/.claude/respeak/config.yaml` | your default across every repo |
| project | `.claude/respeak/config.yaml` | the project's baseline; the only place the gate turns on |
| project local | `.claude/respeak/config.local.yaml` (gitignored) | your override for one repo |
| scopes | `scopes:` entries with `paths:` globs, applied right after their file | path-keyed overrides |
| folder | `.respeak.yaml` in any folder from the project root down | a folder's own audience |
| provider | the `respeak` section of `claude-code-session`'s resolved file (major 2) | the session's tone; optional |
| invocation | `/respeak:respeak bluf`, `--mode`, `--set` | this one render |
| session | `/respeak:off`, `/respeak:on [gate]`, `RESPEAK_HOOKS`, `RESPEAK_GATE` | hooks on or off for this session |

Folder, user, and provider layers set tone only; gate enablement and
shorthand governance are project-only. The knobs are tone axes
(formality, directness, confidence), `tech_level` 1–5 with audience
profiles, per-mode sentence budgets, and shorthand governance. They live in
[`plugin/config/respeak.config.yaml`](/plugin/config/respeak.config.yaml).
The contract and worked examples: [`plugin/docs/config-layers.md`](/plugin/docs/config-layers.md);
a runnable tree: [`examples/layered/`](/examples/layered/).

## Design of record

- [`docs/architecture.md`](/docs/architecture.md): the two lanes, the
  lexicon, the translator, and the influence model.
- [`research/synthesis/design-principles.md`](/research/synthesis/design-principles.md):
  twelve principles and five named risks.
- `design/packets/`: one build packet per change, with its rulings and
  acceptance lines.
- `history/sittings/`: one charter per working session; each handover
  records the choices made inside the design and who consumes them.
- [`docs/references.md`](/docs/references.md): the published sources
  behind each design concept.

## Tests

Each file runs alone in seconds:

| File | What it pins |
| --- | --- |
| `tests/test_measure_gate.py` | the scanner and its budgets |
| `tests/test_corpus.py` | the shipped banned-phrase rules |
| `tests/test_verify_edit.py` | the edit-safety invariants, per format |
| `tests/test_config_layers.py` | the layered configuration resolver |
| `tests/test_provider_layer.py` | the session provider layer |
| `tests/test_readme.py` | this README: the status line, the icon, the size, no sibling path |
| `tests/test_gate_hook.sh` | the gate hook under the resolver |
| `tests/test_hooks.sh` | the narrative nudge and the statusline |
| `tests/test_overrides.sh` | `/respeak:off`, `/respeak:on` and the environment overrides |
| `tests/test_check.sh` | `respeak-check.sh` and its `--verify` |
| `tests/test_render.sh` | the bounded spawns, the renderer's breakers, the README render |
| `tests/test_readme_fresh.sh` | every freshness verdict |
| `tests/test_doctor.sh` | the six doctor lines |
| `tests/test_install.sh` | `make install`: add, update, refuse |
| `tests/test_report_env.sh` | the report target and its footer |
| `tests/test_bounded.sh` | the wall, the lock and the exit of `scripts/bounded` |

```sh
python3 -m unittest tests.test_verify_edit
bash tests/test_render.sh
make check
```

`make check` runs `test`, `lint`, `doclint`, `hygiene`, `readme-fresh` and
`validate` under `scripts/bounded`: one run per tree, a 900 s wall, held
off above load 4 x cores.

## Conventions shared with the sibling plugins

respeak is one of several plugins built to the same conventions.
`scripts/hygiene` (the name and path lint) and `scripts/doclint` (charters,
packets, links) are byte-identical across them, pinned by hash in the
Makefile. Each README is rendered from its source, and the sidecar
`design/readme/rendered.sha256` holds the two hashes `make check` reads.
The one sibling respeak reads is `claude-code-session`, major 2, as the
optional provider of the session's tone. Nothing breaks without it.

## What can go wrong

The risk register
([`research/synthesis/design-principles.md`](/research/synthesis/design-principles.md)
§4) ranks translator error high: a confident wrong BLUF is worse than
shorthand. `never_compress`, the `UNVERIFIED` fence, and the verifier limit
it; spot-check a narrative against the evidence it cites. The gate is
opt-in, so a project that never turns it on gets no enforcement. A
proposal is only a proposal until a human ratifies it.

## Status

Status: version `0.6.1`, rendered `2026-09-23`, `227` unittest cases and `10` bash suites.

| Surface | State |
|---|---|
| Translator subagent, three modes | Working |
| Style gates and corpus | Working |
| Buried-lede test and data-rendering contract | Working |
| Lexicon proposal flow | Working |
| Skills: `respeak:respeak`, `/respeak:init`, `/respeak:report`, `/respeak:off`, `/respeak:on` | Working |
| Hooks: SessionStart lexicon status, PostToolUse style gate (opt-in), Stop narrative nudge (off by default) | Working |
| Statusline script | Working |
| Measure and verify tools, with their suites | Working |
| Headless renderer: `respeak-render.sh` wraps `claude -p` | Working |
| Configuration resolver: `respeak-config.sh resolve\|explain\|gate\|validate` | Working |

Declared, not yet checked or built:

- Lexicon entry cap (150 terms)
- Edit-distance check between near-neighbor shorthand (minimum distance 2)
- Usage-based expiry (180 days unused)
- Auto-ratification gate (5 clean uses required)
- Fresh-decoder legibility audits (30-day cadence)
- `respeak compile`: the corpus as a Vale style package
- A display-only translation hook

See CHANGELOG.md for what each version changed and why.

## Layout

```
.claude-plugin/            the marketplace: its one plugin is ./plugin
.claude/respeak/           this repo's respeak layer: the human-lane scope, the lexicon digest
.hygiene-allow             the names scripts/hygiene permits, per path
.python-version            the pyenv virtualenv the checks run under (3.12, PyYAML)
CLAUDE.md                  how a session in this repo writes and checks the docs
Makefile                   make check, make readme, make doctor, make install
assets/icon.svg            the project icon
plugin/                    the plugin, self-contained: what an install copies
plugin/.claude-plugin/     manifest + userConfig
plugin/agents/respeak.md   the translator
plugin/skills/             respeak, init, off, on, report
plugin/hooks/hooks.json    lexicon status, milestone narrative, style gate
plugin/scripts/            resolver, measure, verify-edit, gate, render, check, doctor
plugin/config/             plugin defaults and the /respeak:init seed
plugin/corpus/             banned phrases, replacements, lexicon, style maps
plugin/docs/               the configuration contract
scripts/readme-render.sh   make readme: the status line, the render, the stamp
scripts/readme-fresh.sh    the README freshness check
scripts/hygiene            the name and path lint
scripts/doclint            charters, packets, and relative links
scripts/bounded            the wall, lock and load breaker make check runs under
tests/                     unittest and bash suites
design/                    the README's source and the build packets
docs/                      architecture and references
examples/layered/          a runnable tree the config tests pin
history/sittings/          one charter per working session
research/                  11 source studies, 4 synthesis passes
```

`make readme` renders this README from `design/readme/source.md` in
technical mode; `make check` refuses a README older than its source.

## License

[MIT](/LICENSE). Copyright (c) 2026 Kevin Tegtmeier.

Third-party material: the research notes summarize published sources under
their own terms, with links. The catalog of AI-writing tells condensed in
[`research/sources/deai-language-landscape.md`](/research/sources/deai-language-landscape.md)
§1 derives from Wikipedia's
["Signs of AI writing"](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)
by Wikipedia contributors (CC BY-SA 4.0). That section is available under
the same license. Some banned-phrase categories were informed by the
[antislop-sampler](https://github.com/sam-paech/antislop-sampler) project
(Apache-2.0); no code or text from it is included.
