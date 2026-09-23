# respeak

<img src="assets/respeak-icon.svg" alt="" width="56" align="left">

Two-lane communication for AI agent swarms in Claude Code: agents talk in
governed shorthand, and every human gets a narrative worth reading.

## The problem

In Clark and Wilkes-Gibbs' experiment, two people describing the same
abstract picture start at about forty words and finish, six rounds later, at
two: "the skater." Garrod's studies measured the cost: outsiders cannot read
the evolved signs, because the meaning lives in the pair's shared history.

Agent swarms do the same. Every token of inter-agent traffic spends context
window, and attention cost grows quadratically with sequence length, so the
pressure to compress is structural. The person supervising the swarm becomes
the outsider. Forcing prose pays the attention tax on every message; letting
the dialect drift gives up auditing your own automation. Facebook's 2017
negotiation bots were pulled back into English by rewarding English, which
gave up the compression.

## What respeak does

Respeak splits the traffic into two lanes and joins them with a feedback
loop. The research found tools that compress (Caveman, LLMLingua), tools
that narrate (PagerDuty Advance, LangSmith Insights), and one protocol with
the right economics (Oxford's Agora), but none that close the loop:
[`research/synthesis/solutions-and-media.md`](/research/synthesis/solutions-and-media.md).

The **machine lane**: agents may use shorthand *ratified* in a lexicon file
and write everything else in full. Nothing intercepts traffic; every session
loads a digest of the lexicon through a CLAUDE.md import. Entries are
proposed, ratified, or retired, never silently edited, as in aviation
phraseology and Q codes. The `never_compress` block keeps error messages,
security findings, user quotes, and numbers with units verbatim, recording
*why*, after medicine's "do not use" abbreviation list.

The **human lane**: a translator subagent renders the work in one of three
modes:

| Mode | Contract |
| --- | --- |
| `eli5` | One idea per sentence, one analogy at most, and the analogy is repaid: the next sentence says the real thing. |
| `bluf` | Sentence one is the result, decision, or ask, with owner and deadline. A manager can forward it unedited. |
| `technical` | Conclusion first, then evidence as `file:line`, then open questions. Technical readers get no fluff; they resent it most. |

Every mode passes the same style gates: 234 banned phrases across 22
categories (AI tells, from `delve` to `load-bearing`), each with a severity;
60 replacement rules; sentence and paragraph budgets from Simplified
Technical English and plain-language standards; tone axes as behavior
tables. A config field with no observable behavior is deleted.

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

## Is an edit safe?

A style edit must be provably meaning-preserving:

```sh
python3 plugin/scripts/respeak-verify-edit.py <before> <after>   # exit 0 = safe
make check                                                # unittest, the bash suites, lint, doclint, hygiene, README freshness
```

| Format | An edit may change | Invariant (checked) |
| --- | --- | --- |
| `.md` | prose | headings, block structure (list items, table rows, quote lines), link and image targets, fenced code, inline code spans, numbers, front matter |
| `.ts .tsx .js .jsx .c .go .java .rs` | comments only | all code and string literals; numbers inside comments |
| `.py` | `#` comments only | code, docstrings, and string literals unless `--allow-strings` |
| `.html` | text nodes | tag skeleton and attributes; `script/style/pre/code` |
| `.yaml .json` | comments / whitespace | parsed data, minus the `--prose-keys` leaves |

`--allow-restructure` downgrades heading and structure changes to warnings
for a caller that owns relinking. `--allow-strings` opens `.py` string
literals for a page generator. `--prose-keys k1,k2` names front-matter or
`.yaml` leaves that hold prose. `--dirs` verifies two rendered trees. The
scanner is local and free:

```sh
python3 plugin/scripts/respeak-measure.py path/to/doc.md
```

## Enforcement

**The gate hook** (`plugin/scripts/respeak-gate.sh`) is a `PostToolUse` hook on
`Write|Edit` (`plugin/hooks/hooks.json`). It measures each Markdown file a tool
call wrote and blocks a failing report with exit code 2, which Claude Code
returns to the model as a correctable error. Setup problems never block.
It is **opt-in per project**: only the project layer sets `gate.enabled: true`.
`gate.block_on: introduced` blocks only on hits the write added;
`block_on: any` judges the whole file.

```yaml
gate:
  enabled: true
  include: ["**/*.md"]     # globs, relative to the project dir
  exclude: ["research/**"] # never gated
  fail_on: error            # none | warn | error
  block_on: introduced      # introduced | any — which hits are this write's business
  allow: []                 # regexes — see "Exceptions and allow" below
```

**The scanner** counts prose only: code, blockquotes, front matter, HTML
comments, and URLs are dropped, and each list item or table row is its own
unit. `--fail-on {none,error,warn}` sets the exit; `--baseline BASE` reports
`[new N, pre-existing M]` per rule; `--config` carries the project's
`style.budgets` and `gate.allow`.

**Exceptions and allow.** A corpus entry's `exceptions:` regexes ship with
the corpus (the `the spine` rule exempts `spine switch`); `gate.allow` skips
a rule for one project, as a stopgap.

**Verify-then-relay.** The `respeak:respeak` skill gates the agent's output
and sends failures back for up to 2 rewrites. `plugin/scripts/respeak-render.sh`
runs the same loop headless over `claude -p`:

```sh
plugin/scripts/respeak-render.sh --mode technical \
  --source notes/draft.md --out docs/guide/03-lesson.md --max-rounds 2
```

**CI.** `plugin/scripts/respeak-check.sh` runs the hook over every Markdown file
git knows about; `--verify <ref>` also proves each edit since the ref
meaning-invariant.

```sh
bash plugin/scripts/respeak-check.sh --verify origin/main   # exit 1 on a block or a changed invariant
```

**Upgrading**: the installed copy under `~/.claude/plugins/cache` is a
snapshot; run `claude plugin update respeak` after pulling a change.

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
segment.

## Use

```
/respeak:respeak bluf                 # translate this session's latest outcome
/respeak:respeak eli5 notes/plan.md   # translate a file for a newcomer
```

Or say it: "explain that last change to my manager." Every translation
opens with a `📣 respeak · <mode>` line.

**Ratifying shorthand**: proposals land in
`.claude/respeak/proposals/<term>.yaml`. To accept one, move it into
`.claude/respeak/lexicon.yaml` with `status: ratified` and regenerate the
digest:

```sh
bash plugin/scripts/render-lexicon-digest.sh
```

**Turning respeak off for a session.** Nothing edits a project file.

```
/respeak:off            # every respeak hook stays quiet this session
/respeak:off gate       # only the style gate
/respeak:on             # back to what the configuration says
/respeak:on gate        # run the gate this session even where it is off
```

For one launch: `RESPEAK_HOOKS=off claude` or `RESPEAK_GATE=off claude`.
Disabling the plugin is `claude plugin disable respeak@claude-code-respeak`.

**Reporting a bug or asking for a feature:**

```
/respeak:report                         # kind, title, body, one at a time
/respeak:report bug "gate blocks .mdx"  # kind and title preset
```

It files a GitHub issue with `gh`, with an environment footer and a privacy
pass you confirm; project files attach only with `--include-content`.

## The knobs

Everything a human can turn lives in
[`plugin/config/respeak.config.yaml`](/plugin/config/respeak.config.yaml); tone axes and
tech levels map to the behavior tables in
[`plugin/corpus/style/tone-mapping.md`](/plugin/corpus/style/tone-mapping.md).

- Tone axes: formality, directness, confidence.
- `tech_level` 1–5, plus audience profiles (`exec`, `peer-engineer`,
  `author`) that set lexicon access; only `author`, level 5, sees raw shorthand.
- Per-mode budgets: sentence caps (20 words BLUF, 25 technical), paragraph
  and metaphor caps.
- Shorthand governance: ratification, entry cap, edit distance, review
  cadence, and repair words (`CORRECTION`, `SAY-AGAIN`, `UNVERIFIED`).
- `editorial_pass`: a buried-lede test on every in-place pass.
- `data`: four or more homogeneous items render as a table.

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

A folder file:

```yaml
# docs/exec/.respeak.yaml
narrative:
  profile: exec        # bluf, tech_level 1, no shorthand
```

Folder, user, and provider layers set tone only; gate enablement and
shorthand governance are project-only. `explain` shows the project root,
the provider, and which layer decided each key:

```sh
bash "${CLAUDE_PLUGIN_ROOT}/scripts/respeak-config.sh" explain --for docs/exec/q3.md
```

The contract and worked examples: [`plugin/docs/config-layers.md`](/plugin/docs/config-layers.md);
a runnable tree: [`examples/layered/`](/examples/layered/).

## What can go wrong

The risk register
([`research/synthesis/design-principles.md`](/research/synthesis/design-principles.md)
§4) ranks translator error high: a confident wrong BLUF is worse than
shorthand. `never_compress`, the `UNVERIFIED` fence, and the verifier limit
it; spot-check a narrative against the evidence it cites.

## Status (v0.6.1)

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
Makefile                   make check, make readme, make doctor
plugin/                    the plugin, self-contained: what an install copies
plugin/.claude-plugin/     manifest + userConfig
plugin/agents/respeak.md   the translator
plugin/skills/             respeak, init, off, on, report
plugin/hooks/hooks.json    lexicon status, milestone narrative, style gate
plugin/scripts/            resolver, measure, verify-edit, gate, render, check, doctor
plugin/config/             plugin defaults and the /respeak:init seed
plugin/corpus/             banned phrases, replacements, lexicon, style maps
plugin/docs/               the configuration contract
scripts/readme-fresh.sh    the README freshness check
scripts/hygiene            the name and path lint
scripts/doclint            charters, packets, and relative links
tests/                     unittest and bash suites
design/                    the README's source and the build packets
docs/                      architecture
examples/layered/          a runnable tree the config tests pin
history/sittings/          one charter per working session
research/                  11 source studies, 4 synthesis passes
```

The design is argued in
[`research/synthesis/design-principles.md`](/research/synthesis/design-principles.md):
twelve principles and five named risks. `make readme` renders this README
from `design/readme/source.md` in technical mode; `make check` refuses a
README older than its source.

## References

The sources behind each design concept. All were fetched and read during the
research runs (2026-08-31); the eleven distilled source studies live in
[`research/sources/`](/research/sources/).

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

[MIT](/LICENSE). Copyright (c) 2026 Kevin Tegtmeier.

Third-party material: the research notes summarize published sources under
their own terms, with links. The catalog of AI-writing tells condensed in
[`research/sources/deai-language-landscape.md`](/research/sources/deai-language-landscape.md)
§1 derives from Wikipedia's
["Signs of AI writing"](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)
by Wikipedia contributors (CC BY-SA 4.0); that section is available under
the same license. Some banned-phrase categories were informed by the
[antislop-sampler](https://github.com/sam-paech/antislop-sampler) project
(Apache-2.0); no code or text from it is included.
