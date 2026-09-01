# respeak.config.yaml — v1 proposal

Evidence base: `config/respeak.config.yaml` (v0), `corpus/style/tone-mapping.md`, the three research files. Config's own governing rule — "a tone axis with no behavioral mapping is decoration and gets removed" (config/respeak.config.yaml:14-15, tone-mapping.md:4-5) — is applied throughout.

---

## 1. Fields to ADD

### `style` block

| Field | Type | Default | Research motivation |
|---|---|---|---|
| `min_alert_level` | map env→level | `{ci: error, interactive: warn}` | Vale's MinAlertLevel pattern; CI fails on error, interactive surfaces warnings (style-as-code-tooling.md:165, :10) |
| `person` | enum `first\|second\|third` | `second` | plainlanguage #14: "you" pulls readers in (communication-best-practices.md:31); flagged as missing at style-as-code-tooling.md:169 |
| `tense` | enum | `present` | plainlanguage #4 (communication-best-practices.md:22; style-as-code-tooling.md:169) |
| `contractions` | enum `required\|allowed\|avoid` | `allowed` | The single most lintable formality behavior — MS tip #3 (style-as-code-tooling.md:121, :170) |
| `negative_contractions` | const | `never` | GOV.UK: "cannot, not can't — many users misread them as the opposite" (communication-best-practices.md:200, :290) |
| `positive_form` | bool | `true` | plainlanguage #8: ban double negatives (communication-best-practices.md:25, :242) |
| `same_term_same_concept` | bool | `true` | plainlanguage #11 + STE one-word-one-meaning; flagged missing at communication-best-practices.md:289 |
| `readability_metrics` | list | `[flesch_kincaid, gunning_fog]` | "grade6" is ambiguous — metrics disagree; Vale averages multiple (style-as-code-tooling.md:168, :27-28) |
| `quoting_exempt` | bool | `true` | Every surveyed linter has an exception mechanism (Vale `exceptions`, write-good `whitelist`, alex literal carve-out) — respeak has none (style-as-code-tooling.md:166, :83) |
| `budgets` | map | see YAML §below | Hemingway's model: weakeners are budgets scaled to length, not zero-tolerance bans (style-as-code-tooling.md:92-95, :167); exclamation cap from Google (style-as-code-tooling.md:134, :174) |
| `feedback` | map | `{core_required: true, specific_praise_required: true, behavior_not_person: true}` | Radical Candor CORE completeness + "criticize the work, never the person" as the *checkable* replacement for the warmth scalar (communication-best-practices.md:147-149, :286) — see REMOVE |

### `narrative` block

| Field | Type | Default | Research motivation |
|---|---|---|---|
| `context_default` + accepted per-invocation `context` | enum `incident\|routine\|celebration` | `routine` | Mailchimp: tone conditions on reader state, not just audience (style-as-code-tooling.md:110-113, :171). `incident` forces plain language — the grounding literature's decompression triggers (linguistics-of-expert-shorthand.md:18-21, :152) |
| `mode_select` | enum `fixed\|compass` | `fixed` | Diátaxis's two-question compass is a cheap classifier for picking a mode when the caller doesn't (style-as-code-tooling.md:141). Default `fixed` to avoid behavior change |

### `shorthand` block

| Field | Type | Default | Research motivation |
|---|---|---|---|
| `max_entries` | int | `150` | Gregg's century of revisions: 150 WPM survived cutting to 181 briefs; later editions (129–132) traded marginal speed for transcription clarity. Returns on entries diminish fast (linguistics-of-expert-shorthand.md:131, :148) |
| `min_token_edit_distance` | int | `2` | Galantucci sign criteria (distinct, easy, variation-tolerant) + the medical failure taxonomy: U/0/4, IU/IV, QD/QOD near-neighbor collisions (linguistics-of-expert-shorthand.md:71, :126, :147) |
| `retire_after_days_unused` | int | `180` | Q-code deprecation: entries are retired centrally, never informally; require usage evidence to retain (linguistics-of-expert-shorthand.md:104, :148) |
| `review_cadence_days` | int | `90` | ICAO's own SID/STAR phraseology eroded without scheduled re-harmonization — "conventions decay without maintenance" (linguistics-of-expert-shorthand.md:99, :143) |
| `legibility_audit` | map | `{cadence_days: 30, method: fresh-decoder, sample: 10}` | Fay/Garrod: conventions forced to survive partner rotation stay legible; a fresh agent decoding a sample from the lexicon alone is the operational test (linguistics-of-expert-shorthand.md:82, :151) |
| `reserved_metawords` | list | `[CORRECTION, SAY-AGAIN, UNVERIFIED]` | ICAO/Q-code reserved repair words that may never be compressed or repurposed (linguistics-of-expert-shorthand.md:97, :105, :149). `UNVERIFIED` matches tone-mapping's speculation fence (tone-mapping.md:47) |
| `register_marker` | enum `required\|optional` | `required` | ICS precedent: shorthand use is announced in-band ("Interco"), never assumed (linguistics-of-expert-shorthand.md:113, :149) |
| `readback_required_for` | list | `[irreversible-actions, security-findings, escalations-to-human]` | ICAO readback/hearback made grounding mandatory for safety-critical items (linguistics-of-expert-shorthand.md:97, :150) |
| `decompress_on` | list | `[escalation-to-human, incident, repeated-fidelity-failure, new-partner]` | The three grounding decompression triggers (time pressure, error history, ignorance gaps) + ICS scope-shrink precedent (linguistics-of-expert-shorthand.md:18-21, :110, :152) |

**Corpus-side additions (noted, not config fields):** per-entry `exceptions:` and `link:` on banned phrases (style-as-code-tooling.md:54-55, :172), a `condescension` category ("simply / it's easy / just / obviously / everyone knows" — style-as-code-tooling.md:134, :173), and lexicon-entry fields `domain_tags`, `opposite_of`, `args`, `context_bans` from the brevity-code entry format (linguistics-of-expert-shorthand.md:88-91, :144).

---

## 2. Fields to CHANGE

1. **`modes.technical.max_sentence_words: 28 → 25`** (config:48). Above every standard; STE caps descriptive text at 25 (communication-best-practices.md:280, :43). Procedural lines get a separate `max_step_words: 20`.
2. **`style.active_voice_min: 0.8` → `style.budgets.passive_per_10_sentences: 2`** (config:63). A ratio is the one constraint nothing surveyed can check; Hemingway shows budgets are the usable form (style-as-code-tooling.md:167). Procedures get a per-structure override of zero passive — STE requires 100% active in instructions (communication-best-practices.md:282, :50).
3. **`style.one_metaphor_max: true` → per-mode `metaphor_budget` int** (config:62). GOV.UK bans metaphors outright; Google bans figurative language; the paid-for single analogy is a *teaching tool* that belongs only to eli5 (communication-best-practices.md:285, :196; style-as-code-tooling.md:134).
4. **`reading_level: grade6` (string) → `reading_level_grade: 6` (int/null)** plus global `readability_metrics`. String encoding names no metric; Vale's readability check takes a numeric grade and averages metrics (style-as-code-tooling.md:168, :27).
5. **`modes.technical.reading_level: none` → `reading_level_grade: 12`.** Hemingway's Technical preset is "a *higher* grade level," not no ceiling (style-as-code-tooling.md:89). **Uncertainty:** no source gives a number; 12 is a judgment call — keeping `null` is defensible, but the prior art keeps a ceiling.
6. **`shorthand.never_compress`: prose strings → structured entries** `{class, failure_mode, use_instead}`. The TJC list format records *why* each ban exists and its scoped exceptions (linguistics-of-expert-shorthand.md:117-124, :146). New classes: safety/caution instructions and the owner+deadline of an ask (communication-best-practices.md:288); identifiers, novel decisions, negations — Piantadosi: never shorten high-surprisal content (linguistics-of-expert-shorthand.md:61, :145).
7. **`shorthand.auto_uses: 5` → structured `auto:` gate.** The v0 comment (config:71-72) promises "no translation-fidelity failures" but the shape only counts uses. Grounding evidence = downstream correct action + verified echo (linguistics-of-expert-shorthand.md:41, :150).
8. **`version: 0 → 1`** with a `schema:` pointer — Vale/textlint both validate config shape; respeak has version but no schema (style-as-code-tooling.md:176).

---

## 3. Fields to REMOVE (decoration, per config:14-15)

1. **`narrative.tone.warmth: 0.4`** (config:19) and **`modes.eli5.tone.warmth: 0.6`** (config:36). The research's verdict: "warmth has the weakest external mapping; the checkable proxy is Radical Candor's four-part test... and CORE completeness" (communication-best-practices.md:286), and bare scalars are exactly what LLMs don't reliably interpret (style-as-code-tooling.md:149). Replaced by the checkable `style.feedback` block (ADD §1); tone-mapping.md:28-38 becomes the documentation for those switches.
2. **`modes.bluf.tone` override entirely** (config:44). `formality: 0.6` lands in the same behavior band (0.4–0.6) as the global 0.4 (tone-mapping.md:8-13) — no observable difference. `directness: 1.0` vs. global 0.9: the directness table has only low/high columns (tone-mapping.md:15-21) — indistinguishable. Both overrides change nothing checkable.
3. **`modes.technical.tone: {formality: 0.5}`** (config:52). Same band as global 0.4 — decoration by the same test.
4. **`style.one_metaphor_max`** — removed from `style` as a consequence of CHANGE #3 (moves into modes).

Kept: `modes.eli5.tone.formality: 0.2` — it crosses into the 0.0–0.3 band (contractions free, And/But openers), a real behavior change (tone-mapping.md:8-13).

---

## 4. Revised `modes` section

```yaml
modes:
  eli5:
    tech_level: 1
    reading_level_grade: 6          # plain-language practice (communication-best-practices.md §10)
    max_sentence_words: 15          # Simply Said / plain-language 15–20 target
    length_budget_words: 150
    max_paragraphs: 1               # single-explanation made explicit (CBP critique #2)
    structure: single-explanation   # no headers; no bullets
    address_reader: true            # "you" — plainlanguage #14, Simply Said #2
    common_ground_opener: true      # Maxwell: open with something the reader already knows
    metaphor_budget: 1              # the one paid-for analogy...
    analogy_must_close: true        # ...and it must say what it maps to (CBP §10 ELI5)
    lexicon_terms: forbidden        # zero shorthand, zero undefined abbreviations
    contractions: allowed           # positive only; negative_contractions ban is global (GOV.UK)
    checks:                         # LLM-judge checks, not lint
      - understand-feel-do          # Maxwell triple: what happened / why you care / what next
      - no-parenthetical-asides     # includes "(s)" plural hedges (CBP §10 ELI5)
    output_glob: "out/eli5/**/*.md" # mode→glob bridge to CI (style-as-code-tooling §9.11)
    tone: { formality: 0.2 }        # crosses a behavior band in tone-mapping.md; kept

  bluf:
    tech_level: 2
    reading_level_grade: 9          # Hemingway default target; GOV.UK-adjacent
    max_sentence_words: 20          # AR 25-50 / plain-language cap
    length_budget_words: 200
    max_paragraph_sentences: 6      # STE paragraph cap
    structure: bluf                 # sentence 1 = the decision/result/ask; no preamble
    require_ask:                    # AR 25-50 canonical ask (CBP critique #5)
      owner: true
      deadline: true
      allow_fyi_no_action: true     # explicit "FYI only — no action needed" satisfies it
    address_reader: true
    metaphor_budget: 0              # GOV.UK: metaphors slow comprehension
    bullets:                        # GOV.UK bullet discipline
      lead_in_required: true
      min_items: 2
      max_sentences_per_item: 1
    grouping: mece                  # Minto: siblings must not overlap, none missing
    scqa_preamble_max_clauses: 1    # situation+complication compress to one clause max
    checks:
      - delete-test                 # sentence 1 alone must carry outcome + expectation (BLUF #6)
      - answer-the-question-asked   # Mattis/BLUF #4: if you can't, say why
    output_glob: "out/bluf/**/*.md"

  technical:
    tech_level: 4
    reading_level_grade: 12         # was none; Hemingway's Technical preset keeps a ceiling.
                                    # UNVERIFIED number — no source names a grade; null is defensible.
    max_sentence_words: 25          # was 28 — above every standard; STE descriptive cap is 25
    max_step_words: 20              # STE procedural cap (separate from descriptive)
    length_budget_words: 500
    max_paragraph_sentences: 6      # STE
    max_paragraph_words: 150        # plainlanguage (hard cap 250)
    structure: finding-first        # conclusion → evidence with file:line → open questions
    open_questions_require_test: true  # Crucial Conversations: end claims with a falsifiable check
    metaphor_budget: 0
    lexicon_terms: expand-first-use # ratified terms free after first expansion (tone-mapping L4)
    passive_allowed_when: agent-unknown  # STE descriptive rule; never for style
    procedural:                     # applies to any embedded steps, any mode
      active_voice: 1.0             # STE: instructions 100% active/imperative
      one_instruction_per_sentence: true
      numbered_steps: true          # GOV.UK: numbered steps, not bullets, for processes
      safety_lines_first: true      # STE: warnings open with a clear command or condition
    checks:
      - facts-before-stories        # first evidence-bearing sentence is a fact, not a verdict
    output_glob: "out/technical/**/*.md"
```

Supporting delta for the other sections (applies ADD/CHANGE items above):

```yaml
version: 1
schema: docs/respeak.config.schema.json   # style-as-code-tooling §9.12

narrative:
  default_mode: technical
  mode_select: fixed                # compass = Diátaxis 2-question classifier (opt-in)
  context_default: routine          # per-invocation: incident | routine | celebration (Mailchimp)
  tone:
    formality: 0.4
    directness: 0.9
    confidence: 0.8
    # warmth removed — replaced by style.feedback (Radical Candor CORE; CBP critique #7)
  tech_level: 3

style:
  banned_phrases: corpus/banned-phrases.yaml
  replacements: corpus/replacements.yaml
  rules: corpus/style/
  no_pleasantries: true
  no_self_narration: true
  person: second                    # plainlanguage #14
  tense: present                    # plainlanguage #4
  contractions: allowed             # compiles from formality; MS tip #3
  negative_contractions: never      # GOV.UK: "cannot", never "can't"
  positive_form: true               # no double negatives (plainlanguage #8)
  same_term_same_concept: true      # plainlanguage #11 + STE; lint against lexicon
  quoting_exempt: true              # quotes/code blocks exempt from bans (Vale/alex pattern)
  readability_metrics: [flesch_kincaid, gunning_fog]   # averaged (Vale semantics)
  min_alert_level: { ci: error, interactive: warn }
  budgets:                          # budgets, not bans (Hemingway model)
    passive_per_10_sentences: 2     # replaces active_voice_min: 0.8; procedural override = 0
    adverb_intensifiers_per_100_words: 1   # very/really/extremely (Simply Said #8)
    qualifiers_per_message: 1       # one precise uncertainty statement (CC + confidence axis)
    exclamations_per_doc: 0         # Google
    warn_phrases_per_1000_words: 5  # warn-severity matches as density, not ban
  feedback:                         # the checkable form of "warmth"
    core_required: true             # context + observation + result + next step, all four
    specific_praise_required: true  # bare "looks good" = Ruinous Empathy
    behavior_not_person: true

shorthand:
  lexicon: corpus/lexicon.yaml
  proposal_dir: corpus/proposals/
  ratification: human
  auto:                             # replaces auto_uses: 5 — shape now carries the semantics
    uses: 5
    fidelity_failures_allowed: 0
    readback_evidence: true         # downstream correct action + verified echo (ICAO)
  legibility_floor: 0.5
  max_entries: 150                  # Gregg: returns diminish fast past ~150 briefs
  min_token_edit_distance: 2        # QD/QOD, IU/IV near-neighbor failures
  retire_after_days_unused: 180     # Q-code deprecation pattern
  review_cadence_days: 90           # SID/STAR erosion: schedule re-harmonization
  legibility_audit: { cadence_days: 30, method: fresh-decoder, sample: 10 }
  register_marker: required         # declare shorthand in-band (ICS "Interco")
  reserved_metawords: [CORRECTION, SAY-AGAIN, UNVERIFIED]
  readback_required_for: [irreversible-actions, security-findings, escalations-to-human]
  decompress_on: [escalation-to-human, incident, repeated-fidelity-failure, new-partner]
  never_compress:                   # TJC format: each ban carries its failure story
    - { class: error-messages-and-stack-traces, failure_mode: verbatim evidence lost }
    - { class: security-findings, failure_mode: high-stakes content must survive any reader }
    - { class: user-quotes, failure_mode: misattribution; alex-style literal carve-out }
    - { class: numbers-with-units, failure_mode: bare magnitudes; TJC trailing-zero precedent }
    - { class: safety-and-caution-instructions, failure_mode: STE — never buried or shortened }
    - { class: ask-owner-and-deadline, failure_mode: BLUF ask stripped in compression }
    - { class: identifiers-novel-decisions-negations, failure_mode: high-surprisal content is where short encodings become unrecoverable (Piantadosi 2011) }
    - { class: reserved-metawords, failure_mode: repair channel must never be repurposed }
```

---

## 5. Per-audience profiles — yes, the research justifies them

Three independent lines of evidence say **audience is an axis orthogonal to mode**:

- **Partner-specific pacts:** shorthand ratified with one partner does not transfer to another; new partners force longer forms (linguistics-of-expert-shorthand.md:15, :29). Lexicon *access* is therefore a per-audience property, not a per-mode one.
- **Community co-membership:** jargon is licensed inside the group, layman terms outside (linguistics-of-expert-shorthand.md:42) — the theoretical basis of the two-register system, keyed to *who reads*, not *what form*.
- **The v0 config already implies it:** tone-mapping defines five tech levels (tone-mapping.md:52-63), but the three modes pin only 1, 2, and 4 — audiences at level 3 and level 5 (the only level where shorthand may appear inline, tone-mapping.md:62-63) have no home today. Mailchimp adds the reader-state dimension (style-as-code-tooling.md:110-113); Diátaxis holds voice constant and varies form by reader *need* (style-as-code-tooling.md:141-143). Grammarly Business ships per-team tone profiles (style-as-code-tooling.md:102 — flagged unverified-by-fetch at :204).

Design: **profile (who) × mode (form) × context (state)**. Voice constants in `style:` never vary (Mailchimp's voice/tone split, style-as-code-tooling.md:109).

```yaml
profiles:
  # A profile encodes the audience's common ground (Clark & Brennan).
  # It composes with a mode (document form, Diátaxis) and a context
  # (reader state, Mailchimp). Voice constants in style: never vary.
  #
  # Field schema:
  #   tech_level:          1-5, per tone-mapping.md table
  #   lexicon_access:      forbidden | expand-first-use | inline
  #                        (inline permitted ONLY at tech_level 5 — tone-mapping.md:62)
  #   reading_level_grade: int | null (overrides mode default)
  #   default_mode:        eli5 | bluf | technical
  #   address:             you | role-noun (formality band interaction)
  #   never_compress_extra: []   # audience-specific additions to the global list

  exec:
    tech_level: 1
    lexicon_access: forbidden
    reading_level_grade: 9
    default_mode: bluf
    address: you
  peer-engineer:              # fills the tech_level-3 gap the three modes leave open
    tech_level: 3
    lexicon_access: expand-first-use
    reading_level_grade: null
    default_mode: technical
    address: you
  author:                     # fills the tech_level-5 gap: the opt-in shorthand reader
    tech_level: 5
    lexicon_access: inline    # the only profile where the two lanes may converge
    reading_level_grade: null
    default_mode: technical
    address: you
```

---

## Limits and open items

- **Could not enumerate directories.** I could not verify whether `corpus/proposals/`, `corpus/style/` (beyond tone-mapping.md), or `docs/` contain files bearing on this review — a listing of `corpus/style/*` and `docs/*` would confirm nothing contradicts the removals in §3.
- **Not read:** `research/sources/deai-language-landscape.md`, referenced by corpus/banned-phrases.yaml:3 — the corpus-side additions (condescension category, entry `link:` fields) should be reconciled against it.
- **Consistency flag:** lexicon entry `2L` has `legibility: 0.4` (corpus/lexicon.yaml:51), below the `legibility_floor: 0.5` (config:78). Under both v0 and this v1 it must be rejected or rewritten at ratification time — currently it sits at `status: proposed` with no note.
- **Two admitted judgment calls:** `reading_level_grade: 12` for technical (prior art says "a ceiling exists," not a number) and `max_entries: 150` (interpolated from Gregg's 129–181 band).