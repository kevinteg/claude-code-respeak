# Caveman (caveman.so)

- Source: https://caveman.so/
- Fetched: 2026-08-31 (extraction notes)
- Relevance to respeak: closest commercial prior art for the **shorthand lane** (machine-facing token efficiency). NOT a de-AI-styler — it optimizes cost, not prose voice. The narrative lane (human-facing wordsmithing) is out of its scope, which is exactly the gap respeak fills.

## What it is

A token-efficiency platform claiming ~65% AI cost reduction via output compression, context optimization, and model routing. Tagline: **"Why many token when few do trick."**

## Mechanisms

- Compresses context before transmission; reduces output verbosity while preserving semantics; detects "computational waste" in requests.
- Example shown: a React debugging explanation compressed from ~72 tokens to ~21 tokens by stripping explanatory padding.
- Sits at the gateway level: drop-in for LiteLLM, Vercel AI SDK, LangChain (OpenAI-compatible proxy).
- Auto-caching, prompt compression, waste detection.
- **27 grader types** verify changes don't degrade quality before activation — savings show "$0.00" until proven on live traffic.

## Distribution

- Claude Code skill: `npx skills add JuliusBrussee/caveman`
- Proxy CLI: `npm install -g @caveman-ai/cli && caveman setup --install`
- Browser extension (ChatGPT, Claude, Gemini).
- Caveman Cloud in private beta; free tier for the GitHub skill.
- Published research: CaveGemma, CaveBench methodology.

## Design lessons for respeak

1. **Verified savings, not vibes**: grade compressed output against quality checks before adopting a compression. Respeak's lexicon proposals should carry the same burden of proof (a translation-fidelity check before a shorthand term is ratified).
2. **Gateway placement**: compression as an interception layer, not a rewrite pass — respeak's shorthand nudges similarly belong at the point of emission (CLAUDE.md conventions, tool-response shaping), not post-hoc rewriting.
3. **Caveman speaks caveman to machines; respeak must also speak human to humans.** The two-lane split is the differentiator.
