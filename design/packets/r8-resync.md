# Packet R8: the post-S10 re-sync, repo-relative rows, check under a bounded runner

| item | value |
|---|---|
| from | claude-code-session `design/conventions.md` §5, §6 and §9 at its `main` `68c76cb`; the S10 charter's re-sync line; the owner's rulings 2026-09-23 14:55, items 1 and 5 |
| pin | claude-code-respeak `main` at `5f571b3` or later. Branch `r8-resync`, worktree `.claude/worktrees/r8-resync` off it. The copy source is the session checkout beside this one, `S=$(dirname "$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")")/claude-code-session`, read as three blobs by `git -C "$S" show 68c76cb:scripts/<name>` and nothing else there |
| wall | this repo; no push, `--amend`, rebase, device, tag, version bump, `make readme`; the canonical scripts are copied, never edited; a merged packet or charter is a record, never rewritten |
| may touch | `scripts/hygiene`, `scripts/doclint`, `Makefile`, `.hygiene-allow`, `.gitignore`, `CHANGELOG.md` (one bullet under `## Unreleased`), `plugin/docs/config-layers.md` (one cell), `examples/layered/README.md` (one cell), every `design/packets/rows-*.json`; new: `scripts/bounded`, `tests/test_bounded.sh`, the charter. Nothing else |
| acceptance | the lines of §6 with their baselines, targeted, each under a minute |
| verify | `make check` |
| budget | 60 turns (act 1 is one commit gated by a measurement, act 2 edits eight files, act 3 adds a suite), 144k context; one commit per act; the charter's open names doclint's five rows; checkpoint at 80% |

## 1. What the source says (quoted)

Conventions §5: "`check` runs under `scripts/bounded` (one per tree by lock `.check.lock`, a 900 s wall, held off above load 4 x cores)"; "A packet's `verify` row is the gate line (`make check`); acceptance lines are targeted". §6: "Every copy of `scripts/hygiene` has sha256 `ca0496350e89ee814de71d6c352e6e6be7239a8dbe75391eeb752428f3e36cb1`, of `scripts/doclint` `3040666c1e9ad08faf1befe9c2efffaff0660f0464554d240f1d07437a03fcda`"; "no owner path, address, domain, private repo or person in any tracked file". The S10 handover: "`.local` only after a hostname"; "re-sync (decisions, respeak, agent-relay): hygiene ca049635..., doclint 3040666c..., `email` allow rows, a `verify` row in new packets, `scripts/bounded` for `check`". Ruling 1: "run 7's re-sync makes the rows repo-relative and the allow file drops the home and private groups". The stand-in's docstring: "repo (~ allowed); prompt (a path, relative to the repo unless absolute)".

## 2. Rulings

Act 1, the re-sync, ONE commit so `make hygiene` never reads red at a commit. `scripts/hygiene` and `scripts/doclint` byte-identical to the two blobs; the Makefile pins (`HYGIENE_SHA`, `DOCLINT_SHA`) move to the two shas of §1 in the same commit. The new hygiene's findings here (§4), each settled inside conventions §6, the canonical copy untouched: `.hygiene-allow` gains `email` on `plugin/scripts/*` (a comment's SSH URL form), `tests/*` (fixture addresses) and `research/sources/*` (a quoted example address); `tests/*` also gains `lan` (a fixture method named `.local(`); three `sibling` rows for the example fixtures whose file name is the plugin's own, `examples/layered/project/docs/api/*`, `examples/layered/project/docs/exec/*` and `examples/layered/project/notes/*` (the new scan reads path names). The one table cell in `plugin/docs/config-layers.md` and in `examples/layered/README.md` that names the local config file by its short form (the name without `.yaml`) is written as the full file name, `config.local.yaml` (the `.local` rule takes the short form for a hostname; the full name is what the cell means; under ten lines, the gate is the pass). No `lan` exception on a public doc.

Act 2, repo-relative rows (ruling 1). Every `design/packets/rows-*.json` carries `"prompt": "design/packets/<packet>.md"`; keys, order and every other value stay byte-identical, `repo` included: the stand-in resolves a relative prompt against `repo`, and `repo` is a `~` path by its contract. `.hygiene-allow`: the `design/packets/*` row becomes `design/packets/*.md: sibling,person`, `design/packets/rows-*.json: sibling,person,home` (the `repo` field) and `design/packets/r5-resync.md: home` (a merged packet is a record; its three copy lines name the session checkout by a home path); the header comment says a directory that mixes records and rows carries one glob per kind. The sittings row keeps `private`: measured, five charters name the private repos in their pin rows; a charter is a record. Say so in the charter.

Act 3, `check` under a bounded runner. `scripts/bounded` copied verbatim from the third blob (sha `e6079e68087d241f7af18c5b466bd4a8a56f9d6877cbc40d79fbc5fe5b62d90a`), unpinned: §6 pins two scripts; the Makefile comment names it a copy of the session's. `check` becomes `$(PYTHON) scripts/bounded --lock .check.lock --wall 900 --load 4 -- $(MAKE) check-unlocked`; `check-unlocked` is today's dependency list; `.PHONY` gains it; `.gitignore` gains `.check.lock*`. `respeak-deadline.sh` stays where it is (the suites, `validate`, the plugin's spawns): it ships in the plugin and is bash; `scripts/bounded` is repo tooling. New `tests/test_bounded.sh`, the repo's bash-suite shape, under the deadline like the others: `--wall 1 -- sleep 30` with `BOUNDED_GRACE=1` exits 124 in under 5 s with no survivor; a lock held by a live pid refuses with 2; a command's own exit passes through (`sh -c 'exit 7'` is 7). One CHANGELOG bullet for the row, in the file's shape (what changed, then "The failure:").

Later: a bare repo name in rows, resolved by the relay against the checkout beside it, would retire the rows row's `home` (the agent-relay packet writer); pinning `scripts/bounded` is conventions' call (the next re-sync).

## 3. Interfaces (signatures, not prose)

- `make check`: `scripts/bounded --lock .check.lock --wall 900 --load 4 -- make check-unlocked`; the gate's own exit, 124 at the wall, 2 when the tree's lock is held by a live pid or the load stays above 4 x cores for 600 s, 127 when it cannot start.
- `scripts/bounded [--lock DIR] [--wall S] [--load N] -- cmd...`: its docstring is the contract (`BOUNDED_GRACE`, `BOUNDED_LOAD_POLL`, `BOUNDED_LOAD_MAX`, `BOUNDED_LOADAVG` for tests).
- A rows file's row: `prompt` repo-relative, `design/packets/<packet>.md`; `repo` a `~` path.
- `.hygiene-allow` rows added or changed: `plugin/scripts/*: sibling,email`, `tests/*: sibling,lan,email`, `research/sources/*: sibling,email`, the three example rows, the three `design/packets` rows.
- Commits `r8 act N: <one line>`; the charter title `# Sitting <run day>-<n>: claude-code-respeak, r8-resync`.

## 4. Findings that name this row

On `main` `5f571b3` under the virtualenv (3.12.7): `make check` 0 (219 unittest cases; the bash suites 40, 12, 56, 32, 11, 43, 11, 26, 19 passed; respeak-check 43 passed, 18 skipped). Today's hygiene reads 0 outside the allowlist; the session's copy from this root reads 15 in 11 files: `lan` 5 lines in 3 files (the short form of the local config file's name in two table cells, the fixture's `local(` method three times in `tests/test_config_layers.py`), `sibling` 3 (the three `.respeak.yaml` fixtures by path name), `email` 7 in 5 files (the four tests and scripts of act 1, one research source). The session's doclint reads 0 here. `home` under `design/packets/`: 10 lines in 8 files (seven rows files, five of them with an absolute prompt; `r5-resync.md` lines 6, 25 and 57). `private`: 5 lines, all under `history/sittings/`. `git rev-parse --path-format=absolute` works (git 2.50). Load about 5.5 on 16 cores; the breaker's ceiling is 64. `sitting-relay plan` on a one-row file fails on `depends_on` alone, so no plan line is an acceptance line.

## 5. Forbidden reads

Every other repo beyond the three blobs of the pin row. `research/` beyond the one allow row. `examples/` beyond the one cell and the three fixture directories' names. `CHANGELOG.md` beyond its first 40 lines. `history/` beyond the builder's charter. The relay's ledgers; any transcript.

## 6. Report (capped: one table, at most five bullets, under 800 words)

Each line's last output on the branch beside `main` at this packet's commit:

| line | main | branch |
|---|---|---|
| `shasum -a 256 scripts/hygiene scripts/doclint \| cut -c1-8 \| paste -sd' ' -` | `d9e99149 4318bc91` | `ca049635 3040666c` |
| `make hygiene 2>&1 \| tail -1` | `hits outside allowlist: 0` | `hits outside allowlist: 0` |
| `grep -c '"prompt": "design/packets/' design/packets/rows-*.json \| grep -c ':0$'` | 5 | 0 |
| `grep -cE '^design/packets/' .hygiene-allow; grep -c 'sittings/\*.md: private' .hygiene-allow` | 1 1 | 3 1 |
| `grep -c 'scripts/bounded --lock .check.lock --wall 900 --load 4' Makefile` | 0 | 1 |
| `shasum -a 256 scripts/bounded \| cut -c1-8` | no such file | `e6079e68` |
| `bash tests/test_bounded.sh 2>&1 \| tail -1` | no such file | at least 3 passed, 0 failed |
| `git status --short \| wc -l \| tr -d ' '` after the last commit | 0 | 0 |

Bullets: each act's commit; choices beyond §2 with reasons; what was left undone and for whom; at most ONE open fork. Last line: the branch and its head sha.
