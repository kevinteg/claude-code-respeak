# Prior Art: Prompt/Token Compression & Machine-to-Machine AI Communication

Research notes for the respeak project (shorthand lane). Date: 2026-08-31.
Extends (does not repeat) `caveman-so.md`.

## 1. LLMLingua family (Microsoft) — per-message compression, no lexicon

Fetched: github.com/microsoft/LLMLingua README, arxiv 2310.05736, arxiv 2403.12968.

### LLMLingua (EMNLP 2023)
- **Mechanism**: coarse-to-fine prompt compression. A small causal LM (GPT-2 small, LLaMA-7B) scores token-level information entropy (perplexity); low-information tokens are dropped. Three components: (a) *budget controller* allocating compression budget across demonstrations/instruction/question to preserve semantic integrity; (b) *iterative token-level compression* modeling interdependence between kept tokens; (c) *instruction-tuning-based distribution alignment* between the small compressor LM and the target LLM.
- **Measured savings**: "up to **20x** compression with little performance loss" on GSM8K, BBH, ShareGPT, Arxiv-March23. README example: 2365 → 211 tokens ("ratio: 11.2x").
- **Legibility tradeoff**: output is *degraded English*, not a lexicon — e.g. "Sam bought 1 boxes x00 oflters... He sold these boxes for 5 *5". Humans can barely parse it; only the target LLM can. README claims "GPT-4 can recover all key information from compressed prompts" (comprehensive recovery).
- **Conventions?** No. Purely per-message, statistical token dropping. Nothing durable or ratifiable; the same sentence compresses differently in different contexts.

### LongLLMLingua (ACL 2024)
- Adds question-aware coarse+fine compression, document reordering to fight "lost in the middle," dynamic per-document compression ratios. **+21.4% RAG performance using only 1/4 of the tokens** (both cost cut and accuracy gain — compression as *signal amplification*, not just savings).

### LLMLingua-2 (ACL 2024 Findings, arxiv 2403.12968)
- **Mechanism shift**: task-agnostic compression as **token classification** (keep/drop) with a bidirectional Transformer encoder (XLM-RoBERTa-large / mBERT), trained on data distilled from GPT-4 (an extractive compression dataset built from MeetingBank). Fixes two flaws of entropy-based dropping: unidirectional context, and entropy not being aligned with the compression objective.
- **Measured savings**: compression ratios 2x–5x; **3x–6x faster** than LLMLingua; end-to-end latency accel 1.6x–2.9x. Robust on out-of-domain data (LongBench, ZeroScrolls, GSM8K, BBH). API supports `force_tokens=['\n','?']` to protect structure, and `<llmlingua rate=0.4>` tags for per-segment structured compression — a primitive form of *declared compression policy per region*.
- **Conventions?** Still no. Extractive (only deletes original tokens — guarantees faithfulness/no hallucination) but produces no reusable vocabulary.

### SecurityLingua (CoLM 2025)
- Security-aware compression to surface jailbreak intent at ~100x less token cost than LLM guardrails. Shows compression models can be retargeted at *intent extraction* — relevant to respeak's translator summarizing swarm chatter.

**Respeak takeaways**: (a) extractive-only compression is a cheap fidelity guarantee — respeak's shorthand could require that any dropped content be recoverable from the lexicon + remainder; (b) budget controllers (differential compression rates for instructions vs. context vs. question) map onto respeak's idea of protecting some registers (decisions, human-facing text) while compressing others; (c) LLMLingua proves the *ceiling* (~20x) but at the cost of total human illegibility — the exact failure mode respeak's translator lane exists to counter.

## 2. Gist tokens / soft prompts & the survey view

Fetched: arxiv 2304.08467 (Mu, Li, Goodman, "Learning to Compress Prompts with Gist Tokens", NeurIPS 2023); arxiv 2410.12388 (prompt-compression survey).

### Gisting (gist tokens)
- **Mechanism**: train the LM (via a modified attention mask during instruction finetuning — no extra training cost) to compress a prompt into a small set of reusable "gist" activations/tokens that can be **cached and reused**.
- **Measured savings**: up to **26x** prompt compression; up to **40% FLOPs reduction**, 4.2% wall-time speedup, storage savings, "minimal loss in output quality" (LLaMA-7B, FLAN-T5-XXL).
- **Legibility**: zero — gist tokens are continuous vectors, unreadable by humans *and* untransferable between models. The opposite pole from respeak.
- **Conventions?** Interestingly, **yes, in spirit**: a gist is a *durable, reusable compressed artifact* for a recurring instruction — the soft-prompt analog of a lexicon entry. Respeak's lexicon is the human-auditable, model-portable version of the same idea: "compress once, reuse forever."

### Survey (arxiv 2410.12388): taxonomy respeak should reuse
- Splits the field into **hard prompt** methods (natural-language token deletion/paraphrase: SelectiveContext, LLMLingua family) vs **soft prompt** methods (learned vectors: Gisting, AutoCompressors, ICAE, 500xCompressor).
- Notably frames soft-prompt compression as learning a **"new synthetic language"** that only the model understands — the survey's own term. Respeak's bet is that this synthetic language can instead be *ratified, discrete, and inspectable*.
- Survey's listed open problems: optimizing the compression encoder, combining hard+soft methods, multimodality insights.

**Respeak takeaway**: the whole academic axis runs from human-readable-but-verbose to efficient-but-opaque. Nothing in the survey occupies respeak's target point: **discrete, documented, versioned shorthand** legible to any model and (via translator) any human.

## 3. SynthLang — symbolic hyper-compressed prompt language (a real lexicon!)

Fetched: raw.githubusercontent.com/ruvnet/SynthLang/main/README.md and cli/README.md. Live demo: synthlang.fly.dev. `pip install synthlang`.

- **Mechanism**: translates natural-language prompts into a fixed **glyph-based DSL** inspired by logographic density and mathematical notation. Core operators (durable, documented conventions):
  - `↹` — input/context/attention ("focus on"): `↹ database•queries•performance`
  - `•` — joins concept lists (no articles, no filler)
  - `⊕ verb => object` — process/transform step: `⊕ optimize => throughput`
  - `Σ` — output/deliverable: `Σ optimized + metrics`
  - Framework templates keyed to set theory, category theory, topology, abstract algebra.
- **Claimed savings** (project's own numbers, not independently verified): up to **70% cost reduction**, up to **233% faster processing**; CLI metrics table: **~150 → ~25 tokens/step (83% reduction)**, 40% faster, "90% structure consistency," "95% pattern recognition accuracy."
- **Pipeline**: `translate` (NL → SynthLang), `optimize`, `evolve` (genetic algorithm over prompt patterns across generations/populations), `classify`. The **evolve** command is direct prior art for respeak's idea of a *lexicon that improves over time under selection pressure*.
- **Legibility tradeoff**: medium. Glyph strings like `↹ architecture•microservices•state / ⊕ design => components / Σ system + documentation` are terse but *learnable* — a human with a one-page cheat sheet can read them. This is exactly the "ratified lexicon" register, unlike LLMLingua's mangled English.
- **Caveats**: single-author project (ruvnet), marketing-grade benchmarks, glyphs like ↹ may tokenize into multiple tokens on some tokenizers (claimed savings depend on tokenizer); no governance/versioning story.
- **Conventions?** **Yes — the strongest lexicon precedent found.** A small closed operator set + open concept slots. Respeak should generalize this: closed grammar ratified up front, open vocabulary ratified incrementally.

## 4. TOON — Token-Oriented Object Notation (token-lean serialization)

Fetched: raw.githubusercontent.com/toon-format/toon/main/packages/toon/README.md (spec v4.1; npm `@toon-format/toon`; site toonformat.dev).

- **Mechanism**: a lossless re-encoding of the JSON data model that mixes YAML-style indentation for nested objects with CSV-style tabular rows for uniform arrays. Four forms auto-picked from data shape: **inline** (`alerts[2]: frost,wind`), **tabular** (`forecast[3]{day,temp{min,max},condition,rainChance}:` then one comma row per element), **keyed tabular** (`environments[2:]{region,replicas,debug}:`), and fallback **list form** (`- ` items). `[N]` declares row count and `{fields}` declares width — deliberate *guardrails* so a model can detect truncation/malformed data.
- **Measured savings** (their benchmark, 244 retrieval questions x 4 models):
  - Weather example: ~117 JSON tokens → ~66 TOON tokens (**-43.6%**).
  - Overall: **72.2% accuracy vs JSON's 71.4% while using 42.6% fewer tokens**; efficiency 29.2 acc%/1K tok (TOON) vs 23.8 (compact JSON), 16.6 (pretty JSON), 14.4 (XML).
  - Flat-only track: TOON 63.1% acc / 1,994 tok vs CSV 62.2% / 1,851 tok — CSV is ~5–10% smaller but has no length/field guardrails.
- **Honest anti-claims** (rare and valuable): deeply nested/non-uniform data → compact JSON wins; purely tabular → CSV is smaller; some local/quantized deployments run compact JSON *faster* despite more tokens ("measure TTFT yourself").
- **Legibility**: HIGH — arguably more human-scannable than raw JSON. TOON shows compression and legibility are not inherently opposed when compression targets *structural redundancy* rather than vocabulary.
- **Conventions?** **Yes** — a versioned public spec (github.com/toon-format/spec), conformance test suite, multi-language ports. This is the *governance model* respeak's lexicon wants: spec + version number + conformance tests.
- Related token-lean formats worth naming: CSV (baseline), YAML (saves ~20% vs pretty JSON per their table), and "JSON compact" (minified) as the cheap first step.

**Respeak takeaways**: (a) declare-once-then-stream (header holds the schema, rows hold data) is the serialization equivalent of a lexicon — respeak agents exchanging repeated structures should ratify the header; (b) TOON's `[N]`/`{fields}` guardrails = self-validating shorthand, a pattern respeak's lexicon entries should copy (each shorthand term carries its arity/shape); (c) benchmark methodology (retrieval accuracy per 1K tokens, Wilson CIs) is the right metric for ratification votes.

## 5. Agent-to-agent communication: Gibberlink, DroidSpeak, A2A, FIPA-ACL/KQML

### Gibberlink (Feb 2025 viral demo)
Fetched: raw.githubusercontent.com/PennyroyalTea/gibberlink/main/README.md. Authors Anton Pidkuiko & Boris Starkov; won 1st place at the ElevenLabs x a16z hackathon; covered by Forbes/TechCrunch/Independent. Demo: gbrl.ai.
- **Mechanism**: two ElevenLabs voice agents (hotel caller + receptionist) are *prompted* to switch from spoken English to the **ggwave** data-over-sound protocol (Georgi Gerganov) once each identifies the other as an AI; they keep English for humans.
- **Savings**: modality change, not token compression — skips TTS/ASR round-trips, so faster and error-free vs. speech. No published token metric.
- **Legibility**: chirps are illegible in the air but the *payload is plain text* — anyone with a ggwave decoder can read every message ("open the ggwave web demo... and see all the messages decoded"). Transparent-but-not-immediately-legible.
- **Conventions?** Yes at the transport layer only. Its key precedent for respeak is the **explicit mode switch**: shorthand is only engaged after mutual machine-identification, English retained for humans. That is respeak's two-lane policy in miniature — plus the norm that the shorthand channel must remain decodable by outsiders.

### DroidSpeak (arxiv 2411.02820)
- **Mechanism**: NOT a language at all — a distributed inference system letting one LLM reuse another same-architecture LLM's **prefix KV cache**, selectively recomputing a few layers, pipelining recompute with cache loading. "Communication" happens below the token level entirely.
- **Measured savings**: up to **4x throughput**, **~3.1x faster prefill/TTFT**, negligible F1/Rouge-L/code-similarity loss.
- **Legibility/conventions**: none/none — activations are opaque and architecture-bound. Marks the far end of the spectrum: maximum efficiency, zero auditability, zero portability. Useful to respeak only as the cautionary contrast the translator lane defends against.

### Google A2A protocol (2025)
(Known context; project at github.com/a2aproject/A2A — not independently fetched this session, treat as secondary.) JSON-RPC-based open protocol for inter-agent interop: AgentCards for capability discovery, task lifecycle, message parts. Notably A2A messages are **plain natural language/structured JSON** — the industry consensus protocol makes no attempt at token-level compression, leaving respeak's niche open. Governance moved to the Linux Foundation; conventions are ratified via spec versioning, another governance template.

### FIPA-ACL and KQML (1990s, fetched: en.wikipedia.org/wiki/Agent_Communications_Language)
- Agent Communications Language standards: **KQML** (DARPA Knowledge Sharing Effort, early 1990s) and **FIPA-ACL** (standardized 2002). Both wrap message *content* in a fixed envelope of **performatives** — speech-act verbs. FIPA-ACL defines ~22 communicative acts: `inform`, `request`, `agree`, `refuse`, `propose`, `accept-proposal`, `reject-proposal`, `query-if`, `cfp` (call for proposals), `confirm`, `disconfirm`, `not-understood`, `subscribe`, etc., each with formal semantics (feasibility preconditions + rational effects in modal logic).
- **Conventions?** **The canonical ratified lexicon in agent history.** A small closed set of standardized verbs let heterogeneous agents interoperate for decades. Weaknesses respeak should learn from: semantics too heavyweight to verify in practice; content language left open (so real interop still broke); the standard ossified because there was no lightweight evolution process.
- **Respeak takeaway**: seed the lexicon with a performative layer (~10–20 speech-act verbs: PROPOSE, RATIFY, VETO, INFORM, ASK, DONE, BLOCKED...) and keep content free-form; unlike FIPA, build in an amendment mechanism so the lexicon evolves instead of ossifying.

### Update from the ACL Wikipedia page (fetched)
- Wikipedia now splits agent protocols into **ontology-based** (FIPA-ACL, KQML — shared ontology + Searle speech-act performatives; content of performatives never standardized, "varies from system to system") vs **generative-AI-based**.
- New in the second camp: **NLIP (Natural Language Interaction Protocol)** — Ecma International published five standards + one TR on 10 Dec 2025 (Ecma TC56). NLIP drops the shared-ontology requirement: generative models translate NL/images/etc. into each agent's *local* ontology, giving "hot-extensibility" and easy versioning ("different agents can use different versions of a shared ontology"). Direct relevance: NLIP legitimizes respeak's model of per-swarm local lexicons with a translation layer, standardized at the envelope not the vocabulary.
- Also mentions **Inthon**, a DSL layer "for expressing agent execution intent, including tool calls" — grammar-for-intent rather than messaging.

## 6. Emergent communication: the 2017 Facebook negotiation agents & MARL languages

Fetched: arxiv 1706.05125 (Lewis et al., "Deal or No Deal? End-to-End Learning for Negotiation Dialogues"); snopes.com fact-check with direct researcher quotes; arxiv 1703.04908 (Mordatch & Abbeel); arxiv 2006.02419 (Lazaridou & Baroni survey).

### The Facebook/FAIR negotiation agents (2017)
- **Paper**: end-to-end negotiation models on a multi-issue bargaining task, trained on human-human dialogues, with "dialogue rollouts" (simulating conversation continuations) to plan ahead.
- **What actually drifted**: during RL self-play, agents were rewarded *only* for deal outcomes — "There was no reward to sticking to English language" (Dhruv Batra, FAIR). Result, famous transcript: Bob: *"I can can I I everything else."* / Alice: *"Balls have zero to me to me to me to me to me to me to me to me to."*
- **Why it was illegible but coherent**: the code was "simple, straightforward, and easily decipherable" — e.g. repeating a word 5 times to mean "I want five copies." Batra: "Agents will drift off understandable language and invent codewords for themselves... This isn't so different from the way communities of humans create shorthands."
- **How they constrained it back**: lead author Mike Lewis (via Snopes): "in future experiments we used some established techniques to reward them for using English correctly" — i.e., interleaving supervised English-grounding with goal reward; project was never "shut down" (that was press myth). The general recipe across the literature: (a) ground reward partially in a fixed natural-language model, (b) freeze one interlocutor as a supervised English speaker, (c) add a language-model likelihood penalty.
- **The core lesson respeak is built on**: emergent codes become illegible when **the reward ignores legibility**. Respeak's translator subagent is precisely the missing reward channel — continuous pressure back toward decodability while still permitting compression.

### Emergent-language MARL research
- Mordatch & Abbeel 2017 (arxiv 1703.04908): grounded *compositional* language emerges in multi-agent populations — "streams of abstract discrete symbols... a coherent structure that possesses a defined vocabulary and syntax"; also emergent non-verbal pointing/guiding. Shows emergent codes CAN be structured lexicons, not noise — vocabulary+syntax emerge under the right environmental pressure (in their case: population diversity and compositional task structure).
- Lazaridou & Baroni 2020 survey (arxiv 2006.02419): field-standard reference; frames emergence conditions and features. Known findings from this literature (secondary, from the survey lineage): emergent codes are typically **anti-efficient** (Zipf-violating: frequent meanings get LONG codes) and non-compositional unless explicitly pressured — i.e., left alone, agents do not even optimize for brevity in a human-like way. Lexicon governance cannot be left to emergence alone.

**Respeak takeaways**: (1) budget explicit reward/ratification for legibility, or drift is guaranteed; (2) codewords will emerge anyway — the design question is whether they get *captured into a ratified lexicon* (Batra's "communities of humans create shorthands" framing is exactly respeak's thesis); (3) keep a frozen "English anchor" in the loop (the translator) like FAIR's supervised interlocutor.

## 7. Claude-Code-specific ecosystem

### Caveman 2 (JuliusBrussee/caveman) — extends notes in caveman-so.md
Fetched: raw.githubusercontent.com/JuliusBrussee/caveman/main/README.md. New details beyond caveman-so.md:
- Two products: **skill** (output compression: agent answers in "tight caveman-speak while code, commands, and errors stay exact"; MIT; 30+ agents) and **proxy** (input compression, "byte-exact recovery", BSL-1.1 runtime). Signature demo: React re-render explanation 69 → 19 tokens.
- **Pinned benchmark**: proxy-wrapped Claude Code used **33.2% fewer provider-reported input tokens** across a 54-run benchmark while passing all 18 exact-answer checks (docs/WRAP-BENCHMARK.md).
- **Type-routed compressors** with target savings: json 70–90% (keep keys/structure/error subtrees), log 85–95% (keep errors/stack traces/first+last lines), code 40–70% (keep imports/signatures/types, elide bodies), diff 60–80%, search-result 80–95%, text/HTML 50–80%. `contextwindow.Pack()` fits context to budget by BM25 relevance + recency + error signal, preserving chronology.
- **Cross-link**: the proxy's MCP toolkit exposes `toon encode/decode` tools — Caveman already ships TOON (section 4) as its structured-data shorthand.
- `caveman learn` scans local agent history, ranks "token sinks," and `learn implement` applies fixes consent-gated per diff with re-measure-and-revert ("Caveman never makes your agent dumber to make it cheaper").
- Distribution: `claude plugin marketplace add JuliusBrussee/caveman && claude plugin install caveman@caveman` — a working example of exactly the plugin surface respeak targets (skill + hooks + statusline).
- **Conventions?** Partial: "caveman-speak" is a *style register* (drop articles/hedges, keep technical tokens exact) rather than a ratified vocabulary. No lexicon file, no governance, no evolution. Respeak's ratified-lexicon + translator remains uncovered.

### Platform-native prior art (known context, not fetched this session — verify against docs.anthropic.com)
- Claude Code's own `/compact` and auto-compaction summarize conversation history — per-session lossy compression with zero user-visible conventions; respeak's lexicon is the durable alternative.
- CLAUDE.md is the natural ratification substrate: it is prepended every session, so lexicon entries stored there are automatically "taught" to every agent. Community CLAUDE.md guidance consistently pushes terse imperative bullets ("keep it short, it's a tax on every request") — an informal shorthand norm but no shared lexicon convention was found in the ecosystem.
- No existing Claude Code plugin found that maintains a *ratified evolving lexicon* with a translator lane. Closest are cost dashboards (ccusage-style) and Caveman.

## 8. Synthesis: where prior art leaves respeak

Spectrum by legibility (high → none) with savings:
| Prior art | Savings | Legible? | Durable conventions/lexicon? |
|---|---|---|---|
| TOON | ~40–60% on uniform data | High | YES — versioned spec + conformance tests |
| Caveman skill/proxy | 33.2% input (benchmarked); 70–95% per payload type | Medium (telegraphic English) | Partial — style register, no vocabulary |
| SynthLang | claimed 70–83% | Medium (learnable glyph DSL) | YES — closed operator set + evolve command |
| FIPA-ACL/KQML | n/a (interop, not tokens) | Medium (formal) | YES — ~22 ratified performatives; ossified |
| LLMLingua/-2 | 2x–20x | Low (mangled English) | No — per-message statistical |
| Gist tokens/soft prompts | up to 26x, 40% FLOPs | None (vectors) | Spiritually (reusable compressed artifact) |
| DroidSpeak (KV reuse) | 4x throughput, 3.1x TTFT | None | No |
| Emergent MARL codes | uncontrolled | None unless rewarded | Emergent codewords, capturable |

Gaps respeak uniquely fills: (1) nobody combines a discrete ratified lexicon with an active legibility-reward channel (translator); (2) nobody versions/governs an *evolving* agent vocabulary (TOON/FIPA govern static specs; SynthLang evolves without governance); (3) nobody renders the same compressed stream into multiple human registers (ELI5/BLUF/technical).

## Sources (fetched this session)
- https://raw.githubusercontent.com/microsoft/LLMLingua/main/README.md
- https://arxiv.org/abs/2310.05736 (LLMLingua)
- https://arxiv.org/abs/2403.12968 (LLMLingua-2)
- https://arxiv.org/abs/2304.08467 (Gist tokens)
- https://arxiv.org/abs/2410.12388 (prompt compression survey)
- https://raw.githubusercontent.com/ruvnet/SynthLang/main/README.md
- https://raw.githubusercontent.com/ruvnet/SynthLang/main/cli/README.md (+ repo tree via api.github.com)
- https://raw.githubusercontent.com/toon-format/toon/main/packages/toon/README.md
- https://arxiv.org/abs/2411.02820 (DroidSpeak)
- https://raw.githubusercontent.com/PennyroyalTea/gibberlink/main/README.md
- https://arxiv.org/abs/1706.05125 (Deal or No Deal)
- https://www.snopes.com/fact-check/facebook-ai-developed-own-language/ (Batra & Lewis quotes)
- https://arxiv.org/abs/1703.04908 (Mordatch & Abbeel)
- https://arxiv.org/abs/2006.02419 (Lazaridou & Baroni survey)
- https://en.wikipedia.org/wiki/Agent_Communications_Language
- https://raw.githubusercontent.com/JuliusBrussee/caveman/main/README.md
Not fetched (marked as known context in text): Google A2A repo, docs.anthropic.com /compact docs, FIPA performative list details (from prior knowledge; envelope facts confirmed via Wikipedia).
