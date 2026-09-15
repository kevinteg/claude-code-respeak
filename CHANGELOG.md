# Changelog

Versions follow `.claude-plugin/plugin.json`. Dates are commit dates.

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
