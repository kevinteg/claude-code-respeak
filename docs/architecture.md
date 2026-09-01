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
| `/respeak [mode]` command | user asks | one subagent turn, on demand |
| `respeak` skill | natural-language ask ("explain to my manager") | same, model-triggered |
| milestone auto-narrative | harness hook at commit/phase boundaries (planned) | background, per milestone |
| lexicon proposals | as a side effect of translation | file writes only |

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
