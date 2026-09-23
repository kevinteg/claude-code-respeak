# Packet R9: the README r7 (public source, status line, the icon at the shared path)

| item | value |
|---|---|
| from | the owner (2026-09-23 12:35): "a rich README per repo, generating high quality respeaked public facing docs with nice project icons like what we have for respeak"; conventions §6 as `CLAUDE.md` carries it; `design/readme/source.md` whole (its facts stand, its words go); `plugin/.claude-plugin/plugin.json`; every `plugin/skills/*/SKILL.md` frontmatter; the script headers under `plugin/scripts/` and `scripts/`; the icon family rules in §2; the STANDING WORD |
| pin | `main` at `2c8ec97` or later. Branch `r9-readme-r7`, worktree `.claude/worktrees/r9-readme-r7` off it |
| wall | this repo only; no push, `--amend`, rebase, device, tag, version bump, `make install`; no network but the render's own `claude -p`; `make readme` at most twice, counted; the canonical scripts untouched |
| may touch | `design/readme/source.md`; `README.md` and `design/readme/rendered.sha256` by `make readme` only; `scripts/readme-render.sh`; `tests/test_render.sh`; `CHANGELOG.md` (one bullet under `## Unreleased`); `assets/icon.svg` by `git mv` from `assets/respeak-icon.svg`; new: `docs/references.md`, `tests/test_readme.py`, the charter. Nothing else |
| acceptance | the lines of §6, targeted, each under a minute |
| verify | `make check` |
| budget | 60 turns, 144k context; one commit per act; the charter's open names doclint's five rows; checkpoint at 80% |

## 1. What the source says (quoted)

`CLAUDE.md`: "The source stays at or under 24,576 bytes". The renderer's header: "a README source keeps its icon line (the HTML img) under the title, never above it: above the title, the strip would remove it". Conventions §6: "A README names dependencies by id and range, nothing else outside the repo; no owner path, address, domain, private repo or person in any tracked file". The icon generator: "filled shapes only: gradients die on zero-extent stroke bboxes".

## 2. Rulings (decided inside the design; the charter records each with its consumer)

1. The source is the finished public document, in this order: the title; `<img src="assets/icon.svg" alt="" width="56" align="left">` on line 3; two sentences of what; "Why it exists" (a household runs several Claude Code plugins in unattended relay runs; agents write to each other in ratified shorthand to spend less context, and every person reads a narrative in their own mode; respeak is both lanes, the loop and the gate); "What respeak does" (the lanes, the loop, the mode table); "Does it work?" (the field-test table); "Install" (the marketplace lines, `make install` from a checkout, `make doctor`, the `--plugin-dir` try, `/respeak:init`); "Commands and skills" (the five skills and the `respeak:respeak` agent, one example each; the scripts a reader runs); "Enforcement" cut to the gate, the scanner and CI; "Where the tone comes from" (the layers table); "Design of record" (`docs/architecture.md`, `research/synthesis/design-principles.md`, the packets, the charters' handovers); "Tests" (targeted lines by file, then `make check` and its parts); "Conventions shared with the sibling plugins" (`scripts/hygiene` and `scripts/doclint` byte-identical across them, the README sidecar; the session plugin by its id `claude-code-session` and range, major 2, as the optional provider; no other sibling, no path); "What can go wrong"; "Status" (the status line first); "Layout"; "License" (MIT). References move whole to `docs/references.md` under a one-line intro; "Design of record" links it. Every fact from the tree.
2. The status line, first under `## Status`: `Status: version \`0.6.1\`, rendered \`YYYY-MM-DD\`, \`N\` unittest cases and \`M\` bash suites.` `scripts/readme-render.sh` writes it into the source before each render from the manifest's `version`, today's date, `unittest.defaultTestLoader.discover("tests").countTestCases()` and the count of `tests/*.sh`; a source without a `Status: version` line exits 2. The contract keeps code spans and numbers byte-identical, so the render cannot drift them.
3. The icon: the megaphone is the family's anchor, so the glyph stays and the file moves to `assets/icon.svg`, the path the four plugins share. The family rules, restated: one 64-box, the glyph centered; monoline `stroke="currentColor"` width 3, round joins and caps; closed shapes filled `#fff`; no gradient, filter, script or external reference (the gotcha: a gradient paint dies on a stroke whose box has zero extent, so a line is a `currentColor` stroke, never a gradient); `role="img"`, `aria-label`, `<title>respeak</title>`; under 1,500 bytes. No PNG: the generator writes SVG masters only. Eyeballed once in Chrome.
4. Hygiene: `README.md` and `design/readme/*` keep `sibling,person` (the plugin's name, the marketplace account), nothing wider; `docs/references.md` sits under the `docs/*` row. No home path, no `../` sibling path, no sibling id but `claude-code-session`.
5. The render: measure the source locally (`respeak-measure.py --fail-on error`, every budget PASS) until it reads clean, then `make readme`; today's source reads FAIL on `max_sentence_words` (46, budget 35). Two failed renders: commit the source, leave the README stale, report. The source, the README and the sidecar land in one commit.
6. Acts: (1) the source, `docs/references.md`, `tests/test_readme.py`; (2) the icon move; (3) the status step and its two cases in `tests/test_render.sh`; (4) the render last, so the line carries the suite's final count, with one CHANGELOG bullet in the file's shape (what changed, then "The failure:").

## 3. Interfaces (signatures, not prose)

- `scripts/readme-render.sh [--repo DIR] [--plugin-root DIR]`: the status step first; exits 0 written and stamped, 1 the style gate after the renderer's rounds, 2 setup, the verifier, or `readme-render: no status line in design/readme/source.md`.
- The line: `^Status: version \`[0-9.]+\`, rendered \`[0-9]{4}-[0-9]{2}-[0-9]{2}\`, \`[0-9]+\` unittest cases and \`[0-9]+\` bash suites\.$`, once per file.
- `tests/test_readme.py`: the status line against the manifest and a live collection; the icon on line 3 and plain (no `url(#`, `viewBox="0 0 64 64"`, a `<title>`); the source under 24,576; the `## ` lines of both files equal; no `../` and no sibling id but `claude-code-session` in either.
- `tests/test_render.sh`: a fixture with a manifest and a status line renders a README whose line names the manifest's version; a fixture without the line exits 2, `README.md` untouched.
- `docs/references.md`: `# respeak references`, one intro line, the six groups byte-identical to today's section.
- Commits `r9 act N: <one line>`; the charter title `# Sitting <run day>-<n>: claude-code-respeak, r9-readme-r7`.

## 4. Findings that name this row

On `main` `2c8ec97` under the virtualenv (3.12.7): `make check` 0, `readme: fresh`; 219 unittest cases collected in 0.1 s, 10 bash suites; `tests/test_render.sh` 26 passed, and it already renders a fixture with a fake `claude`; the source 21,758 bytes, 14 sections, References 5,335 of them; the measure gate on the source: 0 error hits, FAIL `max_sentence_words` 46; the public-group scan (every group but `person` and `sibling`) over the README and the source reads 0; the only sibling id in either is `claude-code-session`, once each; `assets/respeak-icon.svg` 654 bytes, no `url(#`, `<title>` `respeak`; Chrome is installed.

## 5. Forbidden reads

Every other repo (§2 carries the family rules). `research/`. `CHANGELOG.md` beyond its first 40 lines. `history/` beyond the builder's charter. The relay's ledgers; any transcript. No file over 8 KB whole but `design/readme/source.md`, once, to rewrite it; `README.md` never (it is rendered).

## 6. Report (capped: one table, at most six bullets, under 1,500 words)

Each line's last output, `main` beside the branch:

| line | main | branch |
|---|---|---|
| `$PYTHON -m unittest tests.test_readme 2>&1 \| tail -1` | no module | `OK` |
| `bash tests/test_render.sh 2>&1 \| tail -1` | `26 passed, 0 failed` | at least 28 passed, 0 failed |
| `bash scripts/readme-fresh.sh` | `readme: fresh` | `readme: fresh` |
| `sed -n 3p README.md \| grep -c 'src="assets/icon.svg"'` | 0 | 1 |
| `grep -c 'url(#' assets/icon.svg; test -f assets/respeak-icon.svg; echo $?` | no such file | 0 1 |
| `grep -c -E '^Status: version .0\.6\.1., rendered .2026-[0-9-]{5}., .[0-9]+. unittest cases and .[0-9]+. bash suites\.$' README.md` | 0 | 1 |
| the §4 public-group scan over `README.md` and `design/readme/source.md` | 0 | 0 |
| `grep -c -i -E 'syrvis\|claude-code-agents\|agent-relay\|\.\./' README.md design/readme/source.md` | 0 0 | 0 0 |
| `grep -c 'docs/references.md' README.md; grep -c '^## ' README.md` | 0 14 | 1, the source's count |
| `git status --short \| wc -l \| tr -d ' '` at the end | 0 | 0 |

Bullets: each act's commit; the render count and what the gate or the verifier refused; the icon's glyph and why; the status line as rendered; what the public source says that the old one did not; at most ONE open fork. Last line: the branch and its head sha.
