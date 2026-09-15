# respeak architecture

v1 — revised against the research synthesis. The evidence and full reasoning
live in `research/synthesis/design-principles.md` (verdict, 12 principles,
risks); this document states the resulting design.

**Synthesis verdict:** supported and unique. No existing system combines a
governed evolving shorthand vocabulary + an always-on multi-register
translator + a legibility feedback loop; every component has mature precedent
(Anthropic sub-agent and attention-budget guidance; a century of codified
expert shorthands; Agora/Caveman token economics).

## Problem

Long-running agent sessions optimize their own traffic. Left alone, a swarm
converges on compressed conventions ("shorthand") that cut token cost — the
context-engineering principle says every token in inter-agent traffic is
attention-taxed, so compression pressure is structural, not accidental. The
failure mode is that the compressed dialect becomes alien to the human
supervising the work: the human either fights the optimization (forcing the
swarm to write prose, paying the tax everywhere) or loses the loop.

## Design: two lanes, one lexicon, one translator

```
                      ┌──────────────────────────┐
   swarm traffic ────▶│  machine lane            │
   (working agents)   │  shorthand, governed by  │
                      │  corpus/lexicon.yaml     │
                      └───────────┬──────────────┘
                                  │ observed terms
                                  ▼
                      ┌──────────────────────────┐     proposals
                      │  respeak translator      │────▶ corpus/proposals/
                      │  (subagent, read-only    │      (human ratifies)
                      │   toward swarm state)    │
                      └───────────┬──────────────┘
                                  │ narratives
                                  ▼
                      ┌──────────────────────────┐
   human reader  ◀────│  human lane              │
                      │  eli5 | bluf | technical │
                      │  tuned by config         │
                      └──────────────────────────┘
```

### The machine lane

The swarm may use any shorthand that is **ratified** in `corpus/lexicon.yaml`.
The lexicon is the single source of truth, modeled on codified expert
shorthands (brevity codes, Q-codes, ATC phraseology) and on the
long-running-harness finding that structured registries resist agent drift
where prose does not. Properties:

- **Append-mostly**: entries are proposed, ratified, or retired — never
  silently edited or deleted.
- **Legibility floor** (`shorthand.legibility_floor`): entries too alien are
  rejected regardless of token savings. This is the "nudge" — the translator
  prefers the variant of a convention closest to plain English, so the
  dialect drifts toward needing *less* translation over time, not more.
- **never_compress list**: error messages, security findings, user quotes,
  numbers with units always pass verbatim (precedent: the Joint Commission
  do-not-use abbreviation list — domains ban compression where it caused harm).

Injection point: the ratified lexicon is surfaced to the swarm via CLAUDE.md
(or an equivalent context file), so conventions are adopted at emission time
rather than imposed by post-hoc rewriting.

### The translator

A subagent (`agents/respeak.md`) that is deliberately **non-impactful to the
swarm**: it reads swarm output, transcripts, and the lexicon; its only writes
are rendered narratives and lexicon proposals. It runs in its own context
window (sub-agent architecture per the context-engineering post), so the
swarm never pays wordsmithing tokens and the translator never pollutes
working context.

Entry points, cheapest first:

| Surface | When it fires | Cost profile |
| --- | --- | --- |
| `/respeak:respeak [mode] [source]` | user asks | one subagent turn, on demand |
| `respeak` skill, natural language | "explain to my manager" and similar asks | same, model-triggered |
| `respeak-render.sh` (headless) | CI or a swarm's own automation, through `claude -p` | one print-mode call per round, gated and retried |
| Stop hook (milestone auto-narrative) | after a substantive turn, when `narrative.auto_narrative` resolves true (off by default) | one short paragraph of context per milestone |
| SessionStart hook | session start, only in a project with `.claude/respeak/` | one sentence of context |
| PostToolUse gate | Write or Edit of a Markdown file in a project with `gate.enabled: true` | a local scanner run; blocks only on a verdict |
| `/respeak:init`, `/respeak:off [gate]`, `/respeak:on [gate]`, `/respeak:report` | user asks | local script runs, no model turn |
| lexicon proposals | as a side effect of translation | file writes only |

Every hook honors the session overrides (resolved question 7): a marker from
`/respeak:off` or `/respeak:on`, or `RESPEAK_HOOKS=off` and
`RESPEAK_GATE=off|on` in the environment, is read before any work.

### The human lane

Three modes with distinct contracts (see `config/respeak.config.yaml` and
`corpus/style/tone-mapping.md`):

- **eli5** — no assumed background, one analogy max, repaid immediately.
- **bluf** — first sentence is the result/decision/ask; forwardable unedited.
- **technical** — conclusion first, evidence as file:line, open questions last.

All modes pass the same gates: replacements first, banned-phrase scan second,
tone-axis behaviors throughout. The gates are data (`corpus/*.yaml`), not
prompt prose, so they are versionable, lintable (Vale-compilable), and
auditable.

## The influence model

The exposed configuration is the whole interface between the human and the
optimization:

1. **Narrative knobs** (`narrative.*`, `modes.*`): tone axes and tech_level
   change how the human lane reads. They never touch the machine lane.
   These are the keys any layer may set, down to a single folder
   (resolved question 6).
2. **Shorthand governance** (`shorthand.*`): ratification mode, legibility
   floor, and the never-compress list bound how far the machine lane may
   drift. The human changes a number; the swarm's dialect follows.
3. **Corpus** (`corpus/*.yaml`): banned phrases and replacements are the
   editorial voice, maintained as data with severities.

Invariant: **the translator proposes, config disposes, the human ratifies.**
No agent both proposes and ratifies a convention.

## Resolved questions (details: research/synthesis/design-principles.md §2)

1. **Milestone auto-narrative → hooks, never cron.** Layered: a `Stop` hook
   (input carries `last_assistant_message`) with an async milestone heuristic;
   `SubagentStop`/`TaskCompleted` for swarm workers and phase boundaries; and
   `MessageDisplay` → `displayContent` as the zero-context-cost display
   translator — the human sees the translation while transcript and model
   context keep the shorthand.
2. **Lexicon injection → CLAUDE.md `@import` of a generated digest**
   (`lexicon-active.md`, <200 lines), installed with consent by
   `/respeak:init` since plugins can't ship CLAUDE.md; freshness via
   `SessionStart`/`FileChanged` hooks injecting factual `additionalContext`.
   `.claude/rules/*.md` with `paths:` gives register scoping (shorthand
   allowed in `notes/**`, banned in `docs/**`). A skill is the wrong vehicle:
   emission-time adoption needs session-start presence.
3. **Vale compilation → yes, the designed CI path.** `respeak compile` emits a
   `styles/Respeak/` package + `.vale.ini` with per-mode output globs; ratio
   and judgment checks go to an LLM-judge post-processor; diagnostics feed
   back to the translator as rewrite prompts. Precondition: the corpus schema
   carries `exceptions`, declared anchor scope, and density tiers (done in
   corpus v1).
4. **Ratification fidelity → a three-layer gate** on Caveman's "$0.00 until
   proven" burden: static sign-quality checks (min edit distance 2, no
   near-neighbors of never_compress classes), a **fresh-decoder** round trip
   (an agent with no interaction history expands samples from the lexicon
   alone), and readback usage evidence for auto-fast-track.
5. **tech_level 5 shorthand → feature, as explicit opt-in only.** The `author`
   profile (`lexicon_access: inline`) is the one lawful convergence point of
   the two lanes; guardrails: `register_marker: required`, never_compress and
   reserved metawords stay verbatim, and author-profile traffic stays in the
   monthly fresh-decoder audit sample.

6. **Where configuration lives → layered, nearest to the target wins**
   (v0.4; contract in `docs/config-layers.md`). The influence surface above
   was one file per project, which made "different tones for different
   folders" and "my default across every repo" both impossible. The
   resolver (`scripts/respeak-config.py`) now merges, lowest first: plugin
   defaults, the plugin's install-time userConfig, `~/.claude/respeak/
   config.yaml`, ancestor `.respeak.yaml` files above the project, the
   project's `.claude/respeak/config.yaml` and gitignored `config.local.yaml`,
   `scopes:` entries keyed by `paths:` globs (the `.claude/rules` idiom),
   folder `.respeak.yaml` files from the project root down, `$RESPEAK_CONFIG`
   files, and the invocation's own flags. Two invariants keep the influence
   model intact: governance keys (`gate.enabled`, `gate.include/exclude`,
   `shorthand.*`) are project-only and dropped with a warning anywhere else,
   so no folder or user file can switch enforcement or ratification; and
   every consumer (gate hook, Stop hook, statusline, skill, headless render)
   reads through the one resolver, with one project-root rule (nearest
   `.claude/respeak/config.yaml` above the target, never the user config
   directory, then the launch directory, then `.git`), so `explain` shows
   the truth each of them saw. `narrative.profile` is expanded by the resolver, which wires
   the audience profiles into the skill surface for the first time.
7. **Session-scoped control → overrides above the layers, never a layer**
   (v0.5; contract in `docs/config-layers.md`, "Session overrides"). The
   manifest registers every hook for every installer; a session that does
   not want one declines it with a marker (`/respeak:off [gate]`,
   `/respeak:on [gate]`, written by `scripts/respeak-session.sh`) or with
   the environment (`RESPEAK_HOOKS=off`, `RESPEAK_GATE=off|on`), and each
   hook reads `scripts/respeak-override.sh` before doing anything else.
   Precedence is marker, then environment, then the layers. The layers stay
   about place and the overrides about time, so a personal preference never
   has to be expressed by editing the manifest (which reaches every
   installer), and `explain` still shows what the hooks saw.

## Refinements the research forced (v0 → v1)

- **Ratification alone is not governance.** The lexicon now carries the full
  codified-shorthand toolkit: size cap (~150), min token edit distance,
  scheduled re-harmonization (90d), usage-based retirement (180d), reserved
  repair metawords (CORRECTION, SAY-AGAIN, UNVERIFIED), in-band register
  marking, readback for high-stakes messages, and monthly fresh-decoder
  audits — because drift happens *inside* governed systems and the most
  fluent agents deviate most (ICAO's lesson).
- **Capture, don't suppress.** FAIR 2017 suppressed emergent codewords by
  rewarding English; respeak's differentiator is capturing them into the
  lexicon as proposals, with the translator as the standing reward channel.
  The nudge lives at the ratification boundary, never as per-message pressure.
- **Three registers of access, not two lanes only:** `forbidden` /
  `expand-first-use` / `inline`, keyed to audience profiles (who reads), which
  are orthogonal to modes (what form) and context (reader state).
- **Risks and mitigations** (drift, translator hallucination, nudge backfire,
  governance ossification, platform rot) are enumerated with mitigations in
  design-principles.md §4 — each mitigation is a config field or hook, not a
  hope.
