# respeak

Two-lane communication for AI agent swarms in Claude Code: let the agents
talk in governed shorthand, and give every human a narrative worth reading.

## The problem

Put two people in a room and have them describe the same abstract picture to
each other, over and over. In Clark and Wilkes-Gibbs' classic experiment they
start at about forty words ("the one that looks like a person kneeling with
an arm out...") and finish, six rounds later, at two: "the skater." That
compression is automatic and useful. A follow-on line of research (Garrod's
graphical-convention studies) measured its cost: outsiders shown the evolved
signs struggle to interpret them, because the meaning has moved out of the
signs and into the pair's shared history.

Agent swarms do the same thing. A long-running session develops
abbreviations, back-references, and codewords, because every token of
inter-agent traffic is taxed twice: it spends context window, and attention
cost grows quadratically with sequence length. Compression pressure is
structural. Left alone, the swarm's dialect gets cheaper for the agents and
more alien to you, and the person supervising the work becomes the outsider
in that experiment, permanently.

Today you get two bad choices. Force the agents to write prose, and you pay
the attention tax on every message, forever. Let the dialect drift, and you
lose the ability to audit your own automation. When Facebook's 2017
negotiation bots drifted out of English, the researchers' fix was to reward
staying in English, which restored legibility by giving up the compression.

## What respeak does

Respeak splits the traffic instead of compromising one channel, and connects
the two lanes with a feedback loop. Our research pass found tools that
compress (Caveman, LLMLingua), tools that narrate (PagerDuty Advance,
LangSmith Insights), and one protocol with the right economics (Oxford's
Agora); it found none that close this loop. The full landscape review is in
[`research/synthesis/solutions-and-media.md`](research/synthesis/solutions-and-media.md).

The **machine lane** stays efficient. Agents may use any shorthand that is
*ratified* in a lexicon file; everything else gets written out in full. To be
clear about the mechanism: nothing intercepts agent traffic. The lane works
by convention plus context: every session loads a digest of the ratified
lexicon (via a CLAUDE.md import you accept at setup), and a session-start
hook states the lexicon version as fact. The governance model comes from the
shorthand systems that survived a century of expert use: aviation
phraseology, brevity codes, Q codes. Entries are proposed, ratified, or
retired, never silently edited. Some content may never be compressed at
all — error messages, security findings, user quotes, numbers with units.
Medicine keeps a "do not use" abbreviation list because compression harmed
patients; the `never_compress` config block copies that pattern, including
recording *why* each class is banned.

The **human lane** reads well. A translator subagent renders the swarm's work
as a narrative in one of three modes:

| Mode | Contract |
| --- | --- |
| `eli5` | One idea per sentence, one analogy at most, and the analogy is repaid: the next sentence says the real thing. |
| `bluf` | Sentence one is the result, decision, or ask, with owner and deadline. A manager can forward it unedited. |
| `technical` | Conclusion first, then evidence as `file:line`, then open questions. Technical readers get no fluff; they resent it most. |

Every mode passes the same style gates: 234 banned phrases across 22
categories (the catalog of AI tells, from `delve` to `load-bearing`, each
with severity, and marked `owner-preference` where an entry rests on taste
rather than research), 60 replacement rules, sentence and paragraph budgets
taken from Simplified Technical English and federal plain-language standards,
and tone axes documented as behavior tables. The config's standing rule: a
field that maps to no observable behavior gets deleted — the `warmth` axis
already died this way and was replaced by Radical Candor's three checkable
switches.

The **loop** is where the two lanes meet. While translating, the agent
tallies unratified shorthand it had to decode and files proposal entries,
preferring whichever variant of a convention reads closest to plain English.
A human ratifies. Over a long session the swarm's dialect drifts toward
needing less translation, because the librarian keeps nudging it there.
Nobody fights the optimization, and nobody gets locked out of it.

## Does it work?

One field test so far (2026-08-31, n=1, our own doc — sizing evidence, not a
benchmark): the translator ran a technical-mode editorial pass over a real
4,000-word design doc from our wiki. The before/after pair, both measurement
outputs, and reproduce-it-yourself commands are checked in at
[`research/pilot/`](research/pilot/).

| Metric | Before | After |
| --- | --- | --- |
| Banned phrases (error severity) | 3 | 0 |
| Banned phrases (warn severity) | 9 | 1 (a deliberate, documented keep) |
| Em-dashes per 1000 words | 19.9 | 3.1 |
| Average sentence length | 32.1 words | 24.5 words |
| Headings, links, code, numbers changed | n/a | zero (`respeak-verify-edit.py` passes) |

The part worth reading the diff for was judgment: the pass kept "a genuine
platform gap" because the corpus bans `genuinely`, not `genuine`; kept the
author's own contract wording that merely resembled a banned pattern; and
kept table-cell dashes that carry real value breaks. The edited page also
still builds and renders correctly under mkdocs.

## Is an edit safe?

Style edits to real files must be provably meaning-preserving, so the repo
ships a format-aware verifier and a test suite for it:

```sh
python3 scripts/respeak-verify-edit.py <before> <after>   # exit 0 = safe
python3 -m unittest discover tests                        # 45 cases (edit-safety + measure/gate)
bash tests/test_gate_hook.sh                                # gate hook end-to-end (bash, not unittest)
```

| Format | An edit may change | Invariant (checked) |
| --- | --- | --- |
| `.md` | prose | headings/anchors, link and image targets, fenced code, inline code spans, numbers, front matter, admonition types |
| `.ts .tsx .js .jsx .c .go .java .rs` | comments only | all code and string literals byte-identical; numbers even inside comments |
| `.py` | `#` comments only | code and docstrings (docstrings can carry doctests) |
| `.html` | text nodes | tag skeleton and attributes; `script/style/pre/code` byte-identical |
| `.yaml .json` | comments / whitespace | parsed data, deep equality |

For passes allowed to restructure (`editorial_pass: restructure: apply`, when
the caller owns relinking, as in a whole-wiki run), `--allow-restructure`
downgrades heading, admonition-type, and front-matter changes to reported
warnings; link targets, code, and numbers stay hard failures.

The scanner that produced the pilot numbers is also local and free:

```sh
python3 scripts/respeak-measure.py path/to/doc.md
```

## Enforcement

The pilot above measured after the fact. In practice every style gate was
still a prose instruction to the model, and nothing ran the scanner against
what actually shipped: 14 rendered pages went out with 7 hits of the
owner-banned phrase `load-bearing`, other error- and warn-severity hits, and
15–29 em-dashes per 1000 words. Separately, the owner-banned "the spine"
metaphor rule false-positived on literal networking prose ("spine
switches"), because the corpus had no exceptions for the literal sense —
and the banned term was present in the *source* brief, so it propagated
into every page rendered from it. This section closes both gaps.

**The gate hook** (`scripts/respeak-gate.sh`) is a `PostToolUse` hook on
`Write|Edit` (`hooks/hooks.json`) that runs `respeak-measure.py` against any
`.md` file a tool call just wrote, and blocks the tool result (exit 2,
report on stderr — Claude Code feeds that back to the model as a correctable
error) on a failing report. It is **opt-in per project**: it does nothing
unless `<project>/.claude/respeak/config.yaml` exists and sets `gate.enabled:
true`. Configure it there:

```yaml
gate:
  enabled: true
  include: ["**/*.md"]     # globs, relative to the project dir
  exclude: ["research/**"] # never gated
  fail_on: error            # none | warn | error
  allow: []                 # regexes — see "Exceptions and allow" below
```

**`--fail-on`**: `respeak-measure.py --fail-on {none,error,warn}`. `none`
(default) only reports — the pre-enforcement behavior. `error` exits 1 if
any document has a banned-phrase error hit. `warn` also trips on
warn-severity hits, density-tier hits, or a budget failure. Exit 2 is
reserved for usage/IO errors. `--json` now emits a list, one entry per
document, so one call can gate a whole tree:

```sh
python3 scripts/respeak-measure.py wiki/**/*.md --fail-on error
```

**Budgets** (`style.budgets` in `respeak.config.yaml`, read via
`--config`): `emdash_per_1000_words`, `warn_phrases_per_1000_words` (checked
against the corpus's `tier: density` hits — the common-but-excess words that
flag on density, not per occurrence), `avg_sentence_words`,
`max_sentence_words`. Each is measured and reported PASS/FAIL; a FAIL counts
as a warn-level hit for `--fail-on`.

**Exceptions and allow** are two escape hatches at different scopes. A
corpus entry's own `exceptions:` (list of regexes) is scoped to that rule
and ships with the corpus — this is the actual fix for the "spine switches"
false positive: the owner-banned `the spine` metaphor rule now exempts
literal networking senses (`spine switch`, `leaf-spine`, `spine1`, `spine
ASN`, a spine peering/draining/reflecting, …), so a networking-heavy doc
keeps the metaphor ban without losing the literal term. `gate.allow`
(project config) is scoped to one project — it skips a rule entirely for
that project's runs, for a domain term the shared `exceptions:` list doesn't
cover yet. Treat `allow` as a stopgap: file the missing exception upstream
rather than leaving a project-local silence as the permanent fix.

**Verify-then-relay** closes the input-side gap. The `respeak:respeak` skill
no longer relays a rendered narrative on trust: it writes the agent's output
to a temp file, runs `respeak-measure.py --fail-on error` against it, and on
failure sends the report back to the agent for a rewrite — up to 2 rounds —
before relaying. The `respeak:respeak` agent itself now runs an **input
gate** first: it scans the source material for owner-banned terms before
rendering, so a banned term in a brief cannot propagate into the output even
when asked to preserve the source's wording; a passing render reports `gate:
N banned terms removed from source` when it removed any.

**Headless rendering** (`scripts/respeak-render.sh`) runs the same
verify-then-relay loop for the API lane, where there is no interactive skill
to do it — CI, or a swarm's own automation. It wraps `claude-api-agent` (not
part of this plugin — install it separately), builds the system prompt from
`agents/respeak.md`, and gates + retries the same way the skill does:

```sh
scripts/respeak-render.sh --mode technical \
  --source notes/draft.md --out wiki/learning/path/03-lesson.md \
  --max-rounds 2 --budget-usd 1.50
```

**CI usage** — gate a whole tree after a render step, failing the build on
any error-severity hit:

```sh
python3 scripts/respeak-measure.py wiki/**/*.md --fail-on error \
  --config .claude/respeak/config.yaml || exit 1
```

**Upgrading**: the installed copy under `~/.claude/plugins/cache` is a
snapshot, not a live link — after pulling a change here (corpus, gate hook,
or manifest), run `claude plugin update respeak` (or reinstall) so the
`PostToolUse` gate hook and corpus edits actually load.

## Install

Prerequisites: Claude Code ≥ 2.1, bash, python3; the measure/verify scripts
want PyYAML. The translator runs as a Sonnet subagent in its own context
window, so each translation costs one subagent invocation proportional to the
source material — the swarm's context never pays for wordsmithing.

Try it in one session, in any repository (the flag itself changes nothing
persistent; project files appear only if you later run init):

```sh
claude --plugin-dir ~/code/claude-code-respeak
```

Install it for every session (these write to your `~/.claude` config):

```sh
claude plugin marketplace add ~/code/claude-code-respeak
claude plugin install respeak@respeak
# optionally: --config default_mode=bluf --config tech_level=2
```

Then set up each project once:

```
/respeak:init
```

This creates `.claude/respeak/` (project-local config, lexicon, proposals),
generates the ratified-lexicon digest, and offers — never forces — two
integrations: the one-line CLAUDE.md import that makes every session load the
digest, and a statusline segment showing `mode · lexicon version · pending
proposals`.

## Use

```
/respeak:respeak bluf                 # translate this session's latest outcome
/respeak:respeak eli5 notes/plan.md   # translate a file for a newcomer
```

Or say it: "explain that last change to my manager," "give me the ELI5,"
"make this readable." The skill infers the mode from the audience you name.

**Ratifying shorthand**, day to day: the translator writes proposals to
`.claude/respeak/proposals/<term>.yaml`. Review one; if you accept it, move
the entry into `.claude/respeak/lexicon.yaml` with `status: ratified`, then
regenerate the digest so sessions pick it up:

```sh
bash scripts/render-lexicon-digest.sh
```

Both files are ordinary git-tracked YAML, so ratification can ride your
normal code review.

## The knobs

Everything a human should be able to turn lives in
[`config/respeak.config.yaml`](config/respeak.config.yaml); tone axes and
tech levels map to the behavior tables in
[`corpus/style/tone-mapping.md`](corpus/style/tone-mapping.md).

- Tone axes: formality, directness, confidence, each with per-band behavior.
- `tech_level` 1–5, plus audience profiles (`exec`, `peer-engineer`,
  `author`) that set lexicon access: `forbidden`, `expand-first-use`, or
  `inline`. Only the `author` profile, level 5, ever sees raw shorthand,
  because jargon is licensed by membership, and a reader who ratifies the
  lexicon is a member.
- Per-mode budgets: sentence caps (20 words BLUF, 25 technical, per the
  standards), paragraph caps, metaphor budgets, structure checks like BLUF's
  delete test.
- Shorthand governance: ratification mode, legibility floor, entry cap,
  minimum edit distance between terms, review cadence, the never-compress
  classes, and reserved repair words (`CORRECTION`, `SAY-AGAIN`,
  `UNVERIFIED`) that no one may repurpose.
- Bottom-line-first for existing docs (`editorial_pass`): every in-place pass
  runs a buried-lede test: a reader who stops at the first paragraph must
  know the outcome and whether to keep reading. On failure, `advise` mode
  reports a structure advisory (proposed order plus a drafted lead paragraph)
  without moving a thing; `apply` mode may reorder and retitle, for callers
  who own relinking.
- Data visibility (`data`): four or more homogeneous items render as a table,
  never prose; the decision column leads; the summary or verdict row comes
  before detail rows; outliers get named in a sentence above the table. eli5
  is the exception: it states the one comparison the reader cares about.

## What can go wrong

The design's own risk register
([`research/synthesis/design-principles.md`](research/synthesis/design-principles.md)
§4) puts translator error near the top: the human lane is your window, and a
confident wrong BLUF is worse than shorthand. The mitigations are the
`never_compress` passthrough (error text, quotes, and numbers survive any
rewrite verbatim), the facts-before-stories and delete-test checks, the
`UNVERIFIED` fence for speculation — and practice. In the pilot we read the
full diff before trusting it, and the verifier exists so that reading is
cheap. Treat translated narratives the way you treat any report: spot-check
against the evidence it cites.

## Honest status (v0.2)

Working today: the translator and modes, the style gates and corpus, the
buried-lede test with structure advisories and the data-rendering contract,
the lexicon proposal flow, `/respeak:init`, the session-start lexicon hook,
the statusline script, the measure and verify tools with their test suite
(45 cases plus a bash end-to-end suite for the gate hook), the opt-in
PostToolUse enforcement gate and its `--fail-on`/budgets/`gate.allow`
knobs, the verify-then-relay loop in the `respeak:respeak` skill and agent,
the headless `respeak-render.sh` wrapper for the API lane, and the optional
milestone-narrative Stop hook (off by default).

Declared in config but not yet enforced by tooling: the lexicon entry cap,
edit-distance check, usage-based expiry, auto-ratification gate, fresh-decoder
audits, and audience-profile wiring in the skill surface. The config is the
contract. The enforcement scripts are the next milestone, alongside a
`respeak compile` step that emits the corpus as a [Vale](https://vale.sh/)
style package for CI (the corpus is already RE2-safe for it) and a
display-only translation hook that shows you plain English while the
transcript keeps the shorthand.

## Layout

```
.claude-plugin/            manifest + marketplace + userConfig
agents/respeak.md          the translator (Sonnet, isolated context window)
skills/respeak/            /respeak:respeak — the translation entry point
skills/init/               /respeak:init — per-project setup
hooks/hooks.json           session-start lexicon status; optional milestone narrative;
                           opt-in PostToolUse style gate on Write/Edit
scripts/                   measure, verify-edit, gate hook, headless render, statusline,
                           lexicon digest renderer
tests/                     edit-safety + measure/gate enforcement suite (markdown, code,
                           py, html, yaml, json, bash gate-hook end-to-end)
config/respeak.config.yaml the influence surface (v1)
corpus/                    banned phrases, replacements, lexicon, style maps
docs/architecture.md       the design, with resolved questions
research/                  11 source studies, 4 synthesis passes, the pilot artifacts
```

The design decisions are argued, with citations, in
[`research/synthesis/design-principles.md`](research/synthesis/design-principles.md):
twelve principles and five named risks. This README was itself measured with
the bundled scanner (zero error hits, zero warn hits) and adversarially
reviewed against the repo before you read it.

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
