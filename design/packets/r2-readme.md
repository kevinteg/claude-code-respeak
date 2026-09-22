# Packet R2: the README through respeak in claude-code-respeak

| item | value |
|---|---|
| from | claude-code-session `design/conventions.md` §5 (the stale-README refusal), §6 (README via respeak); `design/overhaul-r1.md` §5; `design/plan.md` row 14; `design/packets/r1-respeak-conventions.md` §2 and the R1 handover (`history/sittings/2026-09-22-2.md` on the base branch). The builder reads THIS packet and those only |
| pin | claude-code-respeak branch `r1-respeak-conventions` at `bfdc38a` or later, merged or not. Branch `r2-readme`, worktree `.claude/worktrees/r2-readme` off it |
| wall | this repo. No other repo; no push; no `--amend`; no rebase; no device. `claude -p` is the renderer's runner |
| may touch | new: `design/readme/source.md`, `design/readme/rendered.sha256`, `scripts/readme-fresh.sh`, `tests/test_readme_fresh.sh`. Edit: `Makefile`, `README.md` (written by `make readme` only, never by hand), `CHANGELOG.md`, `CLAUDE.md`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.claude/respeak/config.yaml`, `.hygiene-allow`, `tests/test_overrides.sh`, `tests/test_gate_hook.sh`. Nothing else; anything else is a report line |
| acceptance | the lines of §6 with their baselines; the gate reruns them on the branch |
| budget | 60 turns (plan row 14 says 40; raised: a 40 KB README read once, up to three render rounds), 60k context; commit per item; checkpoint at 80%; never push, amend or rebase |

## 1. What the source says (quoted)

conventions §5: `check` "refuses a `README.md` older than `design/readme/source.md`". §6: "`design/readme/source.md` holds the facts in the technical lane; `make readme` renders `README.md` through the respeak agent in technical mode; the source, not the README, is edited. A README names dependencies by id and range and nothing else beyond the repo". overhaul-r1 §5: "terse ... no prose about the owner's other projects"; "the plugin's own README pipeline". plan row 14: "`make check` 0, README fresh, hygiene 0". The R1 handover: `test_overrides.sh` and `test_gate_hook.sh` "still say bare `python3` and pass only that way"; "remove the `respeak` marketplace, add this repo, reinstall"; "Left undone, as ruled: no version bump or CHANGELOG entry".

## 2. Rulings

The renderer is this repo's `scripts/respeak-render.sh` (wraps `claude -p`, gates its output with the measure script); `make readme` calls it in technical mode; nothing new renders. Nested `claude -p` works inside a Claude Code session (measured 2026-09-22, exit 0), so the builder runs `make readme` itself. Freshness is content, not mtime: git keeps no mtimes, so `design/readme/rendered.sha256` (two `shasum -a 256` lines, the source and the README) is the stamp, `make check` verifies it, and an absent source prints the session's line `readme: skipped, absent design/readme/source.md`, exit 0. The render is an editorial pass: `scripts/respeak-verify-edit.py source README` exits 0, so the source carries every heading, link, code span, number, list item and table row the README will have, and the README differs in prose only. The ceiling is 24,576 bytes, not the session's 6 KB: the research case and References are the plugin's evidence and stay; what goes is prose a linked page already holds (Enforcement, 185 lines today, condenses hardest). Version: `0.6.1` in both manifests (the session pins `^0.6`), one CHANGELOG entry; no tag, no push, the owner's release act. Python: `"${PYTHON:-python3}"` where a suite runs an interpreter for itself; the broken-shim fixture in `test_gate_hook.sh` (lines 164 to 170) tests the hook's finder and stays bare. The marketplace re-registration is README text under Install for anyone who added the marketplace under its old name, `respeak`; the owner reads it there. Cut around: the `plugin/` subtree; `install` and `doctor` (later rows); the editorial pass over the new CHANGELOG entry and CLAUDE.md paragraph, written once and listed for the owner's pass, as R1 did.

## 3. Interfaces (signatures, not prose)

- `design/readme/source.md`: the README's fourteen `##` sections in order, terse, under 24,576 bytes; `## Status (v0.6.1)`; Install gains one paragraph and a fenced block, `claude plugin marketplace remove respeak`, then the `marketplace add` and `install` lines Install already has; Where the tone comes from names `claude-code-session` (major 2) as the optional provider layer, the only id beyond this repo; Layout gains `Makefile`, `design/`, `history/sittings/`, `scripts/hygiene`, `scripts/doclint`, `.hygiene-allow`, `.python-version`. Every link resolves (`scripts/doclint`).
- `Makefile`: `readme:` `bash scripts/respeak-render.sh --mode technical --source design/readme/source.md --out README.md`, then `$(PYTHON) scripts/respeak-verify-edit.py design/readme/source.md README.md` (on failure: `git checkout -- README.md`, exit 2), then `bash scripts/readme-fresh.sh --stamp`. `readme-fresh:` `bash scripts/readme-fresh.sh`. `check: test lint doclint hygiene readme-fresh validate`.
- `scripts/readme-fresh.sh` (bash 3.2, run from the repo root, `[--repo DIR] [--stamp]`): no source, `readme: skipped, absent design/readme/source.md`, exit 0; no stamp or `shasum -a 256 -c --status design/readme/rendered.sha256` fails, `readme: stale, run make readme`, exit 2; else `readme: fresh`, exit 0. `--stamp` writes the two lines with repo-relative paths.
- `tests/test_readme_fresh.sh`: a temporary tree; four verdicts: absent source, fresh, source edited after the stamp, README edited after it; run by the `tests/*.sh` loop.
- `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`: `version` `0.6.1`; nothing else changes.
- `CHANGELOG.md`: `## 0.6.1 (<commit date>)` above 0.6.0, each bullet naming the failure behind it: the session layer (major 2) and `explain`'s provider line; the marketplace name and the re-add lines; `make check` with hygiene and doclint; the pyenv virtualenv; the README rendered by `make readme` with the stamp; the two suites' interpreter.
- `CLAUDE.md`: the human-lane sentence adds `design/readme/source.md`; one new paragraph: the README is rendered, edit the source, run `make readme`, `make check` refuses a stale README.
- `.claude/respeak/config.yaml`: the human-lane scope's `paths` gains `design/readme/**`. `.hygiene-allow`: `design/readme/*: sibling,person`, with a comment (the plugin's name; the repo URL in the install lines).
- `tests/test_overrides.sh` lines 34 and 126, `tests/test_gate_hook.sh` lines 30 and 287: `"${PYTHON:-python3}"`.

## 4. Findings that name this row

The R1 handover's follow-ups are §3's last four bullets. On the base branch under pyenv 3.12.7: `make check` 0 (unittest `OK`, five bash suites, `✔ Validation passed`); the README is 40,089 bytes, fourteen sections, Status heading `v0.6.0`; no `readme` target; both suites carry two bare `python3 -` calls each. `respeak-render.sh` on an absent source exits 2. Outside the wall, named, not done: the session's dependency row `"marketplace": "claude-code-respeak"`; the owner's re-add on this Mac; the tag.

## 5. Forbidden reads

Every repo but this one (§1 quotes the session's records). `~/.claude/projects/` (transcripts hold secrets). `research/` (its links stay as they are). `docs/` beyond `grep -n '^## '` for the sections the source links. `CHANGELOG.md` beyond its first 30 lines (the style). No file over 8 KB whole except `README.md`, once, to condense it. The relay's ledgers. The brief.

## 6. Report (capped: one table, at most five bullets, under 1,500 words)

Each line, its exit and last output on the branch, beside main `c45b5cd` / base `bfdc38a` under pyenv 3.12.7:

| line | main / base | branch |
|---|---|---|
| `make check >/dev/null 2>&1; echo $?` | 2 (no Makefile) / 0 | 0 |
| `make check 2>&1 \| grep -c '^readme: fresh'` | 0 / 0 | 1 |
| `wc -c < design/readme/source.md` | absent | under 24576 |
| `shasum -a 256 -c --status design/readme/rendered.sha256; echo $?` | 1 (absent) | 0 |
| `python3 scripts/respeak-verify-edit.py design/readme/source.md README.md >/dev/null; echo $?` | 1 (absent) | 0 |
| `grep -c '^## ' README.md; grep -c '^## Status (v0.6.1)' README.md` | 14, 0 | 14, 1 |
| `grep -c 'marketplace remove respeak' README.md` | 0 | 1 |
| `grep -c '"version": "0.6.1"' .claude-plugin/plugin.json .claude-plugin/marketplace.json` | 0, 0 | 1, 1 |
| `grep -c '^## 0.6.1 ' CHANGELOG.md` | 0 | 1 |
| `grep -c 'python3 -' tests/test_overrides.sh tests/test_gate_hook.sh` | 2, 2 | 0, 0 |
| `bash tests/test_readme_fresh.sh >/dev/null; echo $?` | absent | 0 |
| `grep -q 'make readme' CLAUDE.md; echo $?` | 1 | 0 |
| `python3 scripts/hygiene && python3 scripts/doclint; echo $?` | absent / 0 | 0 |
| `bash scripts/respeak-check.sh >/dev/null; echo $?` | 0 / 0 | 0 |
| `git status --short \| wc -l` after the last commit | 0 | 0 |

Bullets: the source's bytes and what each section lost, one line each; the render rounds, the model, and any verify failure with its fix; the human-lane edits for the owner's pass (the CHANGELOG entry, the CLAUDE.md paragraph); the owner's re-add lines and the session's dependency row; what was left undone. Last line: the branch and its head sha.
