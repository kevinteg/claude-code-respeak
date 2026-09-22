# Changelog

Versions follow `.claude-plugin/plugin.json`. Dates are commit dates.

## 0.6.0 (2026-09-21)

What a ten-agent editorial pass over nine household sites found on
2026-09-21, across about 2,000 edited files. Each bullet names the field
failure behind it.

- The style gate blocks on what a write introduced, not on every hit the
  file already held. The new key `gate.block_on: introduced | any`
  defaults to `introduced` and hands the scanner a baseline: the committed
  version of the file, else the pre-edit text rebuilt from the `Edit`
  call's own strings, else an empty file. Each step falls through on
  failure, so the hook still fails open. Before this, one error-severity
  hit the pass could not reach, a banned term inside a heading that
  `respeak-verify-edit.py` holds byte-identical, shut the file to every
  later edit. `block_on: any` restores the whole-file verdict, at any
  layer that may set `fail_on`.
- A write that adds nothing passes with a note rather than in silence. The
  hook prints one line of PostToolUse
  `hookSpecificOutput.additionalContext` naming the pre-existing hits that
  sit at or above the resolved `fail_on`, which is what `block_on: any`
  would have blocked on. Density-tier tells stay out of that line: on one
  real page they ran to 79 hits, mostly dashes, and naming them invites
  the layout edits an editorial pass is told not to make.
- `scripts/respeak-gate.sh --file` gains a new `--baseline-ref REF` flag,
  which asks what changed since REF for a build that gates a branch on its
  own diff. Otherwise it keeps whole-file semantics whatever `block_on`
  says, because the CI form has no edit to measure against.
- `respeak-measure.py DOC --baseline BASE` scans BASE with the same corpus
  and configuration, then splits DOC's hits per rule into `introduced` and
  `baseline`. Under a baseline, `--fail-on` sees only introduced hits and
  budgets that got worse, and the text report tags each rule line
  `[new N, pre-existing M]`. This is the mechanism `gate.block_on` runs
  on.
- HTML comments are exempt from the scan, as fenced code and blockquotes
  already were. Nothing inside a `<!-- ... -->` banner reaches the
  rendered page. Its words, its dashes and its phrases still counted
  against the page's budgets. Vendored banners alone put several published
  pages over the dash density.
- A URL is an address, not prose. A bare URL, an autolink, and the target
  of an inline link are dropped before the word and sentence counts, the
  way link targets already were. An address has no words to read and no
  sentence punctuation, so it inflated the word count and joined the lines
  around it into one long sentence. The link's label still counts.
- The sentence splitter reads Markdown structure. Cutting only at `.!?`
  read a bullet list as a single sentence. One site measured an average
  sentence of 68.9 words, and the pass reported bullet lists as long
  sentences on all nine. Prose is now cut into blocks at blank lines, and
  a list item or a table row opens a new unit. The list marker is not
  counted as a word, and each unit is then split at sentence punctuation.
  This repository's README drops from an 89-word longest sentence to 27,
  and from 15.1 to 13.0 average, with no prose changed. Every
  `avg_sentence_words` and `max_sentence_words` figure quoted from a
  pre-0.6.0 run is stale.
- A corpus entry may declare `case_sensitive: true`: its pattern and its
  exceptions then compile without `re.I`. That is what a placeholder-name
  rule needs, so `\b(Lyra|Eira|Jaxon|Elias)\b` now carries it and the LYRA
  pencil brand in a household catalog stops reading as an invented
  character. Matching stays case-insensitive without the key, and a value
  that is neither `true` nor `false` is a setup error.
- `respeak-measure.py --config` is documented in the module docstring and
  in `--help`. A run without it reads neither the project's `gate.allow`
  nor its `style.budgets`. A hand audit then over-counts any project that
  has tuned either: on one site's baseline, 36 reported errors against 13
  real ones. The help text names the `respeak-config.sh resolve` command
  that writes the file to pass.
- The verifier counts every line MkDocs would render as a heading. The old
  rule needed a space after the hashes, so a hard-wrapped line beginning
  `#33256` published as an H1 while the verifier passed the edit. A
  heading is now any line matching `^ {0,3}#{1,6}` outside fences, plus
  setext headings; a backslash-escaped `\#` is not one, which is the fix
  for a wrap that has to keep a number at the line start.
- New Markdown failure class, `block structure changed: <kind> N -> M`.
  Outside fences the verifier counts blockquote lines, bullet items,
  ordered items, thematic breaks, table rows, and definition lines, and
  reports each kind whose count moved. Ordered items count anywhere for
  `1.` or `1)` and only at a block start otherwise, because only `1.` can
  interrupt a paragraph. `--allow-restructure` reports the class as a
  warning instead.
- `--allow-strings` verifies an editorial pass over a page generator,
  whose display text lives in string literals. Both `.py` files are parsed
  with `ast` and every string constant is masked, so the two trees must
  still dump identically: a new dict entry, a changed call, a moved
  statement, or a changed number fails. Paired strings may then differ
  only with their numbers, `%` placeholders, `{}` fields, URLs, link
  targets, and inline code spans intact, and a docstring carrying `>>>`
  stays byte-identical.
- `--prose-keys KEYS` opens the display prose in Markdown front matter and
  in `.yaml` catalogs. KEYS is a comma-separated list of leaf key names,
  or `*` for every string leaf. Structure, key order, every unlisted
  value, and each scalar's quoting style stay invariant, and a listed
  string keeps its numbers, URLs, inline code spans, and link targets. For
  Markdown this replaces the whole-front-matter failure; the body is
  checked as before.
- `--dirs BEFORE AFTER` verifies two rendered trees, which is how an edit
  to a generator is proved at the level the reader sees. Every file both
  trees hold whose bytes differ is verified by its extension, and a type
  with no policy is SKIP rather than FAIL. A file on one side only is
  ADDED or REMOVED, and identical bytes are UNCHANGED. The output is one
  line per file plus a summary, or `--json` for the rows as a list, and
  exit 1 if any file fails.
- Eight corpus entries gain exceptions for the literal sense that tripped
  a real family page. `\bsymphony of\b` clears a Castlevania title,
  printed on 21 pages of a game catalog; `\bshowcas(e|es|ed|ing)\b` an
  in-game panel named that; `\bseamless(ly)?\b` a named fan project.
  `\bjourney\b` clears a Dragon Quest subtitle, `\bindelible( mark)?\b` an
  event name. `\bunderscor(e|es|ed|ing)\b` clears the literal character,
  and a sentence naming another separator or a filename beside it.
  `tapestry` clears the horticultural senses, `crisp` the food, texture
  and weather senses. Each exception is tested against the sentence window
  around the hit, so the cliche still flags.
- `^-{3,}$` (thematic break) and `[“”]` (curly quotes) move to
  `tier: density`. A generator or a vendored footer emits one per page, so
  per-occurrence counting made them the top warn on every site. 539 of one
  site's 565 break hits were the catalog card rule. 296 of another's quote
  hits sat inside publisher blurbs the pass must not reword. A
  density-tier hit no longer counts toward `warn_hits`; it counts toward
  `density_hits` and the `warn_phrases_per_1000_words` budget.
  `--fail-on warn` still trips on one, so a page whose own prose is
  littered with them still fails.
- New `tests/test_corpus.py`, 11 tests that scan the shipped corpus with
  the sentences the site pass met. For each exempted entry the literal
  sense passes and the cliche still flags; both retiered rules land in the
  density bucket; the stock-name entry matches with case.
- `agents/respeak.md` gains editorial-pass rules 5 to 12, the behaviors
  the field run showed the contract did not forbid. Never add, delete or
  correct a factual claim; report it instead. Rewrap without starting a
  line with `#` or `>`. Prose-to-list and list-to-prose count as
  restructure. Template and generator layout is advisory-only. A UI label
  gets the minimal compliant edit, never a rename. A generator edit
  changes string-literal content only, proved with `--dirs` and
  `--allow-strings`. Third-party text is never reworded, only reported
  with a proposed attribution. A banned term inside a heading needs
  `restructure: apply`.
- `scripts/respeak-check.sh --verify` reads each changed file's resolved
  `editorial_pass` and passes the verifier what it allows. `restructure:
  apply` becomes `--allow-restructure`, the new `verify.prose_keys` becomes
  `--prose-keys`, and `verify.allow_strings` becomes `--allow-strings`.
  `verify.paths` (git pathspecs) names the page generators and data files
  the check verifies as well, though never gates. The same three flags on
  the command line apply to one run. A `--prose-keys` violation is its own
  failure class, `front matter prose`, so it stays hard when
  `--allow-restructure` relaxes an unnamed front-matter change.
- The installed copy under `~/.claude/plugins/cache` is a snapshot, so run
  `claude plugin update respeak` to pick up the new gate behavior and the
  corpus changes.

## 0.5.2 (2026-09-15)

- The README status section is rewritten through the translator itself: a
  table of surfaces and their state, the unenforced config keys as a list,
  and version history delegated to this file. Its former heading announced
  honesty instead of showing it, and its first sentence ran 136 words.
- `scripts/respeak-check.sh`: the CI form of the gate. It runs the hook's
  verdict over every Markdown file git knows about, ignores session overrides on
  purpose, and with `--verify <ref>` requires each edit since that ref to be
  meaning-invariant. 16 checks in tests/test_check.sh, one of which is
  this repository's own docs passing its own gate.
- The repository configures respeak on itself: `.claude/respeak/config.yaml`
  names the human lane (README, CHANGELOG, CLAUDE.md, docs/) as a scope in
  technical mode for a peer engineer with structure advised, never applied;
  `CLAUDE.md` states how a session edits and checks those files and imports
  the lexicon digest generated from the corpus.
- The whole README went through the translator's editorial pass in
  technical mode: sentences over 25 words split, em-dashes removed from
  prose, walls of text broken at their seams. Every heading, link, code
  block, code span, and number is byte-identical to before, as checked by
  `respeak-verify-edit.py`. Average sentence length fell from 23 to 15
  words.
- The corpus rule for "the honest (assessment|take|answer|read)" now also
  catches "honest (status|update|summary|look)", with or without an
  article. Same category, same severity; the phrase count is unchanged.

## 0.5.1 (2026-09-15)

- `/respeak:report` runs a privacy pass on every report: identifying
  details (names, addresses, usernames, hosts, home paths, organizations,
  identifiers, anything token-shaped) are replaced with neutral
  placeholders, and the user confirms nothing privileged remains before the
  post. The environment footer shows a python under the home directory as
  `~/...`.
- A black-and-white megaphone icon at `assets/respeak-icon.svg`, shown at
  the top of the README.
- Every translation opens with a `📣 respeak · <mode>` marker line (the
  translator emits it, the skill relays it, the Stop-hook nudge asks for
  it), so a reader can tell the translator's voice from the agent's own.
  The headless renderer strips it from output files.

## 0.5.0 (2026-09-15)

- The PostToolUse style gate hook is registered again in `hooks/hooks.json`.
  A follow-up to 0.4.3 had removed it for one person's convenience, which
  made every documented gate knob a no-op for every installer. A test now
  pins the manifest's event list.
- Session overrides, above every configuration layer: `/respeak:off [gate]`
  and `/respeak:on [gate]` write a per-session marker; `RESPEAK_HOOKS=off`
  and `RESPEAK_GATE=off|on` do the same for one launch. Precedence is
  marker, environment, then configuration. `respeak-config.sh explain`
  ends with the override in force. Contract: docs/config-layers.md.
- `/respeak:report` files a GitHub issue against this repository through
  the GitHub CLI, with an environment footer and nothing from the project
  unless the user opts in and confirms.
- The SessionStart hook speaks only in projects with `.claude/respeak/`,
  uses the found interpreter, and reports counts correctly.
- The Stop hook whitelists the mode, profile, and tech level it puts into
  the model's context.
- The headless renderer drives Claude Code's print mode (`claude -p`);
  `RESPEAK_RENDER_CMD` and `RESPEAK_RENDER_MODEL` substitute a runner or
  model. `--budget-usd` is gone; `--max-rounds` bounds the spend.
- MIT license, with attributions for the condensed Wikipedia catalog
  (CC BY-SA 4.0) and the antislop-sampler influence (Apache-2.0). The
  manifest carries `license`, `author`, `homepage`, and `repository`.
- Documentation clean-room: install instructions use the GitHub
  marketplace form, example paths are placeholders, wording is neutral,
  and the research primer on Claude Code extension surfaces is rewritten
  for readers outside the project. The unpublishable field-test source
  documents are removed; the README keeps the measured numbers as sizing
  evidence.

## 0.4.3 (2026-09-04)

- Paths compare by key: symlink-resolved, case- and NFC-folded on macOS and
  Windows; a symlinked user config directory can no longer become the
  project root; in-project symlinks pointing outside are still gated.
- The interpreter cache moves to a trust-bounded directory under
  `${XDG_CACHE_HOME:-~/.cache}/respeak`; a tampered cache can at worst pick
  another known interpreter.
- `--set` reads boolean spellings on boolean keys; the statusline survives
  spaces in paths; skill commands are quoted; the scanner reads stdin.
- Follow-ups: the spaced-plugin-path limit is documented and announced at
  session start; this repo's own layered tone config is added.

## 0.4.2 (2026-09-04)

- Every measure setup error exits 2, so the gate fails open on a corrupt
  corpus, an invalid `gate.allow` regex, or a non-UTF-8 document instead of
  blocking with a traceback.

## 0.4.1 (2026-09-04)

- One project-root rule for every consumer; the user file is never promoted
  to project grade; symlink-safe path comparison; hooks fail open on setup
  errors; a Markdown-only gate contract; `allowed-tools` on the skills so
  the preamble runs under default permissions.

## 0.4.0 (2026-09-04)

- Layered configuration, nearest to the target wins: plugin defaults,
  install-time userConfig, user file, ancestor folder files, project file
  and gitignored local file, `scopes:`, folder files, `RESPEAK_CONFIG`,
  invocation flags. `scripts/respeak-config.py` resolves it; every hook,
  the skill, the statusline, and the headless renderer read through it.
- Governance keys are project-only. Audience profiles are expanded by the
  resolver. `/respeak:init` seeds a sparse project file.

## 0.3.0 (2026-09-02)

- Enforcement instead of instruction: `respeak-measure.py` gains
  `--fail-on`, budgets, `gate.allow`, per-entry exceptions, and JSON
  output; the PostToolUse gate hook blocks a failing Markdown write with the
  report; the skill verifies before relaying; the agent gates its input.

## 0.2 (2026-09-01)

- First release: governed shorthand lexicon with human ratification, the
  translator subagent with eli5, bluf, and technical modes, the banned-phrase
  corpus with provenance and density tiers, the style scanner, the
  format-aware edit-safety verifier, the lexicon digest renderer, and the
  statusline segment.
