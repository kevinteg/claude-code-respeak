# Landscape & Media Research: Two-Lane AI Communication + Media Recommendations

Research for the **respeak** project (agent-swarm shorthand lexicon + human-facing translator subagent).
Date: 2026-08-31. Researcher: landscape/media research agent.

## Part 1: Existing Solutions — Two-Lane AI Communication Landscape

### 1.1 LLM Observability Platforms

**LangSmith (LangChain)** — https://www.langchain.com/langsmith
- Agent/LLM observability platform: tracing, monitoring, evals, cost tracking.
- **Closest overlap feature: "Insights"** — "Automatically analyze and cluster your traces to detect usage patterns, common agent behaviors, and failure modes. Unsupervised topic clustering... **Executive summary with key findings**."
- So LangSmith already produces a human-facing narrative summary *from* machine traces (one direction of respeak's two lanes).
- Honest overlap vs respeak: **partial (~25%)**. It summarizes traces for humans after the fact, but there is no ratified inter-agent lexicon, no compression of the agent-to-agent channel, no multi-register translation (ELI5/BLUF/technical), and no legibility feedback loop into how agents communicate. It is observability, not communication-protocol design.

**Langfuse** — https://langfuse.com/
- Open-source (MIT) LLM engineering platform: hierarchical traces, prompt management, LLM-as-judge evals, human annotation queues, dashboards. 34k GitHub stars, "21 of Fortune 50," 90B+ observations/month. Has an in-app "Langfuse Assistant" that investigates production data and "turns findings into approved actions," plus a SKILL.md for Claude Code / coding agents.
- Honest overlap vs respeak: **low (~15%)**. The Assistant narrates what happened in traces on demand, but Langfuse doesn't generate standing multi-register narratives, doesn't define or govern agent shorthand, and doesn't nudge agent output style. Notably it integrates with Claude Code and ships a SKILL.md — a useful *pattern precedent* for respeak's plugin packaging, not a competitor.

**incident.io** — https://incident.io/
- "AI software reliability platform." Its "Nexus" production-intelligence model + Investigations agent "scans thousands of signals, delivers a structured hypothesis in seconds," and — notably — "uses an adversarial agent to challenge its own conclusions **before sharing**." Response includes AI Scribe (call transcription), auto status-page updates ("keep customers in the loop"), and AI-drafted post-incident summaries.
- Honest overlap vs respeak: **moderate on one lane (~30%)**. It is a strong existence proof for "machine reasoning internally, curated narrative externally," with distinct audiences (engineers in Slack vs customers on status pages = register switching). But the internal representation is telemetry/signals, not a governed linguistic shorthand, and there's no lexicon ratification or legibility economics. Domain-locked to incident response.
**AgentOps** — https://www.agentops.ai/
- Agent observability SDK/dashboard (OpenAI, CrewAI, AutoGen, 400+ LLMs): event visualization, time-travel debugging of agent runs, token counts, cost tracking, fine-tuning on saved completions.
- Honest overlap vs respeak: **minimal (~5%)**. Pure telemetry/replay; no narrative generation for humans at all, no lexicon concept. Relevant only as a metrics baseline (it proves per-agent token accounting is a solved measurement problem).

**Helicone** — https://www.helicone.ai/
- AI gateway + LLM observability (routing, debugging, request analytics, sessions, prompts, playground); joined Mintlify per site banner.
- Honest overlap vs respeak: **minimal (~5%)**. Gateway-level logging; no executive narratives, no shorthand governance.

### 1.2 AI Summary/Narrative Products (one-lane translators)

**Slack AI ("AI in Slack" / Slackbot)** — https://slack.com/features/ai
- Built-in AI: channel recaps, thread summaries, huddle notes, enterprise search — "AI shouldn't make you think, it should help you do... built with knowledge from your company."
- Honest overlap vs respeak: **partial on the translator lane (~20%)**. Channel recaps ARE machine-generated narrative digests of high-volume communication humans can't keep up with — the exact UX respeak's translator targets. But the source channel is human chat, not agent shorthand; single register; no lexicon or legibility feedback.
**PagerDuty Advance** — https://www.pagerduty.com/platform/generative-ai/
- Generative AI for incident ops: "Get AI-generated incident summaries instantly... automatically synthesizes incident data, chat conversations, and system logs into clear, actionable summaries," plus — key phrase — "**Generate audience-specific status updates in seconds**." Customer quote (Worldline): "It gives us an update draft on the fly while responders focus on triaging... we can customize those updates per customer."
- Honest overlap vs respeak: **moderate on the translator lane (~30%)**. "Audience-specific status updates" is exactly respeak's multi-register translation idea (exec vs customer vs engineer), machine-source → human narrative. No shorthand lexicon, no governance, incident-domain only.

**GitHub Copilot PR summaries** — https://docs.github.com/en/copilot/how-tos/copilot-on-github/copilot-for-github-tasks/create-a-pr-summary
- Copilot generates a natural-language summary of a pull request's diff (what changed, which files a reviewer should focus on). Also a cookbook recipe "summarize repository activity" under "communicate effectively."
- Honest overlap vs respeak: **partial (~20%)**. Diffs are the ultimate machine-efficient representation and Copilot narrates them for humans — a clean one-lane translator. Single register, no lexicon, no feedback into how the "machine lane" is written.

### 1.3 Machine-Lane Precedents (efficient agent-to-agent representation)

**GibberLink** — https://raw.githubusercontent.com/PennyroyalTea/gibberlink/main/README.md
- Viral Feb-2025 demo (11labs × a16z hackathon winner; Forbes/TechCrunch coverage): two ElevenLabs voice agents "switch to ggwave data-over-sound protocol when they identify [the] other side as AI, and keep speaking in english otherwise."
- Honest overlap vs respeak: **conceptual twin of the machine lane (~20%)**, and the best pop-culture citation for the respeak README. It proves the mode-switch (human-legible ↔ machine-efficient) but has no lexicon governance and — crucially — no translator keeping humans in the loop; the human is simply cut out. Respeak is arguably "GibberLink plus accountability."

**LLMLingua / LLMLingua-2 (Microsoft)** — https://raw.githubusercontent.com/microsoft/LLMLingua/main/README.md
- "Effectively Deliver Information to LLMs via Prompt Compression": drops low-information tokens so compressed prompts stay machine-comprehensible but become human-illegible; LLMLingua-2 is 3–6x faster; integrated into LangChain and Prompt flow. Papers at EMNLP 2023 / ACL 2024.
- Honest overlap vs respeak: **machine lane only (~15%)**. Statistical token-dropping, not a ratified vocabulary; compression is lossy and unreadable with no translator. Useful prior art for measuring compression ratio vs task fidelity — a metric respeak's lexicon governance should also track.
**Agora protocol (Oxford: Marro, La Malfa, Wooldridge, Torr et al.)** — https://arxiv.org/abs/2410.11905
- "A Scalable Communication Protocol for Networks of Large Language Models" (Oct 2024). Names the "Agent Communication Trilemma" (versatile / efficient / portable). Core design: "agents typically use **standardised routines for frequent communications, natural language for rare communications, and LLM-written routines for everything in between**." Observes "the emergence of self-organising, fully automated protocols... without human intervention."
- Honest overlap vs respeak: **highest conceptual overlap of anything found (~40%) on the machine lane**. Its frequency-based tiering (routine ↔ natural language) is precisely the economic logic behind a ratified shorthand lexicon. What Agora explicitly does NOT have: a human-facing translator, multi-register narrative, or legibility as a design goal — it celebrates "minimal involvement of human beings," the opposite of respeak's human-in-the-loop stance. Cite it; then differentiate on legibility.

**DroidSpeak (UChicago/Microsoft)** — https://arxiv.org/abs/2411.02820
- "KV Cache Sharing for Cross-LLM Communication and Multi-LLM Serving" (Nov 2024, rev. Jul 2025): agents skip natural language entirely and exchange reusable KV-cache prefixes across same-architecture LLMs, selectively recomputing a few layers with "negligible quality loss."
- Honest overlap vs respeak: **machine lane, more radical (~10%)**. Where respeak keeps a textual (auditable, translatable) shorthand, DroidSpeak goes sub-linguistic — zero human legibility by construction. Good foil for respeak's design argument: text shorthand is the legibility-preserving point on the compression curve.

### 1.4 "Smart Brevity" / BLUF Tooling

**Axios HQ** — https://www.axioshq.com/
- Commercial internal-comms software from the Smart Brevity authors: "AI writing help — brainstorm critical updates and synthesize key details," "Smart Brevity guidance — editing assistance to make your updates more engaging," best-practice templates, engagement analytics.
- Honest overlap vs respeak: **partial on the human lane (~25%)**. It is a productized BLUF generator with an enforced house style — a real-world precedent for respeak's "ratified style config" idea, applied to humans instead of agents. No machine lane, no lexicon of agent shorthand.

### 1.5 Verdict: does anything already do respeak?

**No single product or paper covers respeak's full loop.** The pieces all exist separately:
- Machine-efficient agent channel: GibberLink (mode switch), Agora (frequency-tiered routines ≈ lexicon economics), LLMLingua (token compression), DroidSpeak (KV-cache exchange).
- Human-narrative generation from machine state: LangSmith Insights (exec summaries from traces), PagerDuty Advance (**audience-specific** updates), incident.io (multi-audience incident comms), Copilot PR summaries (diff → prose), Slack AI recaps.
- Enforced brevity style + templates for humans: Axios HQ.
**Nobody combines**: (a) a governed/ratified shorthand lexicon, (b) an always-on translator subagent with multiple registers (ELI5/BLUF/technical), and (c) a legibility-nudging feedback loop from translator back into the agents' tokenization. The differentiation sentence writes itself: *existing tools either compress the machine lane (and cut the human out) or narrate for humans (without touching how machines talk); respeak governs both lanes and the exchange rate between them.*

## Part 2: Vetted Media Recommendations

All entries verified by fetching a live page (see Sources). Audiobook availability noted only where a fetched page confirmed it; libro.fm and Audible block curl (403), so unmarked titles are "audiobook status unverified."

### 2.1 Books — writing craft & de-AI-ing prose

1. **Book: On Writing Well — William Zinsser.** Verified via Wikipedia (Zinsser bio: "a style guide for non-fiction writers that sold an estimated 1.5 million copies"). The canonical clutter-cutting text; Zinsser's war on "clutter" maps 1:1 onto stripping AI filler phrases. Why: source of banned-phrase instincts for the translator's style config.
2. **Book: The Sense of Style — Steven Pinker (2014).** Verified via Wikipedia ("applies science to the process of writing," successor to Strunk & White). Why: Pinker's "curse of knowledge" chapter is the theory behind why agent shorthand becomes illegible to humans — directly motivates the translator subagent.
3. **Book: Several Short Sentences About Writing — Verlyn Klinkenborg (2012).** Verified via Wikipedia (author) + Open Library (first pub 2012). Why: sentence-level economy as a discipline; the anti-"however-therefore-moreover" manifesto; ideal calibration text for the BLUF register.
4. **Book: Smart Brevity — Jim VandeHei, Mike Allen, Roy Schwartz (2022).** Verified via Open Library + Axios HQ product site. Why: the operational playbook for BLUF mode (one strong first sentence, "Why it matters," bullets, bolding); respeak's manager mode can adopt its structure wholesale.
5. **Book: The Pyramid Principle — Barbara Minto (first pub 1978).** Verified via Wikipedia (Minto, "executive communication") + Open Library. Why: answer-first, grouped-and-ordered logic is the structural spec for the manager/BLUF register; the SCQA framing suits incident narratives.

### 2.2 Books — manager & interpersonal communication

6. **Book: Simply Said — Jay Sullivan (2016, Wiley).** Verified via Open Library. Why: "focus on the audience, not yourself" — the single organizing principle respeak's translator needs when choosing register and detail level.
7. **Book: Radical Candor — Kim Scott (2017).** Verified via Wikipedia ("feedback that incorporates both praise and criticism"). Why: model for how the translator should report agent failures to humans — direct, caring, non-euphemistic; anti-corporate-hedging.
8. **Book: Crucial Conversations — Patterson, Grenny, McMillan, Switzler (2002; 3rd ed. 2022; 2M+ sold).** Verified via Wikipedia. Why: high-stakes disclosure patterns (facts before stories, safety before content) for when the swarm must deliver bad news.
9. **Book: Everyone Communicates, Few Connect — John C. Maxwell (2009).** Verified via Open Library. Why: connection-over-transmission framing; useful counterweight so BLUF mode doesn't become affectless.

### 2.3 Books — linguistics of jargon, convention & language change

10. **Book/Audiobook: Because Internet — Gretchen McCulloch (Riverhead/Penguin).** Verified via gretchenmcculloch.com/book/ — "available in hardcover, **audiobook**, ebook, and paperback." "Linguistically inventive online communities spread new slang and jargon with dizzying speed... even the most absurd-looking slang has genuine patterns behind it." Why: the best popular account of how communities ratify shorthand conventions — literally the sociolinguistics of respeak's lexicon governance.

### 2.4 Podcasts

11. **Podcast: Lingthusiasm — Gretchen McCulloch & Lauren Gawne.** Verified via lingthusiasm.com (monthly, transcripts for every episode; NYT: "will change the way you see everyday communications"). Starter episode spotted on-page: "How to rebalance a lopsided conversation." Why: linguistics of convention-formation, jargon, and register — respeak's theory soundtrack.
12. **Podcast: Radical Candor Podcast — Amy Sandler with Kim Scott & Jason Rosoff.** Verified via radicalcandor.com/podcast/ (active; recent episode on meeting sabotage/efficiency). Why: applied manager-communication patterns for the BLUF register's tone.
13. **Podcast: Latent Space — swyx & Alessio.** Verified via latent.space/about ("technical newsletter, podcast (top 10 in US Tech)... for the rising class of AI Engineers"; 200k+ subs; Karpathy endorsements). Why: the community where token/context engineering and agent-swarm practice is discussed first; likely audience for respeak itself.
14. **Podcast: Grammar Girl (Quick and Dirty Tips) — Mignon Fogarty.** Verified via Wikipedia (Fogarty; "educational podcast about English grammar and usage... one of the best podcasts of 2007 by iTunes," still producing). Why: micro-lessons on usage that make good linting rules for translator output.

### 2.5 Blogs, newsletters, style guides, official resources

15. **Blog: Anthropic Engineering** — https://www.anthropic.com/engineering. Verified; directly relevant posts on the live index: "Effective context engineering for AI agents" (Sep 2025), "Effective harnesses for long-running agents" (Nov 2025), "Code execution with MCP: Building more efficient agents," "Building a C compiler with a team of parallel Claudes," "Demystifying evals for AI agents." Why: first-party guidance on exactly respeak's runtime substrate (Claude Code, skills, long-running agents, context/token economics).
16. **Blog: Simon Willison's Weblog** — https://simonwillison.net/. Verified via /about (creator of Datasette, Django co-creator, blogging since 2002; weekly-ish newsletter). Why: the reference practitioner-blog on LLM tooling; also a model of legible technical narration of machine behavior.
17. **Resource: plainlanguage.gov → Digital.gov plain language guide series.** Verified (plainlanguage.gov material; fetch landed on digital.gov "Plain language guide series"): "Plain language... is critical... Not only is plain language more efficient and effective. **It is also the law**" (Plain Writing Act of 2010, audience-specific writing requirement). Why: free, public-domain style rules — harvest directly into translator style config.
18. **Style guide: Google developer documentation style guide** — https://developers.google.com/style. Verified; index includes pages for "Jargon," "Anthropomorphism," "Active voice," "Voice and tone," "Word list," "Inclusive language." Why: the "Jargon" and "Anthropomorphism" pages are ready-made policy for translator output about agents.
19. **Style guide: Microsoft Writing Style Guide** — https://learn.microsoft.com/en-us/style-guide/welcome/. Verified ("Make every word matter... writing style and terminology for all communication"). Why: "warm and crisp" voice + bigger-idea brevity philosophy; good default voice for ELI5 mode.
20. **Style guide: Mailchimp Content Style Guide** — https://styleguide.mailchimp.com/. Verified (sections: Voice and Tone, Grammar and Mechanics, Word List, Writing for Accessibility/Translation — and it opens with a "TL;DR"). Why: the most human of the corporate guides; its voice-vs-tone split maps to respeak's fixed-facts/variable-register design.
21. **Newsletter: AINews (by Latent Space)** — verified on latent.space/about ("AINews: Weekday Roundups"). Why: itself a machine-assisted digest of overwhelming AI-community volume — a daily working demo of the summarize-the-firehose pattern.

### 2.6 Bonus primary sources (from Part 1, doubling as reading list)

22. **Paper: "A Scalable Communication Protocol for Networks of LLMs" (Agora)** — arxiv.org/abs/2410.11905. Why: the Agent Communication Trilemma is respeak's design-space map.
23. **Paper: DroidSpeak** — arxiv.org/abs/2411.02820. Why: the extreme end of the compression-vs-legibility curve.
24. **Repo/Demo: GibberLink** — github.com/PennyroyalTea/gibberlink. Why: the cautionary/viral demo to cite when explaining why respeak keeps a translator.
25. **Repo: Microsoft LLMLingua** — github.com/microsoft/LLMLingua. Why: empirical compression-ratio-vs-fidelity methodology to borrow for lexicon evaluation.

## Part 3: Corpus Candidates for respeak

### 3.1 Banned/flagged phrases for translator output (de-AI prose)
Drawn from Zinsser-style clutter-cutting, Smart Brevity practice, and plain-language guidance:
- "delve", "dive into", "deep dive" (as filler), "furthermore", "moreover", "additionally" (sentence-initial), "it's worth noting that", "it's important to note", "in today's fast-paced world", "leverage" (as verb for "use"), "utilize", "robust", "seamless", "cutting-edge", "landscape" (metaphorical), "navigate" (metaphorical), "unpack", "at the end of the day", "game-changer", "holistic", "synergy", "circle back", "on the same page", "in order to" (→ "to"), "due to the fact that" (→ "because"), "a number of" (→ count or "some"), "very"/"really" intensifiers, "I hope this helps", "as an AI", "certainly!", "great question".
- Hedging stacks: "may potentially", "could possibly", "it seems that perhaps".
- Google style guide: avoid anthropomorphizing systems ("the agent wants/believes" → "the agent is configured to / the agent's output indicates") — nuanced for respeak since agents ARE actors; rule: anthropomorphize intent only when traceable to an actual instruction.

### 3.2 Structural rules per register
- **BLUF/manager mode** (Minto + Smart Brevity + military BLUF): (1) One-sentence answer/ask first. (2) "Why it matters" second. (3) Max 3 grouped support points, each ≤1 line, MECE-ish. (4) Numbers over adjectives ("cut tokens 34%" not "significantly reduced tokens"). (5) State cost, risk, and the decision needed. (6) Hard cap ~120 words.
- **ELI5 mode** (plain language + Mailchimp voice): one idea per sentence; common words; concrete analogy allowed but flagged as analogy; define any lexicon term on first use; no acronyms without expansion; target ~grade-6 readability.
- **Technical mode**: precise identifiers, exact counts/hashes/paths; lexicon terms permitted **with hover/inline gloss on first use per document**; link to the ratified lexicon entry.
- All registers: facts identical across registers (voice fixed, tone varies — Mailchimp's voice/tone split); never bury a failure below a success (Radical Candor: direct + caring).

### 3.3 Lexicon governance conventions (from Part 1 findings)
- Frequency-tiered vocabulary (Agora): only concepts used ≥N times/window earn a shorthand entry; rare concepts stay in natural language.
- Every ratified term carries: canonical gloss, human-readable expansion, ratification date/version, usage counter, deprecation state.
- Track compression ratio AND task-fidelity delta per term (LLMLingua-style evaluation) plus "translator burden" (tokens the translator spends re-expanding it).
- Legibility nudge rule: if a term's translator-burden or mistranslation rate exceeds threshold, translator files a lexicon amendment (rename/split/deprecate) — the feedback loop no existing tool has.
- Audience-specific rendering is table stakes (PagerDuty Advance's "audience-specific status updates"); respeak should ship ≥3 registers from day one.
- Adversarial self-check before human delivery (incident.io Nexus: "adversarial agent to challenge its own conclusions before sharing") — a reviewer pass on translator narratives.

### 3.4 Config parameter ideas
- `registers: [eli5, bluf, technical]`; `bluf.max_words: 120`; `eli5.readability_grade_max: 6`
- `lexicon.ratify_min_uses`, `lexicon.review_window`, `lexicon.max_terms`, `lexicon.deprecate_after_idle`
- `translator.banned_phrases: [...]` (§3.1), `translator.numbers_over_adjectives: true`
- `legibility.translator_burden_threshold`, `legibility.amendment_auto_file: true`
- `narrative.adversarial_review: true`

## Sources (all fetched 2026-08-31)
- https://www.langchain.com/langsmith
- https://langfuse.com/
- https://incident.io/
- https://www.agentops.ai/
- https://www.helicone.ai/
- https://slack.com/features/ai
- https://www.pagerduty.com/platform/generative-ai/ (via link discovery on pagerduty.com; /platform/ai/ and /platform/pagerduty-advance/ 404)
- https://docs.github.com/en/copilot/how-tos/copilot-on-github/copilot-for-github-tasks/create-a-pr-summary (older doc URLs 404; found via docs.github.com/en/copilot/how-tos)
- https://raw.githubusercontent.com/PennyroyalTea/gibberlink/main/README.md
- https://raw.githubusercontent.com/microsoft/LLMLingua/main/README.md
- https://arxiv.org/abs/2410.11905 (Agora)
- https://arxiv.org/abs/2411.02820 (DroidSpeak)
- https://www.axioshq.com/
- https://en.wikipedia.org/api/rest_v1/page/summary/{On_Writing_Well→William Zinsser, The_Sense_of_Style, Barbara_Minto, Verlyn_Klinkenborg, Mignon_Fogarty, Radical_Candor, Crucial_Conversations} (Smart_Brevity summary API returned empty — no article confirmed)
- https://openlibrary.org/search.json (Simply Said; Everyone Communicates, Few Connect; Several Short Sentences About Writing; The Pyramid Principle; Smart Brevity)
- https://gretchenmcculloch.com/book/
- https://lingthusiasm.com/
- https://www.radicalcandor.com/podcast/
- https://www.latent.space/about
- https://simonwillison.net/about/
- https://www.plainlanguage.gov/ (redirects to digital.gov plain language guide series)
- https://www.anthropic.com/engineering
- https://developers.google.com/style
- https://learn.microsoft.com/en-us/style-guide/welcome/
- https://styleguide.mailchimp.com/
- Not fetchable: libro.fm search (403); Google Books API (429); search engines (challenge pages, as briefed). Audiobook availability therefore only confirmed for Because Internet.
