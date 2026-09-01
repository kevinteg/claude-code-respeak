# Anthropic Engineering: Effective context engineering for AI agents

- Source: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- Fetched: 2026-08-31 (extraction notes; not verbatim)
- Relevance to respeak: the economic argument for a shorthand lane (attention budget), and the sub-agent pattern the translator lives in.

## Definitions

- Context engineering = "strategies for curating and maintaining the optimal set of tokens during LLM inference"; the iterative successor to prompt engineering.
- Guiding principle: **"find the smallest set of high-signal tokens that maximize the likelihood of your desired outcome."**

## Constraints

- **Context rot**: recall degrades as context grows — a performance gradient, not a cliff. Models have fewer specialized parameters for very long dependencies.
- **Attention budget**: n² pairwise relationships for n tokens; context is "a finite resource with diminishing marginal returns."
  - *Respeak note: this is the quantitative case for swarm shorthand — every narrative flourish in inter-agent traffic is n²-taxed.*

## System prompts

- Calibrate altitude: between brittle hardcoded logic and vague guidance — "specific enough to guide behavior effectively, yet flexible enough to provide strong heuristics."
- Structure with XML tags / Markdown headers; start minimal with the best model, add against observed failure modes.
- Few-shot: diverse canonical examples, not a laundry list of edge cases.

## Tools

- Token-efficient returns; self-contained; robust to error; extremely clear intended use.
- "If a human engineer can't definitively say which tool should be used in a given situation, an AI agent can't be expected to do better."

## Just-in-time context

- Keep lightweight identifiers (paths, queries, links); load at runtime rather than pre-embedding everything.
- Progressive disclosure via metadata (naming conventions, hierarchies, timestamps).
- Hybrid: pre-compute for speed where domains are static, explore dynamically elsewhere.

## Long-horizon techniques

- **Compaction**: summarize and reinitiate near the limit; preserve architectural decisions, unresolved bugs, implementation details; discard redundant tool outputs. Tune for recall first, then precision. Lowest-risk form: clearing tool results.
- **Structured note-taking / agentic memory**: NOTES.md-style files outside the window; Claude-plays-Pokémon kept precise tallies across thousands of steps.
- **Sub-agent architectures**: specialists explore in clean contexts and return condensed summaries, "often 1,000–2,000 tokens"; the orchestrator keeps only distilled results.
  - *Respeak note: the translator is exactly this — narrative synthesis isolated from the swarm's working context; the swarm never pays for wordsmithing tokens.*

## Selection criteria

- Compaction → long conversational back-and-forth.
- Note-taking → iterative development with milestones.
- Multi-agent → parallel research/analysis.

## Scaling observation

"Smarter models require less prescriptive engineering" — but treating context as precious remains central. "Do the simplest thing that works."
