# Landscape Assessment: respeak

Pillars used for scoring — **P1** translator subagent with mode/register config, **P2** ratified shorthand lexicon, **P3** legibility-nudging feedback loop. Percentages are my judgment estimates against these three pillars specifically; where the research files gave their own single-number estimates against a looser framing, I cite them. Uncertainty is real on anything ±10%.

## 1. EXISTING SOLUTIONS VERDICT

**1. Caveman (caveman.so / JuliusBrussee) — ~30%.** Token-efficiency skill + proxy for Claude Code: output compression ("caveman-speak"), type-routed input compressors, 33.2% benchmarked input-token savings, `caveman learn` with consent-gated fixes (token-compression-prior-art.md:126-131). P2 partial: "a *style register*... rather than a ratified vocabulary. No lexicon file, no governance, no evolution" (token-compression-prior-art.md:132). P1 none — it compresses *toward* machines; "the narrative lane... is out of its scope" (caveman-so.md:5). P3 adjacent-only: its 27 graders gate on *fidelity*, not legibility (caveman-so.md:17). Respeak adds: the entire human lane, lexicon governance, legibility economics. Caveman is also the packaging proof (plugin marketplace install, token-compression-prior-art.md:131).

**2. Agora protocol (Oxford, arXiv 2410.11905) — ~30%.** Frequency-tiered agent comms: "standardised routines for frequent communications, natural language for rare" (landscape-and-media.md:54) — the exact economic logic of a ratified lexicon (P2 conceptual). P1 none; P3 *inverted* — it celebrates "minimal involvement of human beings" (landscape-and-media.md:55). The file calls it "highest conceptual overlap of anything found (~40%) on the machine lane" (landscape-and-media.md:55). Respeak adds: the translator, registers, and legibility as a first-class objective.

**3. SynthLang (ruvnet) — ~25%.** Glyph DSL with a durable closed operator set (`↹ • ⊕ Σ`) plus an `evolve` command — "the strongest lexicon precedent found" (token-compression-prior-art.md:60), with evolution under selection pressure (token-compression-prior-art.md:57). P2 substantial; P1 none (its `translate` runs NL→glyph, the wrong direction); P3 none — evolution optimizes efficiency, not legibility, and there's "no governance/versioning story" (token-compression-prior-art.md:59). Caveat: single-author, marketing-grade benchmarks (token-compression-prior-art.md:59). Respeak adds: ratification process, translator, human registers.

**4. TOON — ~20%.** Token-lean serialization, -42.6% tokens at equal retrieval accuracy, high human legibility, and — crucially — a versioned public spec + conformance suite: "the *governance model* respeak's lexicon wants" (token-compression-prior-art.md:73). P2 partial (governance template for a *static structural* spec, not an evolving vocabulary); P1/P3 none. Respeak adds: semantic vocabulary, translation, evolution.

**5. FIPA-ACL / KQML — ~20%.** "The canonical ratified lexicon in agent history" — ~22 performatives with formal semantics (token-compression-prior-art.md:96-97). P2 yes, historically; P1/P3 none, and it "ossified because there was no lightweight evolution process" (token-compression-prior-art.md:97). Respeak adds: an amendment mechanism and the human lane — the two things whose absence killed FIPA.

**6. incident.io — ~20%.** Machine reasoning internally, curated multi-audience narrative externally, plus an adversarial self-check "before sharing" (landscape-and-media.md:21-22). P1 partial (register switching by audience); P2/P3 none; domain-locked to incidents. Respeak adds: governed shorthand as the source channel, configurable registers, cross-domain.

**7. PagerDuty Advance — ~20%.** "Generate audience-specific status updates in seconds" (landscape-and-media.md:37) — respeak's multi-register translation, productized, incident-only. P1 partial; P2/P3 none. Respeak adds: everything upstream of the narrative.

**8. FAIR negotiation agents, 2017 (arXiv 1706.05125) — ~15%.** Not a product — the founding cautionary tale *and* the only prior art that implemented legibility pressure: after codewords emerged ("no reward to sticking to English"), they "used some established techniques to reward them for using English correctly" (token-compression-prior-art.md:111-113). P3 ancestor; P1/P2 none. Respeak adds: capturing emergent codewords into a governed lexicon instead of suppressing them, with the translator as the standing reward channel (token-compression-prior-art.md:114, 120).

**9. GibberLink — ~15%.** Explicit mode switch (English for humans, ggwave for agents) with a payload that stays decodable by outsiders (token-compression-prior-art.md:85). P2 transport-layer only; P1 none — "the human is simply cut out" (landscape-and-media.md:48); P3 none. Respeak is "GibberLink plus accountability" (landscape-and-media.md:48).

**10. AntiSlop sampler + Slop Forensics (sam-paech) — ~15%.** Generation-time downweighting of a configurable slop-phrase list; "the closest existing mechanism to respeak's banned-phrases.yaml enforced at generation time" (deai-language-landscape.md:233); Slop Forensics gives the audit methodology (deai-language-landscape.md:234). P3 partial (style enforcement, but no loop from a translator back into agent tokenization); P1 tooling-adjacent; P2 none. Respeak adds: the loop, the lexicon, the registers.

**11. LLMLingua family (Microsoft) — ~10%.** 2x–20x statistical compression producing "degraded English" humans can barely parse (token-compression-prior-art.md:12-13); no durable conventions (token-compression-prior-art.md:14). Value to respeak is its evaluation methodology (compression ratio vs task fidelity, landscape-and-media.md:52), not its mechanism.

**12. LangSmith Insights — ~10%.** Exec summaries clustered from traces (landscape-and-media.md:12) — single-register, post-hoc, no lexicon, no nudging. (File's looser estimate: ~25%, landscape-and-media.md:14.)

**Tail (≤10% each):** Axios HQ (enforced BLUF house style for humans — precedent for the style config, landscape-and-media.md:64-65); Gist tokens (durable reusable compressed artifact "in spirit" a lexicon entry, but continuous vectors — zero legibility, token-compression-prior-art.md:36-37); DroidSpeak (sub-linguistic KV-cache exchange — the far pole respeak argues against, token-compression-prior-art.md:88-90); Slack AI / Copilot PR summaries (one-lane, single-register digests); Langfuse / AgentOps / Helicone (observability, no communication-protocol design); A2A / NLIP (envelope-level standards that deliberately leave the vocabulary uncompressed/local — NLIP actually *legitimizes* per-swarm lexicons with a translation layer, token-compression-prior-art.md:93, 102).

**Does anything already do this whole thing?** No — and both research passes reached that conclusion independently after checking observability platforms, summary products, compression research, agent protocols, and the Claude Code plugin ecosystem (landscape-and-media.md:69-73; token-compression-prior-art.md:153). Every pillar exists separately and maturely: Agora/SynthLang/FIPA have lexicon economics or actual ratified vocabularies; PagerDuty/incident.io have audience-specific translation; FAIR 2017 and AntiSlop have legibility pressure. But no system combines a *governed, evolving* shorthand vocabulary with an always-on multi-register translator, and — the sharpest gap — nobody runs a feedback loop where the human-lane translator files amendments against the machine-lane vocabulary. The nearest miss on pillars 2+3 is SynthLang (lexicon that evolves, but blindly, with no legibility signal); the nearest miss on pillar 1 is PagerDuty Advance (registers, but incident-only and with no machine lexicon beneath it). Confidence caveat: both files searched via fetches on 2026-08-31 and could not use search engines freely (landscape-and-media.md:177), so a small/new project could have been missed; but the Claude Code ecosystem specifically was checked and "no existing Claude Code plugin found that maintains a *ratified evolving lexicon* with a translator lane" (token-compression-prior-art.md:137).

## 2. MEDIA SHORTLIST (16, ranked within groups)

Verification note: every entry below was verified by a live page fetch (landscape-and-media.md:77), but **audiobook availability is confirmed only for *Because Internet*** — libro.fm/Audible blocked the researcher (403), Google Books rate-limited (landscape-and-media.md:177). All other books: print/ebook verified, **audiobook unverified**.

### A. Lexicon governance & convention formation (pillar 2)
1. **Because Internet — Gretchen McCulloch.** Hardcover/paperback/ebook/**audiobook confirmed** (landscape-and-media.md:96). The sociolinguistics of how communities ratify shorthand — respeak's lexicon governance, in book form.
2. **Lingthusiasm** (podcast, monthly, full transcripts; landscape-and-media.md:100). Convention-formation, jargon, and register — the theory soundtrack.
3. **Agora paper** (arXiv 2410.11905, free). The Agent Communication Trilemma is respeak's design-space map (landscape-and-media.md:117).

### B. Translator craft & register design (pillar 1)
4. **The Sense of Style — Pinker.** Print/ebook verified; audiobook unverified. "Curse of knowledge" is *why* agent shorthand goes illegible — the translator's raison d'être (landscape-and-media.md:82).
5. **Smart Brevity — VandeHei/Allen/Schwartz.** Print verified via Open Library + Axios HQ site; **flag:** Wikipedia summary API returned empty, weakest verification of the books (landscape-and-media.md:165); audiobook unverified. The operational BLUF playbook — manager mode can adopt it wholesale (landscape-and-media.md:84).
6. **The Pyramid Principle — Minto.** Print verified; audiobook unverified. Answer-first SCQA structure = the manager-register spec (landscape-and-media.md:85).
7. **On Writing Well — Zinsser.** Print verified; audiobook unverified. Clutter-cutting maps 1:1 onto stripping AI filler — source of banned-phrase instincts (landscape-and-media.md:81).
8. **Several Short Sentences About Writing — Klinkenborg.** Print verified; audiobook unverified. Sentence-level economy; BLUF calibration text (landscape-and-media.md:83).
9. **plainlanguage.gov / Digital.gov plain-language series** (free web). Public-domain style rules to harvest directly into the ELI5 config — "it is also the law" (landscape-and-media.md:109).
10. **Google developer documentation style guide** (free web). The "Jargon" and "Anthropomorphism" pages are ready-made policy for writing *about* agents (landscape-and-media.md:110).
11. **Mailchimp Content Style Guide** (free web). Its voice-vs-tone split is exactly respeak's fixed-facts/variable-register design (landscape-and-media.md:112).

### C. Tone, candor & de-AI legibility (pillar 3)
12. **Radical Candor — Kim Scott** (book, print verified/audiobook unverified) **+ the Radical Candor podcast** (verified active; landscape-and-media.md:90, 101). The model for reporting agent failures: direct, caring, non-euphemistic.
13. **Grammar Girl** (podcast, still producing; landscape-and-media.md:103). Micro usage lessons that convert directly into translator lint rules.

### D. Substrate & audience (agent-swarm engineering)
14. **Anthropic Engineering blog** (free web). First-party guidance on respeak's exact runtime — context engineering, long-running agents, token economics (landscape-and-media.md:107).
15. **Simon Willison's Weblog** (free web + newsletter). Reference practitioner blog *and* a working model of legible narration of machine behavior — he also mainstreamed "slop" (landscape-and-media.md:108; deai-language-landscape.md:164).
16. **Latent Space** (podcast + newsletter, incl. AINews daily digest). Where token/context engineering discourse happens first, and respeak's likely first audience; AINews is itself a live demo of the summarize-the-firehose pattern (landscape-and-media.md:102, 113).

Cut deliberately: Crucial Conversations, Simply Said, Maxwell (their one usable principle each is covered by #12 and #9–11), Microsoft Writing Style Guide (redundant with #10–11), Slack AI/Copilot docs (competitor exhibits, not media).