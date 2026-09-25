# Packet R15: the README renderer runs as a marked helper (relay-r1 §10)

| item | value |
|---|---|
| from | agent-relay `design/relay-r1.md` §10 at its `main` after `ar25c-fixes-adv15` merged; `scripts/readme-render.sh`; `scripts/readme-fresh.sh`; `tests/test_render.sh`; `CHANGELOG.md` `## Unreleased` |
| pin | this repo's `main` at the row's start; branch `r15-resync` off `main` (no `base`); worktree `.claude/worktrees/r15-resync` |
| wall | this repo only; agent-relay read only. Public repo: no private repo name, home path or personal name in any file. No push, `--amend`, rebase, device or network. Tests set `HOME`, `XDG_CONFIG_HOME` and `XDG_STATE_HOME` to temp dirs; no live `claude` in a test. Never `relay plan` or `run` without `--rows` and a temp `XDG_STATE_HOME`. Logs go to `mktemp` |
| may touch | `design/packets/r15-resync.md`, `scripts/readme-render.sh`, `scripts/readme-fresh.sh` (if it names the helper), `tests/test_render.sh`, `CHANGELOG.md` (one bullet), `design/readme/source.md`, `README.md`, `design/readme/rendered.sha256` (these three by `make readme`), `history/sittings/*.md`. Nothing else |
| acceptance | `grep -c 'CLAUDE_SESSION_HELPER=1' scripts/readme-render.sh` reads 2 or more; `grep -c 'refused past depth 2' scripts/readme-render.sh` reads 1 or more; `grep -c 'env -u' scripts/readme-render.sh` reads 0; `sed -n '/^## Unreleased/,/^## [0-9]/p' CHANGELOG.md \| grep -c 'CLAUDE_SESSION_HELPER'` reads 1 or more; `grep -c 'CLAUDE_SESSION_HELPER' tests/test_render.sh` reads 2 or more; `bash tests/test_render.sh 2>&1 \| tail -1 \| grep -c ', 0 failed'` reads 1; `python3 -m unittest tests.test_readme 2>&1 \| tail -1` reads `OK`; `shasum -c --status design/readme/rendered.sha256` exits 0; `make doclint` exits 0; `make hygiene` exits 0; `grep -c '^# Packet R15:' design/packets/r15-resync.md` reads 1; `git diff --name-only --diff-filter=A main...HEAD -- history/sittings \| xargs grep -cE '/Users/[a-z]\|~/cod[e]/\|filled at close'` reads 0; `git status --short \| grep -c .` reads 0 |
| budget | 50 turns, 144k context, `claude-opus-5-5` (`--max-turns 50`); one commit per act; `make check` in the foreground, then commit in the same turn; checkpoint at 40 turns: land the act in flight, close |
| verify | `make check` |

## 1. What the source says (quoted)

relay-r1 §10, expected: "a helper a sitting spawns keeps `RELAY_ROW` and `CLAUDE_SESSION_MAX_TURNS`, runs in the foreground as `CLAUDE_SESSION_DEPTH=$((d+1)) CLAUDE_SESSION_HELPER=1 claude -p … --max-turns N`, and is refused past depth 2; Stop and `start.json` skip it; `DropSitting` is the relay's own helpers' alone". The text on agent-relay's `main` wins where they differ.

## 2. Rulings

You are headless (`claude -p`): the sitting ends the moment your turn ends. Never delegate an act to an agent, never start a background command or a background agent, never end a turn waiting for a notification. Do every act yourself, in the foreground, and commit it before the next act starts.

Paths are repo-relative. `M` is the main checkout (`git rev-parse --path-format=absolute --git-common-dir`, less `/.git`), `P` its parent. No worktree yet (not a relay row): `git worktree add .claude/worktrees/r15-resync -b r15-resync main` in `M`. `python3` is the virtualenv `.python-version` names. At most ONE fork, for the owner; no NEXT.

0. **Copy-in, first.** Your packet is `relay/prompts/2026-09-24-r15-resync.md` in the orchestrator's private checkout under `P` (the row's `prompt`; `ls "$P"/*/relay/prompts/2026-09-24-r15-resync.md` finds it). Copy it verbatim to `design/packets/r15-resync.md` (`cp`, `cmp`); commit that file alone.
1. **Charter, rule text.** Open `history/sittings/2026-09-24-<n>.md` (next free n), `# Sitting 2026-09-24-<n>: claude-code-respeak, r15-resync`: doclint's five rows (goal, budget, pin, window, agents), `## Done-ness`, `## Handover`, `## Next act`. In a subshell `cd "$P/agent-relay"` (a relay row refuses `git -C`): `git log -1 --format=%h main -- design/relay-r1.md`; `git show main:design/relay-r1.md` to a `mktemp` file; cut §10's sentence, `a helper a sitting spawns keeps` through `own helpers' alone`, to a `mktemp` file `S`. Record the sha, `S`'s sha256 prefix. `S` empty: close the charter ("no helper rule at <sha>"), stop. Commit.
2. **The rule.** `scripts/readme-render.sh`: the `respeak-render.sh` line gains `CLAUDE_SESSION_DEPTH=$((d + 1)) CLAUDE_SESSION_HELPER=1`, d being `CLAUDE_SESSION_DEPTH` (unset or empty: 0); `RELAY_ROW` and `CLAUDE_SESSION_MAX_TURNS` pass through; `plugin/scripts/respeak-render.sh` stays. In setup, before any write: d not a plain non-negative integer, or d + 1 over 2, exits 2. Its comment quotes `S` verbatim on one line, citing relay-r1 §10 at the sha; the header's exit 2 names it. `readme-fresh.sh` changes only if it names the helper. Tests in `tests/test_render.sh`, by the readme-render cases: d = 1, the fake `claude` sees depth 2, `CLAUDE_SESSION_HELPER=1`, `RELAY_ROW` and `CLAUDE_SESSION_MAX_TURNS` as given; d = 2, exit 2, no runner call, nothing written; each red on `main`. A `CHANGELOG.md` bullet under `## Unreleased` names the rule (`CLAUDE_SESSION_HELPER=1`). One commit.
3. **README, only if act 2 moved the suite's count.** `make readme` once (the new helper); `make check` green; commit. A failed render leaves README.md untouched: commit the source, name it (the fork).
4. **Close.** The charter closed, under 4,096 bytes, no home path, before the last commit. Commit.

## 3. Interfaces (signatures, not prose)

`scripts/readme-render.sh`: exit 2 before any write when d + 1 > 2. Commits `r15 act N: <one line>`.

## 4. Findings that name this row

On `main` `3c1f63d`: `scripts/readme-render.sh` 77 runs the renderer unmarked, so its `claude -p` reads as a sitting; since ar25b Stop skips only a marked helper.

## 5. Forbidden reads

Other repos beyond this packet and relay-r1 §10; ledgers, transcripts; `history/` beyond your charter.

## 6. Report (capped)

Each acceptance line's exit and last line; the sha, `S`'s prefix; each test red on `main`; `make readme` or not; the fork. Last: branch, head sha.
