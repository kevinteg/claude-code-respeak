# claude-code-respeak

This repository ships the respeak plugin and uses it on itself. A session
working here follows these rules.

**The human lane.** `README.md`, `CHANGELOG.md`, this file,
`design/readme/source.md`, and everything under `docs/` are read by people. They are written in respeak technical mode
for a peer engineer; `.claude/respeak/config.yaml` declares that as a scope,
and `respeak-config.sh explain --for <file>` shows it. Skills and agent
prompts are Markdown too and pass the same gate, but their reader is a model.

**Editing a human-lane file.** Do not hand-edit prose in those files. Ask the
`respeak:respeak` agent for its technical-mode editorial pass over the file,
written to a scratch path, then prove the edit changed only prose:

```sh
python3 scripts/respeak-verify-edit.py <before> <after>            # exit 0 = safe
bash scripts/respeak-check.sh --verify HEAD                        # gate + verify every doc git knows about
```

Headings, links, fenced code, inline code, and numbers must be byte-identical
across an editorial pass. New content is written once, then passed the same
way.

**The README is rendered.** `README.md` is written by `make readme` only:
it renders `design/readme/source.md` through the translator in technical
mode, proves the render prose-only with `respeak-verify-edit.py`, and stamps
both files in `design/readme/rendered.sha256`. Edit the source, then run
`make readme`. `make check` refuses a README whose stamp no longer matches.

**The gate is on.** Every Markdown write outside `research/`, `examples/`,
and `corpus/` is scanned by the PostToolUse hook and blocked on an
error-severity hit. `/respeak:off gate` silences it for one session when you
must; say so in the commit message.

**Before committing.** Run `bash scripts/respeak-check.sh` (every doc passes
its own gate) and `make check`. Use `python3` for anything Python: in this
repo it is the pyenv virtualenv `.python-version` declares,
`claude-code-respeak` (3.12, with PyYAML).

**Lexicon.** The ratified shorthand digest below is generated from
`corpus/lexicon.yaml` by `scripts/render-lexicon-digest.sh`; regenerate it
when the lexicon changes. Only ratified terms may be used as shorthand.

@.claude/respeak/lexicon-active.md
