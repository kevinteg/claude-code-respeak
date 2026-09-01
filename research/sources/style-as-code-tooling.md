# Style-as-Code Tooling: Schema Prior Art for respeak's Voice Config & CI Lint Path

Research date: 2026-08-31. Dimension: how style/voice get encoded as machine-readable configuration; Vale-style CI linting for respeak narratives.

## 1. Vale — the reference architecture for style-as-code

Vale (vale.sh, MIT, Go, sole dev @jdkato; repo now vale-cli/vale) is "code-like linting for prose." Key positioning from its own docs: it is **not** a grammar checker — "it offers a framework for creating and enforcing custom rules"; it ensures *consistency across multiple authors against one shared standard*. This is exactly respeak's problem shape: many agent authors, one ratified standard.

### Architecture
- **`.vale.ini`** (INI): core settings — `StylesPath` (where rule dirs live), `Packages` (remote style zips, `vale sync` installs), `Vocab` (accept/reject wordlists that override rules), `MinAlertLevel` (suggestion|warning|error), `IgnoredScopes`/`SkippedScopes`; then per-glob sections (`[*.md]`) with `BasedOnStyles`, `BlockIgnores`, `TokenIgnores`.
- **Styles** = directories of one-rule-per-file YAML (`.yml` required, not `.yaml`). Rule ID = `StyleName.FileName`.
- **Rule header fields** (all checks): `extends` (check type, required), `message` (required, `%s` interpolation), `level` (suggestion|warning|error; default suggestion), `scope` (heading, sentence, paragraph, raw, text...; default text), `link` (URL for rationale), `limit` (max triggers per file), `vocab` (bool).
- **Markup-aware**: parses Markdown/AsciiDoc/reST/HTML/XML/Org; skips code blocks by default; rules can target scopes (only headings, only sentences). Built on an NLP library, so sentence-level targeting works.
- **Actions/Fixes**: rules can carry `action: {name: replace|remove|edit|suggest, params: [...]}` → editors present Quick Fixes via vale-ls (LSP). There is also an MCP guide (docs.vale.sh/guides/mcp) — Vale is already positioning for agent consumption.

### Check (extension point) taxonomy — 12 types
| Check | What it encodes | Key params |
|---|---|---|
| `existence` | banned tokens/regexes | `tokens` (word-bounded non-capturing group), `raw` (concatenated regex, no `\b`), `ignorecase`, `nonword`, `exceptions` |
| `substitution` | bad→preferred map | `swap: {observed: expected}`; regex keys, capture groups (`$1`), pipe-separated multiple suggestions, `matchcase`/`capitalize` |
| `occurrence` | min/max count of a token per scope | `max`, `min`, `token`, `scope` (e.g., ≤3 commas/sentence; ≤70 chars/heading) |
| `repetition` | doubled words ("the the") | |
| `consistency` | either-or, pick one ("advisor" vs "adviser") | |
| `conditional` | "if X appears, Y must too" (e.g., acronym must be defined) | |
| `capitalization` | heading/case style ($title, $sentence, brand casing) | |
| `metric` | arbitrary formula over doc-level variables | `formula` + `condition`; variables: `words, sentences, syllables, characters, paragraphs, complex_words, long_words, polysyllabic_words, heading.h{n}, list, blockquote, pre` |
| `readability` | grade-level ceiling | `metrics:` one+ of Gunning Fog, Coleman-Liau, Flesch-Kincaid, SMOG, Automated Readability; `grade:` float ceiling; **multiple metrics are averaged**; always whole-document scope |
| `spelling` | Hunspell dicts + custom | |
| `sequence` | NLP token-sequence patterns (POS-aware) | |
| `script` | Tengo-scripted custom logic, sandboxed (no fs/network/process access) | |

### Packaged styles (github.com/errata-ai/packages; browse vale.sh/explorer)
Registry = `library.json`; entries tagged `style` (rules) or `config` (markup support). Notable packages: **Microsoft** (Vale port of the Microsoft Writing Style Guide), **Google** (Google developer docs style), **write-good**, **proselint**, **Joblint** (biased/exclusionary job-post language), **alex** (insensitive language), **Readability** (all the grade-level formulas as rules), plus Hugo/Docusaurus/MDX configs. Docs note the ports beat the originals: markup handling, scope targeting, no npm/pip needed, and rules from several packages mix in one config. Version-pin by using the release URL instead of the package name — recommended for CI "where a new rule appearing on its own would be disruptive."

### Vale in CI
- Official GitHub Action: `errata-ai/vale-action` (reviewdog-based; annotates PR diffs). Also: pre-commit hook, MegaLinter, CircleCI recipes.
- `level: error` rules fail the build (exit code nonzero at/above MinAlertLevel); `--minAlertLevel` flag overrides per-run.
- Mintlify (docs platform, Vale sponsor) "ships Vale as a built-in CI check"; Promptless "runs Vale on every doc its agents write" — precedent for **Vale as an LLM-output gate**, which is respeak's exact CI story.
- Output formats: line, JSON, and custom templates — JSON is machine-parseable for a translator-agent feedback loop.

### Field-by-field compilation: corpus/banned-phrases.yaml → a Vale style package
respeak's schema (read 2026-08-31): top-level `categories:` → each has `note` + `entries[]`; entry = `phrase` (literal) | `pattern` (regex), `severity` (error|warn), optional `fix` (guidance string). Case-insensitive by default.

Mapping (mechanical; a ~40-line compiler script covers it):
| banned-phrases.yaml field | Vale equivalent | Notes |
|---|---|---|
| category (e.g. `ai_cliches`) | one rule file per category: `styles/Respeak/AiCliches.yml` — or one file per entry for per-entry severity (see below) | Vale reports `Respeak.AiCliches` as the rule ID; category `note` → nothing native, fold into `message` or `link` |
| `phrase: delve` | `existence` rule `tokens: [delve]` | tokens get `\b` boundaries + non-capturing group automatically |
| `pattern: '\bthe spine\b'` | `existence` rule `raw:` entry | `raw` skips Vale's `\b` wrapping — respeak patterns already carry their own boundaries/anchors, so `raw` is the correct target, not `tokens`. CAVEAT: Vale uses Go's RE2 — no lookahead/backrefs; all current respeak patterns are RE2-safe. Anchors: `^(great|excellent|good) question` anchors to the *scope* — needs `scope: paragraph` or `sentence` to mean "opener" |
| `severity: error` | `level: error` | identical semantics: error = CI-fail |
| `severity: warn` | `level: warning` | Vale adds a third tier, `suggestion`, respeak lacks |
| `fix: examine / look at / dig into` | two options: (a) keep `existence`, put fix text in `message: "Avoid '%s' — examine / look at / dig into"`; (b) **upgrade to `substitution`** with `swap: {delve: examine|look at|dig into}` + `action: {name: replace}` → machine-applicable Quick Fix. (b) is strictly better for entries whose fix is a replacement; entries whose fix is *guidance* ("say what breaks if it changes") stay `existence` with the guidance in `message` |
| case-insensitivity default | `ignorecase: true` on every rule | |
| (missing in respeak) | `exceptions:` | Vale rules can whitelist strings — respeak has no per-entry exception list; needed for "unless quoting" (severity:warn comment says "flag for rewrite unless quoting"— Vale handles the quoting case structurally: blockquote scope can be ignored via `SkippedScopes` or scoped rules) |
| (missing in respeak) | `link:` | respeak entries have no rationale URL; category notes could compile to `link` pages under docs/ |

Granularity decision: Vale severity is per-*rule*, respeak severity is per-*entry*. So a category with mixed severities must compile to ≥2 files (`AiCliches-error.yml`, `AiCliches-warn.yml`) or one file per entry. One-file-per-entry gives the best diagnostics (rule ID names the phrase) at the cost of file count — this is what the Microsoft/Google packages do (e.g., `Microsoft.Adverbs`, `Google.We`).

Also directly compilable from respeak config: `modes.*.max_sentence_words` → `occurrence` (scope: sentence, token: `[^\s]+`... — in practice packages use existence-on-long-sentence regex or `metric`); `modes.*.reading_level` → `readability` rule with `grade: 6` / `grade: 9`; `style.active_voice_min: 0.8` → **not directly expressible** (Vale's write-good port flags each passive instance; a *ratio* needs `script` in Tengo or post-processing of JSON output); `summary_inflation` anchored patterns → `scope: paragraph` existence rules. `corpus/replacements.yaml` → one `substitution` rule, trivially.

Bottom line: **~90% of respeak's style layer compiles mechanically to a Vale package**; the non-fits are (1) per-entry severity granularity (solved by file-splitting), (2) ratio-based constraints like active_voice_min (needs `script` or wrapper), (3) mode-conditional rules — Vale configs are per-glob, so respeak's three modes map cleanly to three globs/paths (`out/eli5/*.md`, `out/bluf/*.md`, `out/technical/*.md`) each with its own `BasedOnStyles` + readability rule. That per-glob trick is the clean way to encode modes in Vale.

## 2. textlint, proselint, write-good, alex — rule models

### textlint (textlint.org, MIT, JS)
- "ESLint for natural language." **No bundled rules** — every rule is an npm package (`textlint-rule-*`); config is `.textlintrc.json` with a `rules:` map (rule name → true/options object). Rules are JS functions over an AST (TxtAST), so rules can be arbitrarily smart (unlike Vale's declarative YAML).
- Supports `--fix` with dry-run, and rule *presets* (e.g., `preset-ja-technical-writing`, which famously enforces max sentence length, max ten, no doubled particles — the Japanese tech-writing community is textlint's stronghold).
- CI: formatters include `checkstyle`, `github`, `junit`, `json` — drop-in for any CI annotate step. Inline disabling via `<!-- textlint-disable -->` comments.
- Model lesson for respeak: per-rule options objects (severity + parameters per rule in one config file) and the preset mechanism (a "mode" = a preset of rules with parameters).

### proselint (amperser/proselint, BSD, Python)
- Rules are curated *usage advice* from named authorities (Garner, Pinker, Orwell, DFW...). ~60 checks with dotted IDs. Output: `file:line:col: check_name: message`, or JSON with a **stable wire schema**: `check_path`, `message`, `pos`, `span`, `replacements` (nullable).
- Checks most relevant to respeak (they overlap its corpus directly): `hedging` ("avoid undermining yourself with uncertainty"), `cliches.misc`, `industrial_language.corporate_speak` (corporate buzzwords), `industrial_language.jargon`, `misc.metadiscourse` ("avoid discussing the discussion" = respeak's self_narration category), `misc.apologizing`, `misc.pretension`, `mixed_metaphors` (≈ respeak's one_metaphor_max, weaker), `lexical_illusions`, `redundancy.misc`, `restricted.top1000` (vocabulary restriction — an ELI5-adjacent idea: restrict to the 1000 most common words), `restricted.elementary`.
- Config: `~/.proselintrc.json` toggles checks on/off; no severity tiers (everything is one level) — weaker than Vale/respeak here.

### write-good (btford/write-good, MIT, JS)
- Nine named checks, each individually toggleable: `passive` (passive voice), `illusion` (repeated words), `so` (sentence-initial "So"), `thereIs` (sentence-initial "there is/are"), `weasel` (weasel words), `adverb` (weakening adverbs: really, very, extremely), `tooWordy`, `cliches`, `eprime` (all forms of "to be"; off by default).
- API: `writeGood(text, {passive:false, whitelist:['read-only'], checks: customExtension})` → `[{reason, index, offset}]`. Extension = module of `{fn(text) -> [{index, offset}], explanation}` — the minimal viable rule interface.
- Lesson: `whitelist` (per-run exception list) and check-level disable — both absent from respeak's schema.

### alex (get-alex/alex, MIT, JS; built on retext-equality + retext-profanities)
- Catches "gender favoring, polarizing, race related, or other unequal phrasing": gendered work titles/proverbs, ableist language, **condescending language** (`obviously`, `everyone knows` — directly relevant to respeak's tone constraints), master/slave, profanity.
- Notable engineering: **assumes good intent and ignores words meant literally** (quoted "he", `He — ...`) — the same carve-out respeak's never_compress list makes for quoted user text. Config: `allow`/`deny` lists + `profanitySureness` threshold (0-2). Inline `<!--alex disable rule-->` comments. reviewdog GitHub Action exists.

## 3. Hemingway Editor — the metric set

(hemingwayapp.com; docs at /help/docs/readability and /help/docs/highlighted-issues; Boondoggle Studio, LLC)

- **Readability score**: US grade level for the whole document. **Default target: grade 9** — "the average for adults in the United States." Three presets: **Accessible** (lower grade, young/accessibility audiences), **Default**, **Technical** ("higher grade level for technical and academic writing"). This preset triple is a near-exact match for respeak's eli5(grade6)/bluf(grade9)/technical(none) — independent convergence on the same design.
- **Highlight taxonomy** (each type individually hideable via eye-toggle — per-check disable again):
  - **Yellow** = hard-to-read sentence (more complex than target readability); **Red** = very hard to read ("far more complex than your target score"). Note the thresholds are *relative to the chosen target grade*, not absolute word counts — a subtler design than respeak's fixed `max_sentence_words`.
  - **Blue "weakeners"** — three sub-counts: **Adverbs** ("could use a more interesting verb"), **Passive voice** (rewrite active), **Qualifiers** ("maybe", "I think" — "make your writing sound less confident"; recommended fix is deletion). Classic Hemingway presented these as budgets ("aim for N or fewer") scaled to document length rather than zero-tolerance.
  - **Purple** = word with a simpler exact synonym ("utilize"→"use"; sometimes "remove entirely") — i.e., a substitution table.
  - **Green** = grammar/spelling/punctuation (Plus-only).
- Explicit philosophy: "our highlights and scores are only a guide... you don't need to fix every yellow or red sentence... focus on the worst offenders and try to bring your overall score down." I.e., document-level score with per-instance advisories — supports respeak treating warn-level matches as a budget, not a ban.
- Document stats exposed: letters, characters, words, sentences, paragraphs, reading time.
- Editor Plus adds LLM rewrites priced per sentence ("AI sentence credits"), and only charges "if a rewrite lowers the grade level" — a fitness-gated rewrite loop, structurally identical to respeak's translator nudging output below a readability ceiling.

## 4. Grammarly — tone detection axes and style-guide-as-config

- Grammarly's **tone detector** analyzes word choice, phrasing, punctuation, and capitalization and labels drafts from a set of **40+ tone labels**; the commonly surfaced ones include: confident, formal, friendly, optimistic, worried, curious, joyful, sad, surprised, urgent, direct, appreciative, accusatory, disapproving, informal, neutral. It reports the top 2–3 detected tones with emoji, and (in business tiers) lets an org flag tones to *aim for* or *avoid*.
- Grammarly Business **style guides**: admins encode company terminology as rules (term → preferred term, with notes), essentially a hosted substitution dictionary layered over the general engine; plus **tone profile** settings per team (formality: informal/neutral/formal; and "sounds like us" brand-tones). The tone axes Grammarly exposes to configuration are effectively: **formality** (3-level), **confidence**, **friendliness/warmth**, **directness/urgency** — the same four axes respeak already has (formality, confidence, warmth, directness), which validates respeak's axis choice.
- Key structural difference: Grammarly's detector is a classifier over labels; respeak's config is generative (0-1 scalars steering production). The lintable middle ground is Grammarly's aim-for/avoid tone lists: a *detector in CI* asserting "output classifies as direct+confident, not apologetic" is more testable than asserting a scalar.

## 5. Mailchimp Content Style Guide — voice constant, tone varies

(styleguide.mailchimp.com, CC BY-NC 4.0 — the canonical, most-copied SaaS style guide)

- The model: **"You have the same voice all the time, but your tone changes"** — with your closest friends vs. in a meeting with your boss. "Our voice doesn't change much from day to day, but our tone changes all the time."
- Tone selection is keyed to the **reader's emotional state**: "You wouldn't want to use the same tone of voice with someone who's scared or upset as you would with someone who's laughing." Practical instruction: infer state of mind, adjust tone; "it's always more important to be clear than entertaining"; forced humor is worse than none — "If you're unsure, keep a straight face."
- Voice is defined as a short list of named traits with one-paragraph operationalizations: **plainspoken** ("value clarity above all... avoid distractions like fluffy metaphors and cheap plays to emotion"), **genuine** (familiar, warm, accessible), **translators** ("demystify B2B-speak and actually educate" — Mailchimp literally names the *translator* role that respeak builds), **dry humor** ("winking to shouting"; "never condescending").
- Lintable residue: active voice, no slang/jargon, positive phrasing, plus the guide's separate Word List (term substitutions). The voice traits themselves are judgment; the guide encodes them as *examples + named traits*, not parameters.
- Mapping to respeak: voice = respeak's `style:` block + banned-phrases corpus (constant across modes); tone = per-mode `tone:` overrides. Mailchimp's insight respeak lacks: tone should also condition on *reader state* (incident vs. routine report), not just mode/audience — a `context:` or `urgency:` input the translator could accept per-invocation.

## 6. Microsoft & Google style guides — what is lintable vs. judgment

### Microsoft Writing Style Guide (learn.microsoft.com/en-us/style-guide)
Brand voice: "warm and relaxed, crisp and clear, and ready to lend a hand." The **Top 10 tips** (with lintability assessment):
1. **Bigger ideas, fewer words** ("Shorter is always better") — partially lintable (length budgets).
2. **Write like you speak** (read aloud; no jargon) — judgment.
3. **Project friendliness = use contractions** (it's, you'll, we're) — fully lintable (substitution: `it is → it's`; Vale's Microsoft package has `Microsoft.Contractions`).
4. **Get to the point fast** (front-load keywords; lead with what matters) — judgment (≈ BLUF).
5. **Be brief** — partially lintable (word budgets, `tooWordy` lists).
6. **Sentence-style capitalization** — fully lintable (`capitalization` check).
7. **No end punctuation in headings** — fully lintable (the canonical Vale `existence` example).
8. **Oxford comma** — lintable (regex approximation).
9. **One space after periods; no spaces around dashes** — fully lintable.
10. **Revise weak writing** (start with a verb; cut "you can"; avoid "there is/are") — mostly lintable (`thereIs` check; "you can" existence rule exists in Vale's Microsoft package).
Rule of thumb visible here: mechanics and word choice lint; *emphasis, ordering, and audience empathy* don't — they need either an LLM judge or a human.

### Google Developer Documentation Style Guide (developers.google.com/style)
- Explicit precedence hierarchy: project style → this guide → Merriam-Webster/Chicago/**Microsoft** (Google defers to MS for technical style gaps). Opens with Orwell: "Break any of these rules sooner than say anything outright barbarous" — guidelines, not rules.
- Voice/tone: "conversational, friendly, and respectful... like a knowledgeable friend"; "Don't try to be super-entertaining, but also don't aim for super-dry."
- Its **avoid-list is almost entirely lintable** and overlaps respeak's corpus heavily: buzzwords/jargon; **figurative language incl. metaphors** (cf. respeak `one_metaphor_max` — Google is stricter: zero); placeholder phrases ("please note", "at this time"); choppy or long-winded sentences; sentences all starting with the same phrase (Vale `consistency`/`repetition`-adjacent); pop-culture references; **exclamation marks** (existence: `!`); "let's do something" phrasing (cf. respeak's `self_narration` ban on "let's"); **"simply / It's easy / quickly" in procedures** (condescension — candidate for respeak's corpus); internet slang (tl;dr, ymmv).
- Grammar chapters that are pure lint: active voice, present tense, second person, contractions, no anthropomorphism, sentence case. All shipped in the Vale `Google` package.

## 7. Diátaxis — document modes as first-class config (diataxis.fr)

- Four forms from a 2×2 (action/cognition × acquisition/application): **tutorials** (learning-oriented, "Can you teach me to…?", a lesson), **how-to guides** (goal-oriented, "How do I…?", steps), **reference** (information-oriented, "What is…?", "dry description"), **explanation** (understanding-oriented, "Why…?", "discursive explanation"). Analogy given: teaching a child to cook / a recipe / the back-of-packet info / an article on culinary history.
- Core claim relevant to respeak: each form has its own *writing style contract*, and the main failure mode is **blur** — "writing style and content make their way into inappropriate places... in the worst case a complete or partial collapse" of adjacent forms into each other. Structure "provides both clear expectations (to the reader) and guidance (to the author)."
- Direct analogy to respeak's modes: eli5 ≈ tutorial/explanation (understanding, one analogy), bluf ≈ how-to/decision brief (goal/action), technical ≈ reference+explanation (information with evidence). The transferable lesson: **define each mode by the reader's need and forbid cross-mode blur** — a lintable proxy: structural rules per mode (respeak already has `structure:` per mode: no headers/bullets in eli5, first-sentence-decision in bluf, finding-first in technical). Diátaxis's "compass" (two questions: action vs. cognition? acquisition vs. application?) is a cheap classifier the translator can run to pick a mode when the caller doesn't specify.
- One form ≠ one tone: Diátaxis holds *voice* constant across quadrants and varies form/content — the same voice-constant/tone-varies split as Mailchimp, at the document-architecture level.

## 8. LLM-era voice configuration

- **Claude Code output styles** (code.claude.com/docs/en/output-styles): "Output styles change how Claude responds, not what Claude knows. They modify the system prompt to set **role, tone, and output format**." Built-ins include **Concise** — "leads with the result, skips preamble and narration, keeps responses short... always keeps the complete content of error reports, security warnings, and confirmations for destructive actions." That carve-out is a direct precedent for respeak's `never_compress` list (verbatim evidence classes exempt from compression). Custom styles are Markdown files with frontmatter (name/description) + prose instructions; selection persisted in `.claude/settings.local.json` (`outputStyle` field). Since respeak is a Claude Code plugin, its three modes could literally *ship as output styles* generated from respeak.config.yaml.
- **CrewAI agent persona schema** (crewAIInc/crewAI): per-agent `role`, `goal`, `backstory`, plus `llm`, `tools`, `settings` in JSONC — persona as freeform strings, no measurable axes; nothing lintable. Typical of agent frameworks (AutoGen `system_message`, LangGraph prompts): voice is prose, not parameters. respeak's numeric tone axes + corpus compilation is *ahead* of framework practice here.
- The emerging pattern across products (Grammarly tone profiles, Hemingway readability presets, Claude output styles, Writer/Jasper-class "brand voice" features): a voice config = (a) a few coarse **enum/scalar axes** (formality, confidence, warmth), (b) a **terminology table** (banned/preferred), (c) **structural/format contract** per mode, (d) **length/readability budgets**, (e) an **exemption list** for content that must pass through verbatim. respeak.config.yaml already has all five groups — rare and good.
- Critical caveat documented in respeak's own config comment ("a tone axis with no behavioral mapping is decoration and gets removed"): LLMs don't reliably interpret bare scalars like `warmth: 0.4`. Prior art says compile scalars into *behavioral instructions + lintable assertions* (e.g., formality≤0.4 → "use contractions" → Vale Contractions rule as the check). The config should be the single source that both the system prompt and the Vale package are generated from.

## 9. Synthesis: the field set of a good voice-config schema, and a critique of respeak.config.yaml

Composite schema from all prior art (source in parentheses):
1. **Voice constants** (Mailchimp): named traits w/ operational one-liners; banned/preferred terminology; hard constraints (no pleasantries, active-voice, metaphor budget). Constant across modes.
2. **Tone axes** (Grammarly): formality, directness, warmth/friendliness, confidence — plus per-context override and aim-for/avoid tone labels for classifier-based checking.
3. **Mode contracts** (Diátaxis/Hemingway): per mode — reader need, structure, reading-level target, sentence cap, length budget, tech level.
4. **Budgets, not just bans** (Hemingway/write-good): adverb count, passive-voice share, qualifier count, warn-phrase density per 1000 words — scaled to document length.
5. **Terminology** (Vale/Grammarly Business): substitution map with severities, exceptions, rationale links; vocab accept/reject lists.
6. **Verbatim exemptions** (Claude Concise style, alex's literal-use carve-out, medical do-not-use lists): content classes that bypass compression/rewrite.
7. **Enforcement wiring** (Vale/textlint): severity tiers incl. a third "suggestion" level; per-rule disable/inline-escape; min alert level per environment (CI vs. interactive); machine-readable output for the rewrite loop.

### Critique of config/respeak.config.yaml (read 2026-08-31)
**Strong / keep:** four tone axes match Grammarly's exposed set exactly; per-mode reading_level/max_sentence_words/length_budget mirrors Hemingway's presets; `never_compress` has better prior-art support than the authors may know (Claude Concise, alex literals); the "no behavioral mapping ⇒ removed" discipline is the right answer to scalar-decoration risk.
**Gaps (ordered by value):**
1. **No third severity/alert-level tier and no `min_alert_level`** — Vale's suggestion/warning/error + MinAlertLevel lets CI fail on error while interactive runs surface warnings. Add `style.min_alert_level: {ci: error, interactive: warn}`.
2. **No exceptions/whitelist mechanism** — every linter surveyed has one (Vale `exceptions`, write-good `whitelist`, alex `allow`, textlint inline-disable). banned-phrases entries need optional `exceptions: []`, and quoting contexts (blockquotes, code) should be structurally exempt.
3. **`active_voice_min: 0.8` is the only ratio constraint and nothing can currently check it** — either add tooling notes (Vale `script`/JSON post-processing) or restate as a budget ("≤2 passive sentences per 10"), which Hemingway shows is the usable form. Generalize: add `budgets:` (adverbs, qualifiers, warn-phrase density) instead of only binary bans.
4. **Readability metric unspecified** — `reading_level: grade6` doesn't say Flesch-Kincaid vs. ARI vs. averaged; Vale docs note the metrics disagree. Specify `readability_metrics: [Flesch-Kincaid, Gunning-Fog]` + document that multiple are averaged.
5. **No person/POV or tense field** — MS/Google both mandate second person + present tense; it's cheap to lint (Vale Google package does). Add `style.person: second` (per-mode override: eli5 may want "you/we"), `style.tense: present`.
6. **No contractions switch** — the single most lintable formality behavior (MS tip #3); `formality: 0.4` should compile to `contractions: required|allowed|avoid`.
7. **No reader-state/context input** (Mailchimp): mode ≠ situation. An `urgency` or `context: incident|routine|celebration` parameter the translator accepts per-invocation, adjusting tone within the same mode.
8. **No rationale links** — Vale rules carry `link:`; respeak categories have `note` but entries lack a pointer to research (e.g., deai-language-landscape.md anchors). Cheap to add, pays off when a human disputes a ban.
9. **No condescension bans** — Google's "simply / it's easy / just / quickly (in procedures)" and alex's "obviously / everyone knows" belong in banned-phrases (new category `condescension`).
10. **Exclamation policy missing** — Google: avoid exclamation points; trivially lintable occurrence rule (`max: 0` or 1 per doc).
11. **Modes aren't wired to enforcement** — add per-mode output globs so a generated .vale.ini can apply `Respeak-Eli5` (grade 6 readability, 15-word sentences) only to eli5 outputs, etc. The mode→glob mapping is the missing bridge between config and CI.
12. **version: 0 but no schema** — publish a JSON Schema for respeak.config.yaml itself; textlint/Vale both validate config shape.

### Recommended CI lint path for respeak narratives
1. `respeak compile` (small script): banned-phrases.yaml + replacements.yaml + config budgets → `styles/Respeak/` Vale package (existence/substitution/occurrence/readability rules; one file per entry for error-level, per category for warn-level) + generated `.vale.ini` with per-mode globs.
2. Run `vale --output=JSON` in CI (errata-ai/vale-action for PR annotation; pre-commit hook locally). error ⇒ fail; warning ⇒ annotate.
3. Ratio/judgment checks Vale can't do (active-voice share, one-metaphor-max, BLUF-first-sentence, tone classification): a post-processor over Vale's JSON + an LLM-judge step with the config as rubric — same two-tier pattern as Hemingway (mechanical highlights + AI rewrites gated on score improvement).
4. Feed Vale's JSON diagnostics back to the translator agent as a rewrite prompt — Promptless already demonstrates "Vale on every doc its agents write."

## Sources (all fetched 2026-08-31)
- https://raw.githubusercontent.com/errata-ai/vale/v3/README.md
- https://vale.sh/docs/ (redirects to docs.vale.sh)
- https://docs.vale.sh/llms.txt
- https://docs.vale.sh/checks/existence.md , /checks/substitution.md , /checks/occurrence.md , /checks/readability.md , /checks/metric.md
- https://docs.vale.sh/topics/.vale.ini.md , /topics/styles.md
- https://raw.githubusercontent.com/errata-ai/packages/master/README.md
- https://raw.githubusercontent.com/amperser/proselint/main/README.md
- https://raw.githubusercontent.com/btford/write-good/master/README.md
- https://raw.githubusercontent.com/textlint/textlint/master/README.md
- https://raw.githubusercontent.com/get-alex/alex/main/readme.md
- https://hemingwayapp.com/ , /help , /help/docs/readability , /help/docs/highlighted-issues
- https://styleguide.mailchimp.com/voice-and-tone/
- https://learn.microsoft.com/en-us/style-guide/welcome/ , /style-guide/top-10-tips-style-voice
- https://developers.google.com/style , /style/tone
- https://diataxis.fr/ , https://diataxis.fr/map/
- https://code.claude.com/docs/en/output-styles.md
- https://raw.githubusercontent.com/crewAIInc/crewAI/main/README.md
- Local: corpus/banned-phrases.yaml, config/respeak.config.yaml (read directly)

Note on Grammarly: grammarly.com marketing pages are JS-heavy and were not fetched; the tone-detector axes summarized in §4 reflect widely documented product behavior (40+ tone labels, top-3 display, business aim-for/avoid tone settings, 3-level formality) — treat specifics as unverified-by-fetch and confirm before quoting numbers downstream.
