# Communication Best Practices: Enforceable Writing Rules for respeak

Research distillation of communication books and plain-language standards into
checkable rules (lintable or LLM-judge-enforceable), mapped onto respeak's three
translator modes (ELI5, BLUF/manager, technical).

Date: 2026-08-31

## 1. plainlanguage.gov Federal Plain Language Guidelines

Source: original guidelines archived in the GSA/plainlanguage.gov GitHub repo
(`_pages/guidelines/`); current maintained version at digital.gov's Plain
Language guide series. The Plain Writing Act of 2010 makes these legally
required for US federal public content.

Enforceable rules (each is lintable or judge-checkable):

1. **One idea per sentence.** "Express only one idea in each sentence." Check: no sentence contains two independent clauses joined by "and/but/so" carrying separate claims.
2. **Short paragraphs: ≤150 words, 3–8 sentences; hard cap 250 words; one topic per paragraph.** Occasional one-sentence paragraphs are fine; vary lengths.
3. **Active voice.** "Passive voice obscures who handles what and is one of the biggest problems with government writing." Detector: form of "to be" + past participle. Passive allowed only when the actor is unknown/irrelevant.
4. **Present tense by default.** "Use tenses other than the present only when necessary for accuracy."
5. **No hidden verbs (nominalizations).** Flag nouns ending in -ment, -tion, -sion, -ance, and "the X of" constructions; rewrite as verbs ("conduct an analysis of" → "analyze").
6. **Keep subject, verb, and object adjacent.** No modifier clauses inserted between subject and verb or verb and object; move them to another sentence or the end.
7. **Main idea before exceptions and conditions.** Never open a sentence with "Except as...". State the rule, then the exception ("However, see X for an exception").
8. **Positive form; ban double negatives.** Flag pairs like "no fewer than" (→ "at least"), "has not yet attained" (→ "is under"), "is not ... unless" (→ "is ... only if").
9. **No noun strings longer than three nouns.** "Once you get past three, the string becomes unbearable." Unpack with prepositions/articles.
10. **Minimize abbreviations; prefer nicknames.** "The committee" instead of "ESAC". Use undefined abbreviations only from the short common-usage list.
11. **Same term = same concept, always.** "You don't need synonyms to make your writing more interesting... it can decrease clarity." (Directly supports respeak's ratified-lexicon idea.)
12. **Simple word substitutions** (word-pair table with ~200 entries): commence→begin, utilize→use, ascertain→find out, in close proximity→near, at the present time→now, afford an opportunity→allow, a number of→some, due to the fact that→since. Lintable as a replacement dictionary.
13. **Topic sentence first in every paragraph.** "Readers should be able to get a good general understanding of your document by skimming your topic sentences."
14. **Address the reader as "you."** "More than any other single technique, using 'you' pulls users into the information."
15. **"Must" for requirements** — not "shall" (ambiguous), not slashes ("and/or" banned).

## 2. ASD-STE100 Simplified Technical English (Issue 9, Jan 2025)

Source: asd-ste100.org (official STEMG site) + Wikipedia "Simplified Technical
English". A controlled natural language: **53 writing rules + a dictionary of
~900 approved words**. Core principle: "One word, one part of speech, one
meaning." Now an international standard; free official copy on request.

Enforceable rules:

1. **Sentence length caps: ≤20 words in procedures/instructions; ≤25 words in descriptive text.** The single most lintable rule in this whole corpus.
2. **One instruction per sentence.**
3. **One topic per paragraph; ≤6 sentences per paragraph.**
4. **Approved words only, used only in the approved part of speech and meaning.** E.g., "test" is approved only as a noun; "close" (v) only for physical closing or circuits — never "close a meeting."
5. **No multi-word noun clusters over three words.**
6. **Only simple verb forms:** infinitive, imperative, simple present/past/future, past participle as adjective only. No complex auxiliary constructions ("would have been removed").
7. **"-ing" verb forms only as technical nouns or noun modifiers** — no progressive tenses, no gerund-led clauses.
8. **Active voice in procedures always; in descriptions, passive only when the agent is unknown.**
9. **Never omit sentence parts (verb, subject, article) to save space.** Compression must not create telegraphese — directly relevant to respeak's shorthand legibility floor.
10. **Vertical lists for complex text.**
11. **Safety instructions start with a clear command or condition.**
12. Domain-specific technical nouns/verbs (e.g., "propeller," "to ream") are allowed even if not in the dictionary — controlled vocab plus a domain lexicon, exactly respeak's lexicon model.

Cautionary finding: STE is often misapplied as a full style guide, producing
"grammatically incorrect application of STE-approved words." ASD's own
disclaimer: "Can STE be used alone? No." And on checkers: "if authors rely
blindly on what checkers tell them, they are likely to write rubbish." Lesson
for respeak: lint rules gate, but an LLM judge (or human) still owns meaning.
Existing STE checkers to note: Boeing Simplified English Checker (350-rule
parser), HyperSTE (Etteplan), Congree STE Checker, TechScribe term checker.

## 3. BLUF — Bottom Line Up Front

Source: Wikipedia "BLUF (communication)". Origin: US Army Regulation 25-50,
*Preparing and Managing Correspondence*: "Army writing will be concise,
organized, and to the point. Two essential requirements include putting the
main point at the beginning of the correspondence (bottom line up front) and
using the active voice." Deductive (conclusion-first) presentation, like
journalism's inverted pyramid; simpler and more concise than an executive
summary — "similar to a thesis statement."

Enforceable rules:

1. **The first sentence states the decision/result/ask — the bottom line.** Everything else follows it.
2. **The BLUF names what the receiver must do and by when** (the canonical example: "I need you to approve both the design and content of the attached flyer by noon on August 10").
3. **After the bottom line: essential background only** — the considerations that led to it, in decreasing order of importance.
4. **Answer the question asked** (Mattis 2017 DoD guidance): "Do not avoid the question or answer a different question. If you can't answer the question or address the issue, state why."
5. **Active voice throughout** (paired with BLUF in AR 25-50 itself).
6. Judge check: delete everything after sentence one — does the reader still know the outcome and what's expected of them? If not, it's not a BLUF.
## 4. Minto Pyramid Principle (Barbara Minto)

Sources: Wikipedia "Barbara Minto"; untools.co/minto-pyramid. Minto (first
female MBA McKinsey hired, 1963; *The Pyramid Principle*, 1985/1996) invented
MECE and the pyramid: "ideas ... organized top-down, starting with a main idea
that is a high-level summary of supporting key ideas, each of which is derived
from further supporting sub-points." "Humans naturally impose this kind of
hierarchy on information we receive."

Enforceable rules:

1. **Lead with the conclusion** (= BLUF). "Lead with the conclusion, then provide key arguments and finally support them with detailed information" (untools).
2. **Exactly three layers:** conclusion → key points (the "why", as one-line summaries) → supporting detail (facts, evidence, numbers). Detail is skippable: "They only need to consume the details if they choose to, not in order to get to the main point."
3. **Groupings must be MECE** — mutually exclusive, collectively exhaustive. Judge check: do any two sibling points overlap? Does an obvious sibling go unmentioned?
4. **Every grouping must summarize to a single idea.** "You can't derive an idea from a grouping unless the ideas in the grouping are logically the same, and in logical order" (Minto). Headings/bullets that are just topic labels ("Background", "Other issues") fail.
5. **SCQA opening** (Minto's narrative intro, standard framework from the book): Situation (uncontested context) → Complication (what changed/broke) → Question (raised in the reader's mind) → Answer (your main point). In BLUF-style docs the Answer moves to sentence one and S-C compress to a clause.
6. Judge check: read only the top-level statements — they must form a complete, coherent argument on their own.

## 5. Simply Said (Jay Sullivan / Exec-Comm, Wiley 2017)

Source: exec-comm.com product page + book (standard framework). Exec-Comm's
core philosophy, verbatim from their site: "we are all more effective
communicators when we focus less on ourselves and more on others." The book's
organizing idea: audience focus — "it's not about you."

Enforceable rules (book framework; checkable formulations ours):

1. **One-sentence core message, ≤10 words, no "and"/comma splices.** If you can't state the message in one short sentence, you don't have one yet. Check: ask for the message sentence; count words and conjunctions.
2. **Audience-benefit orientation: the message names what it means to *them*, not what you did.** Lint proxy: in openings, second-person ("you/your") should outnumber first-person ("I/we/my/our"). Openings that start "I" fail.
3. **Short sentences, one idea each.** Sullivan's guidance aligns with the plain-language ~15–20 word target.
4. **Active voice, plain words.** No jargon the audience hasn't already used themselves.
5. **Answer the question first, then explain** — when asked something, respond with the answer, not the history.
6. **Cut throat-clearing:** no warm-up sentences before the point ("I just wanted to touch base...", "As you may know...").
7. **"So what" test on every paragraph:** each paragraph must state or clearly imply the implication for the reader.
8. **Prefer concrete verbs and nouns over abstractions;** delete intensifiers ("very", "really", "extremely") — they weaken, not strengthen.
9. **In documents: state purpose in the first sentence; one page when possible; white space and headers are part of the message.**
10. Judge check: could the reader repeat your main point after one reading? If the main point lives in the middle of a paragraph, it fails.

## 6. Radical Candor (Kim Scott)

Sources: radicalcandor.com "What is Radical Candor?" + radicalcandor.com/glossary.
Definition: "saying what you think while also giving a damn about the person
you're saying it to" — feedback that is **"kind, clear, specific and sincere."**
2x2: Care Personally × Challenge Directly →
- **Radical Candor** (high/high, the goal)
- **Obnoxious Aggression** (challenge without care — "front stabbing"; "praise that doesn't feel sincere or criticism ... [not] delivered kindly")
- **Ruinous Empathy** (care without challenge — "praise that isn't specific enough to help the person understand what was good or criticism that is sugar-coated and unclear. Or simply silence." "Most managers default to Ruinous Empathy.")
- **Manipulative Insincerity** (neither — flattery to the face, criticism behind the back)

**CORE model** (glossary, verbatim expansion): "Context — the situation in
which the behavior occurred; Observation — the specific behavior observed;
Result — the impact or outcome of that behavior; Explore — an invitation for
dialogue about next steps." (Extends CCL's SBI: Situation-Behavior-Impact.
Note: some editions gloss the E as "nExt stEps"; the official glossary says
Explore.)

**HHIPP** principles of guidance (glossary, verbatim): "Humble — deliver
feedback in a way that acknowledges you may be wrong; Helpful — state your
intention to help and show specifically what is good or bad; Immediate — say
it right away in 2–3 minutes rather than scheduling a later meeting; In Person;
Private — criticize in private, praise in public; not Personalized — address
behavior and its impact, never character or identity."

Enforceable rules for generated text (status reports, reviews, feedback):

1. **Every criticism must contain all four CORE parts:** the context, the observed behavior/fact, the concrete result, and a next step or open question. A criticism missing the Result or nExt-stEp fails.
2. **Praise must be specific:** cite the exact thing and why it worked. Ban bare "great job", "nice work", "looks good" — that is Ruinous Empathy by definition.
3. **Criticize the work, never the person:** flag second-person + character adjectives ("you are careless") vs. behavior statements ("the test was skipped in commit X, which broke Y").
4. **No sugar-coating and no sandwich:** the critical point may not be buried after praise; state it directly, kindly.
5. **Humility marker, once:** state uncertainty explicitly and precisely ("I may be missing context on X") rather than diffuse hedging throughout.
6. **Sincerity ban-list:** no flattery, no "as you know better than I...", no insincere qualifiers. (Maps to respeak's no_pleasantries.)
7. Judge check per feedback item: is it kind, clear, specific, AND sincere? All four or rewrite.

## 7. Crucial Conversations (Patterson, Grenny, McMillan, Switzler)

Sources: cruciallearning.com book-resources page, Crucial Conversations for
Dialogue course page (lesson list fetched), Wikipedia article; STATE/pool
terminology from the book (standard framework). A crucial conversation = high
stakes + opposing opinions + strong emotions. Goal: keep information flowing
into the "pool of shared meaning" — the bigger the shared pool, the better the
decision.

Course skill sequence (fetched verbatim from lesson list): Get Unstuck →
Master My Stories ("take responsibility for the emotions you bring ... by
owning your story") → Start With Heart ("stay focused on what you really
want") → **State My Path ("speak honestly and respectfully; share tough
messages in a way that invites others into the conversation")** → Make It Safe
("take steps to rebuild safety when others get defensive") → Learn to Look →
Seek Mutual Purpose ("find common ground even when it seems impossible") →
Explore Others' Paths → Move to Action.

**STATE** (book): Share your facts; Tell your story; Ask for others' paths;
Talk tentatively; Encourage testing.

Enforceable rules for generated text:

1. **Facts before stories.** Lead with observable, verifiable data (file:line, log output, measurements) before any interpretation. Check: the first evidence-bearing sentence contains a fact, not a conclusion-word ("clearly", "obviously", "sloppy").
2. **Label interpretations as interpretations.** Conclusions drawn from facts get tentative framing: "this suggests", "my read is". Ban stating a story as a fact.
3. **Contrasting statements for correction-prone messages:** the don't/do pair — "I don't mean X; I do mean Y." Use when a message could be misread as blame or as bigger/smaller than intended. Checkable pattern: negation-of-misreading + assertion-of-meaning.
4. **Talk tentatively without being weak:** one precise softener on opinions ("In my view..."), never on facts. Facts get zero hedges.
5. **Encourage testing:** high-stakes claims end with an invitation to disagree or a falsifiable check ("If the metric doesn't drop by Friday, I'm wrong").
6. **Mutual purpose stated up front in disagreements:** one sentence naming the shared goal before the disagreement.
7. **No "violence or silence":** no sarcasm, labeling, or absolutes ("always", "never" about people); and no withholding — every known material risk must appear in the text (silence check is a completeness judge, not a linter).
8. **Move to Action ending:** who does what by when, and how follow-up happens. A crucial message without an owner+deadline fails.
## 8. GOV.UK Style Guide (A-to-Z of GOV.UK style)

Source: gov.uk/guidance/style-guide/a-to-z-of-gov-uk-style (fetched).
"Plain English is mandatory for all of GOV.UK." (GOV.UK's companion content
guidance targets a reading age of ~9 and sentences of ~25 words max; the A-to-Z
carries the enforceable entries below.)

Enforceable rules:

1. **Words-to-avoid ban list** (verbatim selections; each has a prescribed replacement): agenda→plan, collaborate→work with, commit/pledge→"plan to x", deliver→make/create/provide ("pizzas, post and services are delivered — not abstract concepts like improvements"), deploy (unless military or software)→use, dialogue→discussion, empower→allow, facilitate→(say specifically how), foster→encourage/help, impact (unless collision)→have an effect on, incentivise→encourage, initiate→start, key (unless it unlocks something)→important, leverage (unless financial)→influence/use, liaise→work with, overarching→(delete), robust (unless a sturdy object)→well thought out/comprehensive, streamline→simplify, tackle→stop/solve/deal with, transform→(describe the actual change), utilise→use.
2. **Anti-metaphor rule:** "Avoid using metaphors — they do not say what you actually mean and lead to slower comprehension." Banned: drive (non-vehicle), drive out, going/moving forward→"from now on", in order to→(delete), hub/portal/one-stop shop→website/service, ring fencing→separate.
3. **Active voice** ("This will help us write concise, clear content").
4. **Front-load sentences** — main information first, in sentences as well as pages.
5. **Explain each abbreviation at first use, then initials only** — except a short well-known list (BBC, EU, etc.). No full stops in abbreviations (BBC, not B.B.C.).
6. **No negative contractions:** "Use cannot, instead of can't" — "many users ... misread them as the opposite of what they say." No complex contractions (should've).
7. **Sentence case everywhere,** including titles; capitals only for proper nouns.
8. **Bullet discipline:** always a lead-in line; ≥2 bullets; bullets read on from the lead-in; lower-case start; **max one sentence per bullet**; no "and"/"or" after bullets; no trailing semicolons/full stops.
9. **Numbered steps (not bullets) for processes;** each step a complete sentence ending in a full stop.
10. **Bold only for UI elements the user must act on** — "Do not use bold ... to emphasise text."
11. **No brackets for singular/plural "document(s)"** — always use the plural.
12. **Legal content still in plain English;** if legal jargon must appear, add a plain-English summary; explain any needed legal term.

## 9. Everyone Communicates, Few Connect (John C. Maxwell, 2010)

Sources: sobrief.com summary (fetched); five-principles/five-practices
structure from the book (standard framework). Core claim: "More than 90
percent of the impression we often convey has nothing to do with what we
actually say" — connection over transmission. "People don't care how much you
know until they know how much you care."

Connecting Principles (book): connecting increases influence; connecting is
all about others; connecting goes beyond words; connecting requires energy;
connecting is more skill than talent. Connecting Practices: find common
ground; keep it simple ("To be simple is to be great"); capture interest /
create an experience; inspire; live what you communicate.

Four components of connection — people must: **see** something (visual
conviction), **understand** something (intellectual content), **feel**
something (emotional resonance), **hear** something (words/tone).

Least lintable source in this set; the checkable residue:

1. **Common-ground opener:** the first paragraph must reference something the reader already knows/cares about (their system, their metric, their last question) — not the writer's activity.
2. **Simplicity as a hard constraint:** "Simplify your message to its core; complexity signals confusion" (sobrief). Enforce via the one-sentence core message + reading-level caps from other sources.
3. **Others-centered pronoun ratio** (same lint as Simply Said rule 2).
4. **Understand + feel + do:** a narrative must contain a comprehension payload (what happened), a stakes payload (why it matters to the reader), and an action payload (what to do). Judge check: can all three be extracted?
5. **Credibility check:** never claim what the evidence doesn't show — inflated claims destroy connection ("trust is the prerequisite for persuasion").
6. Anti-rule worth noting: Maxwell's "capture interest / inspire" pulls toward energy-words and metaphor — exactly what GOV.UK bans. respeak should resolve this: interest comes from relevance and concreteness (Maxwell's common ground), never from hype vocabulary.
## 10. Combined Rule Set Mapped to respeak's Three Modes

Universal (all modes — belongs in style/ hard constraints):
- U1. First sentence carries the main point (BLUF/Minto/plainlanguage topic-sentence). No preamble, no throat-clearing.
- U2. One idea per sentence; subject-verb-object adjacent; no noun strings >3 nouns.
- U3. Active voice ≥0.8 of sentences (config already has this; STE says 100% in procedures — see per-mode below).
- U4. Present tense by default.
- U5. No nominalizations ("conduct an analysis" → "analyze") — lintable via -tion/-ment/-ance + "the X of" patterns.
- U6. No double negatives; positive form; no negative contractions (cannot, not can't).
- U7. Same term = same concept; the ratified lexicon is the single source of naming (plainlanguage consistency rule + STE one-word-one-meaning).
- U8. Facts before stories; interpretations labeled; hedges: zero on facts, at most one precise uncertainty statement per message (Crucial Conversations + config confidence axis).
- U9. Main idea before exceptions; never open with "Except...".
- U10. Word ban lists: GOV.UK words-to-avoid + plainlanguage simple-word table → corpus/banned-phrases.yaml and corpus/replacements.yaml.
- U11. Vague-praise ban in any evaluative text: "great job", "looks good", "nice work" without a specific referent (Radical Candor).
- U12. Answer the question asked; if you can't, say why (Mattis/BLUF).
- U13. Criticism carries CORE: context, observation (fact), result, next step/question. Behavior, never character.
- U14. Every actionable message ends with owner + deadline or an explicit "no action needed" (Crucial Conversations Move to Action + BLUF ask).

Per mode:

**ELI5** (tech_level 1, grade6, ≤15 words/sentence, ≤150 words):
- Common-ground opener mandatory (Maxwell): anchor in something the reader knows.
- Second person "you" (plainlanguage address-the-user); contractions allowed EXCEPT negative ones.
- Zero undefined abbreviations and zero lexicon shorthand — full expansion always.
- One analogy max (config already says this; GOV.UK would say zero metaphors — keep the paid-for single analogy but require it to be closed: say what it maps to).
- Understand/feel/do triple present (Maxwell): what happened, why the reader cares, what happens next.
- No parenthetical asides; no "(s)" plural hedges.

**BLUF/manager** (tech_level 2, grade9, ≤20 words/sentence, ≤200 words):
- Sentence 1 = decision/result/ask with owner and deadline (AR 25-50 + Minto Answer). Delete-test: sentence 1 alone must carry the outcome.
- Then impact ("what it means to them" — Simply Said), then supporting facts grouped MECE, in decreasing importance (inverted pyramid).
- Key points as one-line summaries; details linkable/skippable (Minto layer 3).
- No metaphors at all (GOV.UK); no hype vocabulary (leverage, robust, transform...).
- Bullets: lead-in line, ≥2, one sentence max each (GOV.UK).
- SCQA compressed: situation-complication as at most one clause, never a paragraph of background ("no background preamble" — config already right).

**Technical** (tech_level 4, ≤28 words/sentence, ≤500 words):
- Finding-first (config) = Minto conclusion-first; then evidence with file:line (facts before stories); then open questions with an explicit test/invitation to falsify (Encourage testing).
- STE discipline for any procedural/instruction content embedded in the narrative: ≤20 words/sentence for steps, one instruction per sentence, imperative mood, numbered steps not bullets, safety/caution lines first.
- Descriptive text cap should be 25 words (STE), not 28 — see critique below.
- Abbreviations: lexicon-ratified terms allowed without expansion (reader = working engineer); anything else expanded at first use.
- Passive allowed only when the agent is unknown/irrelevant (STE descriptive rule).
- Never omit verbs/subjects/articles for brevity (STE) — compression belongs to the shorthand lane, never the narrative lane.

### Critique of config/respeak.config.yaml mode parameters

1. **Sentence caps are well-chosen but technical=28 is above every standard.** STE caps descriptive text at 25. Recommend `max_sentence_words: 25` for technical, and a separate `max_step_words: 20` for procedural lines in any mode (STE's procedures/descriptive split is more useful than a single cap).
2. **Missing paragraph parameters.** plainlanguage: ≤150 words and 3–8 sentences per paragraph (hard 250); STE: ≤6 sentences. Add `max_paragraph_sentences: 6` (technical), and for eli5 `structure: single-explanation` already implies one paragraph — make it explicit (`max_paragraphs: 1`).
3. **active_voice_min: 0.8 is right globally but wrong for procedures.** STE requires 100% active/imperative in instructions. Add a per-structure override: `procedural: active_voice_min: 1.0`.
4. **No pronoun-orientation parameter.** Simply Said/Maxwell/plainlanguage converge on reader-address. Add `address_reader: true` for eli5/bluf (lint: "you" count ≥ "I/we" count in the first two sentences).
5. **bluf mode lacks the ask contract.** structure comment says "decision/result/ask" — make it checkable: `require_ask: {owner: true, deadline: true}` with an allowed explicit "FYI only — no action needed".
6. **one_metaphor_max conflicts with GOV.UK zero-metaphor guidance.** Keep 1 for eli5 (analogy is the teaching tool), set 0 for bluf and technical. The current global "one metaphor is a loan" is close but modes should override.
7. **Tone axes mostly have standards backing:** directness 0.9 ≈ BLUF/AR 25-50; confidence "uncertainty stated once, precisely" is exactly the Radical Candor humble + Crucial Conversations tentative-but-not-weak synthesis — good. `warmth` has the weakest external mapping; the checkable proxy is Radical Candor's four-part test (kind/clear/specific/sincere) on evaluative content, and CORE completeness — consider documenting warmth in tone-mapping.md as "CORE completeness + behavior-not-person," not adjectives.
8. **reading_level grade6/grade9 match plain-language practice** (GOV.UK targets ~age 9 reading age for everyone, which is stricter — grade9 for bluf is defensible for internal managers; keep).
9. **never_compress list matches STE rule "do not omit parts of the sentence to make text shorter"** — add "safety/caution instructions" (STE starts them with a clear command and never buries them) and "owner + deadline of an ask".
10. **Consistency rule missing:** add `same_term_same_concept: true` under style — a linter can diff synonyms against lexicon entries (e.g., flag "repo/repository/codebase" mixing within one narrative).
11. **Negative contractions:** config bans nothing here; add to banned-phrases: can't, don't, won't → cannot, do not, will not (GOV.UK) — at least for bluf/technical; eli5 may keep positive contractions (it's, we're).

## 11. Existing Tooling Observed (partial coverage of respeak's linting lane)

- Boeing Simplified English Checker (BSEC) — 350-rule parser checking STE compliance.
- HyperSTE (Etteplan), Congree STE Checker, TechScribe term checker — commercial STE linters; proof that controlled-vocabulary + sentence-cap linting is a solved product category.
- STE's own caveat applies to respeak: checkers "are not fool-proof ... if authors rely blindly on what checkers tell them, they are likely to write rubbish" — pair lint with an LLM judge.

## Sources (all fetched 2026-08-31)

- https://www.plainlanguage.gov/guidelines/ (redirects to https://digital.gov/guides/plain-language/ — guide series index)
- https://digital.gov/guides/plain-language/writing (active voice, present tense, hidden verbs)
- https://raw.githubusercontent.com/GSA/plainlanguage.gov/master/_pages/guidelines/concise/write-short-sentences.md
- https://raw.githubusercontent.com/GSA/plainlanguage.gov/master/_pages/guidelines/concise/write-short-paragraphs.md
- https://raw.githubusercontent.com/GSA/plainlanguage.gov/master/_pages/guidelines/concise/keep-the-subject-verb-and-object-close-together.md
- https://raw.githubusercontent.com/GSA/plainlanguage.gov/master/_pages/guidelines/concise/use-positive-language.md
- https://raw.githubusercontent.com/GSA/plainlanguage.gov/master/_pages/guidelines/words/avoid-noun-strings.md
- https://raw.githubusercontent.com/GSA/plainlanguage.gov/master/_pages/guidelines/words/minimize-abbreviations.md
- https://raw.githubusercontent.com/GSA/plainlanguage.gov/master/_pages/guidelines/words/use-the-same-terms-consistently.md
- https://raw.githubusercontent.com/GSA/plainlanguage.gov/master/_pages/guidelines/words/use-simple-words-phrases.md
- https://raw.githubusercontent.com/GSA/plainlanguage.gov/master/_pages/guidelines/organize/place-the-main-idea-before-exceptions-and-conditions.md
- https://raw.githubusercontent.com/GSA/plainlanguage.gov/master/_pages/guidelines/organize/have-a-topic-sentence.md
- https://raw.githubusercontent.com/GSA/plainlanguage.gov/master/_pages/guidelines/audience/address-the-user.md
- https://www.gov.uk/guidance/style-guide/a-to-z-of-gov-uk-style
- https://www.asd-ste100.org/
- https://en.wikipedia.org/wiki/Simplified_Technical_English
- https://en.wikipedia.org/wiki/BLUF_(communication)
- https://en.wikipedia.org/wiki/Barbara_Minto
- https://untools.co/minto-pyramid/
- https://www.exec-comm.com/ and https://www.exec-comm.com/product/simply-said/
- https://www.radicalcandor.com/blog/what-is-radical-candor/
- https://www.radicalcandor.com/blog/how-to-practice-radical-candor
- https://www.radicalcandor.com/glossary
- https://cruciallearning.com/crucial-conversations-book/
- https://cruciallearning.com/courses/crucial-conversations-for-dialogue/
- https://en.wikipedia.org/wiki/Crucial_Conversations
- https://sobrief.com/books/everyone-communicates-few-connect
- Book frameworks cited directly where noted (SCQA, STATE, Simply Said tactics, Maxwell principles) — marked "standard framework" in text.
