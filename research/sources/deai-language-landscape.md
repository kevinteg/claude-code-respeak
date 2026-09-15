# De-AI Language Landscape: Tells of AI-Generated Prose

Research for respeak corpus/banned-phrases.yaml. Compiled 2026-08-31.

## 1. Wikipedia "Signs of AI writing" (WP:AISIGNS) — condensed catalog

> Attribution: this section condenses a page written by Wikipedia contributors and licensed [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). The condensed version is available under the same license; the rest of this repository is MIT.

Fetched 2026-08-31 from https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing. This is the single richest curated catalog; maintained by WikiProject AI Cleanup. Key caveats the page itself gives: detection tools (GPTZero, Pangram) have non-trivial error rates; average humans detect AI text near chance, but heavy LLM users hit ~90% accuracy (Russell, Karpinska & Iyyer 2025, arXiv:2501.15654); human language is drifting toward LLM style (arXiv:2409.01754), so tells decay over time.

Root cause framing (useful for respeak docs): LLMs "regress to the mean" — they replace specific, unusual facts with generic, positive, importance-flavored statements. "The subject becomes simultaneously less specific and more exaggerated."

### 1.1 Content-level tells (each with the page's "words to watch")

| Tell (WP shortcut) | Words/patterns to watch | Severity signal |
|---|---|---|
| Undue emphasis on significance/legacy (WP:AILEGACY, WP:AITREND) | stands/serves as, is a testament/reminder, a crucial/pivotal/vital/significant/key role/moment, underscores/highlights its importance/significance, reflects broader, symbolizing its ongoing/enduring/lasting, contributing to the, setting the stage for, marking/shaping the, represents/marks a shift, key turning point, evolving landscape, focal point, indelible mark, deeply rooted | strong |
| Canned notability/media-coverage emphasis (WP:AIATTR) | independent coverage, local/regional/national media outlets, trade publications, cited/featured/profiled in, written by a leading expert, "maintains an active social media presence" | strong; more common in 2025+ models |
| Superficial analyses (WP:SUPERFICIAL) | sentence-final present-participle ("-ing") clauses: highlighting/underscoring/emphasizing…, ensuring…, reflecting/symbolizing…, contributing to…, cultivating/fostering…, encompassing…, enhancing…, valuable insights, align/resonate with | strong |
| Promotional/ad language (WP:AIPUFFERY) | boasts a, vibrant, rich, profound, enhancing, showcasing, exemplifies, commitment to, natural beauty, nestled, in the heart of, groundbreaking, renowned, featuring, diverse array, rich cultural heritage, breathtaking, stunning natural beauty | strong |
| Vague attributions / weasel (WP:AIWEASEL) | Industry reports, Observers have cited, Experts argue, Some critics argue, "several sources/publications" when few cited, "such as" before non-exhaustive lists | medium |
| Outline-like "Challenges / Future Outlook" endings (WP:FACESCHALLENGES) | "Despite its X, [subject] faces several challenges…", "Despite these challenges", sections titled "Challenges and Legacy", "Future Outlook", "Future Prospects" | strong (it's the rigid formula, not the topic) |
| Title-as-proper-noun leads | "[List title] refers to / is a curated compilation of…" | medium |
| "Awards and recognition" section | "X and Y" section headers, esp. "Awards and recognition" | medium |
| Knowledge-cutoff disclaimers (WP:AICUTOFF) | "as of my last knowledge update", "While specific details are limited/scarce…", "not widely available/documented/disclosed", "based on available information", "maintains a low profile" | unambiguous |
| Collaborative chatbot voice (WP:CERTAINLY) | I hope this helps, Of course!, Certainly!, You're absolutely right!, Would you like…, is there anything else, let me know, more detailed breakdown, here is a…, "I hope this message finds you well" | unambiguous |
| Phrasal templates / placeholders (WP:AIPLACEHOLDER) | [Your Name], [Specific Topic], access-date=2025-XX-XX, INSERT_SOURCE_URL, PASTE_..._URL_HERE | unambiguous |

### 1.2 Language & grammar tells

**High density of "AI vocabulary" (WP:AIVOCAB)** — the page's referenced word list (each word footnoted to ≥1 study): Additionally (sentence-initial), align with, boasts (= "has"), bolstered, crucial, deep dive, delve, emphasizing, enduring, enhance, fostering, garner, highlight (verb), interplay, intricate/intricacies, key (adjective), landscape (abstract noun), meticulous/meticulously, pivotal, robust, showcase, tapestry (abstract), testament, underscore (verb), valuable, vibrant.

Era breakdown given by the page (words co-occur within an era):
- 2023–mid-2024 (GPT-4): Additionally, boasts, bolstered, crucial, delve, emphasizing, enduring, garner, intricate/intricacies, interplay, key, landscape, meticulous(ly), pivotal, underscore, tapestry, testament, valuable, vibrant
- Mid-2024–mid-2025 (GPT-4o): align with, bolstered, crucial, emphasizing, enhance, enduring, fostering, highlighting, pivotal, showcasing, underscore, vibrant
- Mid-2025+ (GPT-5): emphasizing, enhance, highlighting, showcasing + canned notability words
- Grok idiosyncrasy: causal, empirical, correlate, persistent underscore (as of 2026)
- Page's rule: one or two AI-vocab words may be coincidence; many, repeatedly, post-2022 is "one of the strongest tells". Synonyms of overused words are NOT necessarily overused — match literally.

**Avoidance of copulas (WP:AINOCOPULA)**: serves as / stands as / marks / functions as / operates as / represents a; boasts/features/maintains/offers a; "refers to" in definitions. One study: >10% drop in "is/are" usage in 2023 academic writing; GPT-3.5 revision experiment reduced is/are counts. Elaborate forms: "ventured into politics as a candidate" for "was a candidate".

**Vague connection/association (WP:AICONNECT)**: in connection with/to, connected with/to, in association with, associated with — instead of of/for/by or naming the relationship (working with, used for, caused by).

**Negative parallelisms (WP:AIPARALLEL)**: "Not just X, but also Y"; "It is not just X, it's Y"; "It's not X, it's Y"; "no X, no Y, just Z"; "This isn't X — it's Y"; reversed form "X rather than Y" (Grok-typical). Multi-sentence form: "...renowned for X. However, his life took a path that…".

**Rule of three (WP:RO3)**: adjective-adjective-adjective; short phrase ×3; triple bullet lists; used "to make superficial analyses appear more comprehensive."

### 1.3 Style/formatting tells

- Title heading repeating the document/article name at top (WP:AITITLE behavior).
- Title Case In Headings (WP:AITITLECASE).
- Headings that contain only other headings (no body text).
- Overuse of boldface, "key takeaways" bolding of every occurrence of a term (WP:AIBOLD).
- Inline-header vertical lists: "**Bold Label**: description" bullets (WP:AILIST); bullets rendered as •, -, – or emoji.
- Em-dash overuse (WP:AIDASH): spaced em dashes " — ", formulaic punched-up parallelisms; July 2026 study: of contemporary models **only Claude** still uses em dashes more than professional writers; GPT-5.1 suppressed them (Nov 2025).
- Emoji as heading/bullet decoration (WP:AIEMOJI): 🧠🧱🚨🧭📌 etc.
- Unnecessary small tables that should be prose (WP:AITABLE).
- Curly quotes/apostrophes from ChatGPT/DeepSeek (Claude and Gemini typically use straight quotes).
- Skipped heading levels; level-1 heading overuse; thematic breaks (----) between sections (Markdown import).
- Markdown-in-wikitext (WP:AIMARKDOWN): ## headings, **bold**, ```fenced blocks```, [text](url) links.

### 1.4 Machine-artifact tells (unambiguous, tool-specific)

- ChatGPT: `:contentReference[oaicite:N]{index=N}`, `oai_citation`, `citeturn0search0`, `turn0image0`, `attributableIndex` JSON, `utm_source=chatgpt.com` / `utm_source=openai` on URLs, `+1` reference artifacts.
- Gemini: `[cite: N]`, `[span_1](start_span)…(end_span)`.
- Grok: `<grok-card data-id=…>`, `grok_render_citation_card_json`, `referrer=grok.com`.
- DeepSeek: lenticular-bracket citations `【85†L261-269】`.
- Perplexity: `[attached_file:1]`, `[web:1]`, `ppl-ai-file-upload` S3 URLs.
- Copilot: `utm_source=copilot.com`.
- Unclassified: `:::writing{variant="document" id="12345"}`.
- Citation pathologies: hallucinated refs; valid-looking DOIs resolving to unrelated papers; invalid ISBN checksums; book cites with no page numbers; references declared but unused; ↩ footnote-return characters.

### 1.5 Comment/interaction tells (WP:AICOMMENT)

Made-up policy shortcuts; lengthy comments divided into titled sections; downplaying AI use ("reflects my thoughts"); "to ensure the article adheres to/aligns with Wikipedia's policies"; "Dear Editorial Team, I am writing to…"; "I hope this message finds you well"; sycophantic pivots ("You're absolutely right!"); edit summaries that are exhaustively procedural about guideline compliance.

### 1.6 Key studies cited by the page (evidence base)

- Kobak, González-Márquez, Horvát & Lause 2025, "Delving into LLM-assisted writing…", Science Advances 11(27) / arXiv:2406.07016 — excess vocabulary; ≥13.5% of 2024 PubMed abstracts LLM-processed (up to 40% in subcorpora).
- Juzek & Ward, ACL 2025 Findings, "Why Does ChatGPT 'Delve' So Much?" arXiv:2412.11385 — sources of lexical overrepresentation; RLHF implicated.
- Juzek & Ward, "Word Overuse and Alignment in LLMs: The Influence of Learning from Human Feedback", arXiv:2508.01930.
- Reinhart et al., PNAS 122(8) 2025, "Do LLMs write like humans? Variation in grammatical and rhetorical styles" — LLMs overuse present participial clauses and nominalizations; instruction-tuned models diverge more than base models.
- Russell, Karpinska & Iyyer, ACL 2025, arXiv:2501.15654 — expert humans as detectors.
- Geng & Trotta, "Human-LLM Coevolution: Evidence from Academic Writing"; also "Is ChatGPT Transforming Academics' Writing Style?"
- Huang et al., "Wikipedia in the Era of LLMs: Evolution and Risks".
- Sun, Yin, Xu, Kolter & Liu, "Idiosyncrasies in Large Language Models".
- Ju, Blix & Williams, ACL 2025 Findings, arXiv:2505.07784 — syntactic domain match.
- Kriss, Sam. "Why Does A.I. Write Like … That?" NYT Magazine, Dec 3 2025.
- Merrill, Chen & Kumer, Washington Post, Nov 13 2025, "What are the clues that ChatGPT wrote something?"
- "How to spot AI writing", The Economist, July 30 2026.
- Belcher, Wendy. "10 Ways AI Is Ruining Your Students' Writing", Chronicle of Higher Ed, Sept 16 2025.
- External directory linked: "Tropes — AI Writing Pattern Directory" and CanYouPassTheTuringTest.com.

## 2. Academic evidence: excess vocabulary and lexical overuse

### 2.1 Kobak, González-Márquez, Horvát & Lause (Science Advances 2025; arXiv:2406.07016)

Method: 15.1M PubMed abstracts 2010–2024; counterfactual expected 2024 frequency extrapolated from 2021–22; excess ratio r = observed/expected, excess gap δ = observed − expected. Data: github.com/berenslab/llm-excess-vocab (fetched; 900 excess words with annotations in results/excess_words.csv, 407 annotated "style").

Headline effect sizes (2024):
- delves: r = 28.0 (28× more frequent than expected)
- underscores: r = 13.8
- showcasing: r = 10.7
- potential: δ = 0.052 (5.2 pp excess), findings: δ = 0.041, crucial: δ = 0.037
- 2013–2019 no word ever exceeded δ > 0.01; only Covid terms did before LLMs (covid r>1000). LLM effect on writing exceeds the Covid effect (Δ 0.135 vs 0.069).
- Lower bound of LLM-assisted 2024 abstracts: 13.5%; up to Δ≈0.20 for computation/bioinformatics, China/South Korea/Taiwan; 0.25 for journal Sensors; 0.41 for computation papers from China; local t-SNE clusters ≈0.50.
- The 10-word "common marker" set (each individually high-δ): across, additionally, comprehensive, crucial, enhancing, exhibited, insights, notably, particularly, within — jointly Δ_common = 0.134.
- The "rare set": 291 style words, Δ_rare = 0.136.
- Paper found 379 style words with elevated 2024 frequencies.
- Prior work cited: Gray (2024): 2× increase for "intricate" and "meticulously" in 2023; Liang et al. (2024): top LLM-preferred words = pivotal, intricate, showcasing, realm.

Full 407-word annotated "style" list from the repo (all are LLM-associated; verbs/adjectives dominate). High-value subset for a banned/flagged lexicon (excluding words too common to flag):
accentuates, adept, akin, amidst, avenue(s), bolster(ed/ing), boasts, burgeoning, commendable, compelling, crafted/crafting, crucial, culminating, delve(d/s)/delving, discern(ible/ing), elevate(s/d), elucidate(s)/elucidating, embracing, emphasize/emphasizing, empowers, encapsulates, encompass(es/ing), endeavors, enduring, enhance(s/d)/enhancing, ensuring, escalating, excels, exceptional(ly), exhibit(ed/ing/s), expedite, exploration, facilitate(s/d)/facilitating, formidable, foster(s)/fostering, foundational, garner(ed/ing), grappling, groundbreaking, groundwork, harness(es/ing), heighten(ed), highlight(s/ing), hinges, illuminates/illuminating, imperative, impressive, innovative, insights, integrates/integrating, interconnectedness, interplay, intricate/intricacies/intricately, invaluable, juxtaposed, leverages/leveraging, meticulous(ly), multifaceted, necessitate(s)/necessitating, notable/notably, noteworthy, nuanced/nuances, orchestrating, paving, pinpoint(ed/ing), pioneering/pioneers, pivotal, poised, pressing, pronounced, propelling, realm(s), remarkable, renowned, revolutionize/revolutionizing, scrutinize(d)/scrutinizing, seamless(ly), serves, shaping, shedding (light), showcase(d/s)/showcasing, signifying, solidify, spanning, spurred, stands, strategically, streamline(d/s)/streamlining, substantial, surmount, surpass(ed/es/ing), swift(ly), transformative, uncharted, uncovering, underexplored, underscore(d/s)/underscoring, unlocking, unparalleled, unraveling, unveil(ed/ing/s), upholding, versatility, warranting.

Also flagged in the "common but excess" tier (flag only at density, not per-occurrence): across, additionally, address(es/ing), align(s/ing), alongside, both, broader, challenges, comprehensive, consequently, despite, distinct(ive), diverse, effectively, evolving, however, impact(ful), including, offering, particularly, potential, thereby, thorough, typically, ultimately, valuable, various, within.

### 2.2 Juzek & Ward, ACL Findings 2025 (arXiv:2412.11385), "Why Does ChatGPT 'Delve' So Much?"

- Identifies focal overused words via scientific-abstract comparison; attributes overuse largely to RLHF/human-feedback preference (raters mildly prefer these words), not (only) training data frequency.
- Follow-up: "Word Overuse and Alignment in LLMs: The Influence of Learning from Human Feedback" (arXiv:2508.01930) — cited by Wikipedia for "meticulous/meticulously".

### 2.3 Reinhart et al., PNAS 2025 — grammatical/rhetorical divergence

"Do LLMs write like humans?" (PNAS 122(8), doi:10.1073/pnas.2422455122): instruction-tuned LLMs overuse present participial clauses and nominalizations relative to human text across genres; the divergence increased with instruction tuning. This is the academic backing for the "-ing clause tacked on the sentence end" tell.

### 2.4 Related evidence stream (from WP:AISIGNS reference list; not all fetched)

- Russell/Karpinska/Iyyer ACL 2025 (arXiv:2501.15654): expert LLM users detect AI text ~90%; naive readers ≈ chance.
- Yakura et al. arXiv:2409.01754: LLM vocabulary leaking into human *spoken* language (podcasts) — tells will decay.
- Geng et al. ACL 2025 Findings: LLM impact on academic writing and speaking.
- Kousha & Thelwall, ISSI 2025 (arXiv:2509.09596): multi-database, full-text analysis of LLM language change.
- Ju, Blix & Williams (arXiv:2505.07784): LLM-regenerated text fails to match syntactic properties of the original domain.

## 3. Structural and tonal tells (cross-source synthesis)

Each entry: tell → why it reads as AI → fix. Sources: WP:AISIGNS (§1), Reinhart PNAS 2025, Rettberg 2026, antislop corpus (§7).

### Structure
1. **Bullet-point inflation** — prose that should be sentences rendered as "**Bold Label**: text" bullets; ordered lists with explicit "1." numbering; bullets used to fake comprehensiveness. Fix: default to prose; use a list only when items are truly parallel and >3.
2. **Header spam** — a heading per 1–2 paragraphs; Title Case Headings; headings that contain only other headings; a title heading restating the document name; "X and Y" headers ("Awards and recognition", "Challenges and Legacy"). Fix: headings only where a reader would scan for them.
3. **Summary sandwich** — intro that previews ("In this section we will…"), body, then "In conclusion/Overall/Key takeaways" recap that adds nothing. Fix: cut both slices; keep the filling.
4. **Outline-rigid endings** — "Despite these challenges… future prospects" formula; vaguely positive final assessment; speculation about ongoing initiatives. Fix: end on the last fact.
5. **Rule of three** — triadic adjectives/phrases/clauses everywhere ("bad weather, high tariffs and climbing transportation costs" — Rettberg notes each "perfectly balanced with an adjective and a noun, like AI-generated crowd photos where all the people look like clones"). Fix: vary list lengths; one strong item beats three padded ones.
6. **Uniform paragraph rhythm** — near-equal paragraph lengths, near-equal sentence lengths (low burstiness). Human text mixes 4-word and 40-word sentences. Fix: vary deliberately; allow fragments.
7. **Thematic-break litter** — `---` between every section (Markdown habit).
8. **Emoji headers/bullets** — 🚀 ✅ 📌 decoration.
9. **Unnecessary mini-tables** for 3 facts that belong in a sentence.
10. **Sentence-final participial clause** — ", highlighting/underscoring/reflecting/ensuring/contributing to…" bolted onto a factual sentence (Reinhart: LLMs measurably overuse present participial clauses; also nominalizations). Fix: delete the clause or make the claim a sentence with an agent.

### Tone
11. **Sycophantic openers** — "Great question!", "You're absolutely right!", "Certainly!", "I'd be happy to…". Fix: start with the answer.
12. **Hedging closers** — "I hope this helps", "Let me know if…", "Feel free to…", "Would you like me to…". Fix: end when done.
13. **Contrastive inflation ("not just X, but Y")** — negative parallelism family: "not only X but also Y", "It's not X — it's Y", "no X, no Y, just Z", "X rather than Y" (Grok-flavored). Reads as clearing up a misconception nobody had. Fix: make one claim at a time; assert Y directly.
14. **False balance / both-sidesing** — "While X has critics, supporters argue…", "It could be argued that…" with no named arguer; presenting one source's view as "widely held"; "Experts argue", "Observers have cited". Fix: attribute or delete.
15. **Importance inflation** — grading significance instead of stating mechanism: "plays a crucial/pivotal/vital role", "marks a significant shift", "key turning point", "underscores the importance of". Fix: name what it does, not how important it is.
16. **Hedging sprinkle** — arguably, somewhat, tend to, may or may not, to some extent, generally speaking — uncertainty smeared instead of stated once with a reason.
17. **Self-narration / process talk** — "Let's dive in", "Without further ado", "As mentioned above", "In this report we will".
18. **Em-dash overuse** — spaced " — " pairs punching up parallelisms. As of the July 2026 study cited by Wikipedia, **Claude is the only major model still above professional-writer em-dash rates** — a Claude-specific severity bump.
19. **Genre glitch (Rettberg 2026)** — sudden register switch: promotional/sensory phrase inside informational text ("tart bursts of flavor in salads and sandwiches" mid-inflation-story; "a route famous for its scenic views" in a legal memo). Fix: every clause must serve the document's genre.
20. **Weasel quantities** — "several sources", "many experts", "widely regarded" with ≤1 citation.
21. **Copula avoidance** — "serves as", "stands as", "functions as", "represents a", "boasts", "features", "offers" where "is/has" is meant; "refers to" in definitions. Backed by a measured >10% drop of is/are in 2023 academic text.
22. **Vague association** — "associated with", "in connection with" instead of naming the relation (of/for/by/caused by/used in).
23. **Superficial-competence sheen** — the AI-slop signature per Kommers et al. 2026 (cited in Wikipedia's AI slop article): "superficial competence, asymmetric effort and mass producibility." Fluent, structured, empty.

### Context from the AI slop article (en.wikipedia.org/wiki/AI_slop)
- "Slop" = generative content "lacking in effort, quality, or meaning… produced in high volume"; pejorative like "spam"; 2025 Word of the Year for Merriam-Webster and the American Dialect Society; term mainstreamed by Simon Willison (May 2024).

## 4. Claude-specific tells and the user-banned family

Documented Claude-specific facts (from WP:AISIGNS): Claude uses straight quotes (not curly); Claude is the last major model overusing em dashes (July 2026 study); Claude's system prompt historically enforced tidy Markdown (headers, nested bullets) — so heavy, well-formed Markdown is a Claude fingerprint.

Owner-banned terms (already in corpus/banned-phrases.yaml): load-bearing, spine in a line / the spine, the honest assessment/take, sharpest part, crisp.

Analysis of the family: these are all **structure-as-body metaphors and self-congratulatory editorial framing** — Claude describing its own prose's anatomy and virtue instead of the subject. Extension candidates (same generator, proposed severities):

Structure-as-anatomy metaphors:
- "the backbone (of)" — warn — same organ as "the spine"
- "the connective tissue" — error
- "the skeleton / skeletal structure (of the argument)" — warn
- "the beating heart of" — error
- "muscle" as praise ("gives the argument muscle") — warn
- "the scaffolding" — warn
- "load-bearing wall" and any "what's load-bearing here" variants — error (already banned root)
- "does the heavy lifting" — warn — same anatomical-effort family
- "the through-line" — warn — spine's cousin
- "the connective thread / the thread that runs through" — warn

Self-grading editorial frames (announcing quality instead of exhibiting it):
- "the honest answer/read/version" — error (extends banned pattern)
- "if I'm being honest / to be blunt / frankly" as prefix — warn
- "the real question/story/work is" — warn
- "the key insight (here) is" — warn
- "here's the thing" — warn
- "the short version:" / "the TL;DR:" as rhetorical throat-clearing — warn
- "what actually matters (here)" — warn
- "the sharpest edge / the sharpest version of this" — error (extends banned pattern)
- "a sharper way to say this" — warn
- "tight/tighter" as prose praise ("a tighter framing") — warn — sibling of "crisp"
- "clean/cleaner" as prose praise ("a cleaner way to put it") — warn
- "punchy/punchier" — warn
- "this lands / doesn't land" — warn
- "does a lot of work (in this sentence)" — warn — cousin of load-bearing
- "carries the weight" — warn
- "earns its place / earns the reader's trust" — warn

Claude conversational reflexes (chat voice leaking into documents):
- "You're absolutely right" — error (WP:CERTAINLY lists it verbatim)
- "Great catch!" / "Good catch" — warn
- "I appreciate you (pointing that out)" — warn
- "Let me be direct/clear" — warn
- "To be fair," — warn
- "That said," as universal pivot — warn (density-based)
- "importantly," / "crucially," / "critically," sentence adverbs — warn
- "genuinely" as intensifier — warn
- "deeply" as intensifier ("deeply rooted", "deeply personal") — warn
- "quietly" as drama ("quietly one of the most important…") — warn
- "arguably the most" — warn
- "in many ways" — warn
- "at its core" — warn
- "fundamentally," sentence-initial — warn
- "the way I'd think about this is" — warn

## 5. Humanizer / de-AI tools — classification

Respeak's translator is STYLE-focused: it edits for human legibility. Tools whose value proposition is beating detectors are DETECTION-EVASION and out of scope (they optimize against classifiers, not for readers; WP:AIDETECTION notes detectors are fragile to exactly these paraphrase attacks).

### DETECTION-EVASION (out of scope; noted and excluded)
- **Undetectable.ai** — verified tagline: "Detect AI content, humanize your writing" — paraphraser whose selling point is passing detectors.
- **WriteHuman.ai** — verified tagline: "Works with Copyleaks, ZeroGPT, and GPTZero" — explicitly detector-targeted.
- **StealthGPT** — verified tagline: "humanizes AI content with a 99% AI-detection bypass rate."
- Same category by market positioning (not fetched; classify identically): BypassGPT, HIX Bypass, Humbot, Phrasly.ai, Netus.ai, Twixify, Walter Writes AI, AIHumanizer.ai, Smodin "AI detection remover". QuillBot's "AI Humanizer" (Cloudflare-blocked on fetch) sits in the same lane; QuillBot's core paraphraser is a gray area.
- Research context: RAID benchmark (arXiv:2405.07940) shows paraphrase attacks degrade all detectors — which is why these tools "work" and why respeak should never cite detector scores as ground truth.

### STYLE-focused (legitimate editing; respeak-aligned)
- **AntiSlop sampler** (github.com/sam-paech/antislop-sampler) — inference-time backtracking that downweights a configurable slop-phrase list, incl. regex bans for "not x, but y"; adopted by koboldcpp v1.76. This is the closest existing mechanism to respeak's banned-phrases.yaml enforced at generation time.
- **Slop Forensics** (github.com/sam-paech/slop-forensics) — builds canonical slop lists from over-represented words/bigrams/trigrams across models; produces per-model "slop profiles". Methodology respeak could reuse to audit its own swarm's output.
- **Hemingway Editor / ProWritingAid / classic style linters** — human-legibility editing (sentence length, adverbs, passive voice); no evasion claim.
- **Vale / write-good / proselint** — open-source prose linters accepting custom rule files; natural enforcement backends for banned-phrases.yaml.
- **Wikipedia's WikiProject AI Cleanup + WP:AISIGNS** — human editorial checklist, the purest style-side resource.
- Detectors (GPTZero, Pangram, Copyleaks) are neither: they are measurement tools with "non-trivial error rates" (WP:AIDETECTION); do not gate respeak output on them.

## 6. Editorial guidance from human editors on fixing AI prose

Distilled from WP:AISIGNS editing practice, Rettberg, and the studies above:
1. **Cut the frame, keep the fact.** Delete significance claims ("marking a pivotal moment") and keep the verifiable event. Wikipedia editors fixing AI text overwhelmingly delete, not rephrase, the puffery.
2. **Restore the copula.** "serves as the exhibition arm" → "is the exhibition space". "boasts 8 tracks" → "has 8 tracks".
3. **Chop sentence-final participles.** "…was established in 1989, marking a pivotal moment…" → end the sentence at the fact.
4. **Name the relation.** "associated with water management applications" → "used for pool backwash".
5. **De-triple.** Replace balanced triads with the one or two items that carry information.
6. **Attribute or delete opinions.** "Experts argue" → "[Named person] argues, in [source]" or cut.
7. **One hedge, with a reason.** Replace scattered "arguably/somewhat/may" with a single stated uncertainty and its cause.
8. **Match the genre everywhere** (anti-genre-glitch): no sensory/promotional inserts in technical or status text.
9. **Vary rhythm.** Break uniform paragraph/sentence lengths; allow short sentences.
10. **Kill the sandwich.** No "In this document we will"; no "In conclusion" recap of a one-screen text.
11. **Specificity is the strongest anti-tell.** The Wikipedia page's core diagnosis: AI text is "simultaneously less specific and more exaggerated." Concrete numbers, names, and failure modes read human; graded importance reads machine.
12. **Don't chase detectors.** Humans who use LLMs heavily detect at ~90% via the tells above; casual readers at chance. Write for the expert reader's tells, not for GPTZero.

## 7. The antislop corpus (517 phrases, fetched) — families relevant to respeak

Source: slop_phrase_prob_adjustments.json in sam-paech/antislop-sampler (auto-generated from over-represented words in LLM story datasets; author warns it is uncurated). Families:

**Expository slop (overlaps §1–2, corroborates):** delve/delving/delved, tapestry/tapestries, testament to, symphony, kaleidoscope, weave/wove/weaving, bustling, labyrinthine, nestled, transcended, meticulous(ly), navigating, complexities, realm, dive into, tailored, underpins, everchanging, ever-evolving, not only, embark, journey, "today's digital age", game changer, "designed to enhance", "it is advisable", daunting, "when it comes to", "in the realm of", "unlock the secrets", "unveil the secrets", elevate, unleash, cutting-edge, mastering, harness, "it's important to note", "in summary", "remember that", landscape, "in the world of", vibrant, metropolis, moreover, crucial, furthermore, vital, "as a professional", thus, "you may want to", "on the other hand", "as previously mentioned", "it's worth noting that", "to summarize", "to put it simply", "in today's digital era", revolutionize, indelible, "in conclusion", "it's essential to", "there are a few considerations", fostering, interconnectedness, amidst, newfound, resilience, adversity, inclusivity, adaptability, perseverance, resourcefulness, camaraderie, palpable, cacophony, piqued, serendipitous, unbeknownst, firsthand, wholeheartedly, tirelessly.

**Narrative slop (for any storytelling/ELI5 mode):** "barely above a whisper", "shivers down/up the spine", "eyes sparkling with mischief", "practiced ease", "moth to a flame", "cold and calculating", "eyes never leaving", "body and soul", "chuckles darkly", "for now, that was enough", "maybe, just maybe", "little did he know", "life would never be the same", "for what seemed like an eternity", "air was filled with anticipation", "bore silent witness to", "reckless abandon", "torn between", "humble abode", "ethereal beauty", "once upon a time", "nestled deep within", "only just getting started", "ready for the challenges", "they would face it together", thrummed, flickered, rasped, glinting, twinkled, gossamer, rivulets, ministrations.

**LLM default-name tell (novel category):** Elara, Elysia, Lyra, Eira, Eldoria, Atheria, Oakhaven, Whisperwood, Zephyria, Ravenswood, Kael, Jaxon, Elias — stock invented names; respeak examples/analogies should avoid the stock-name basin (also Sarah/Emily/Alex/Maya as default persona names).

**Dialogue-tag slop:** chimed, interjected, sighed, warmly, thoughtfully, intently, excitedly, hesitantly, gruffly, sagely, conspiratorially, mischievously, quizzically, reassuringly.

