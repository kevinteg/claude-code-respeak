# Packet R10: the ADV10 fixes, a committed-only project file and watchdogs that outlive their parent

| item | value |
|---|---|
| from | `design/review-adv10.md` (ADV10-1, 2, 3, 6, 7); ruling 10 of `2026-09-23-5-decisions` in the relay history (the renderer keeps a file's final newline) and ruling 11 (builders run `make readme` at close); ruling 1 (an account failure stops the run) |
| pin | claude-code-respeak `main` at `e661812` or later. Branch and worktree named by the row id, off it |
| wall | this repo; no push, `--amend`, rebase, device, tag, version bump; no real `claude` beyond `plugin validate` inside `make check` and the one `make readme` of act 5; no test opens a path under the real checkout except the scripts it tests |
| may touch | `CHANGELOG.md` (a bullet per act under `## Unreleased`), `plugin/docs/config-layers.md`, `plugin/scripts/respeak-config.py`, `plugin/scripts/respeak-deadline.sh`, `plugin/scripts/respeak-render.sh`, `scripts/readme-render.sh`, `tests/test_check.sh`, `tests/test_config_layers.py`, `tests/test_render.sh`; in act 5 only, `README.md`, `design/readme/source.md`, `design/readme/rendered.sha256`; the charter. Nothing else |
| acceptance | the lines of §6 with their baselines, targeted, under a minute each |
| verify | `make check` |
| budget | two rows: `r10a-fixes-adv10` builds acts 1 and 2 (60 turns), `r10b-fixes-adv10` acts 3 to 5 (70 turns) after r10a lands; 144k context; one commit per act; the charter's open names doclint's five rows; checkpoint at 80% |

## 1. What the source says (quoted)

ADV10: "a nested project file softens `respeak-check`, and git can hide it"; "every bound moves its child out of the caller's process group and keeps its watchdog inside it"; "the renderer ignores `is_error`"; "a failed `make readme` rewrites `design/readme/source.md`". Ruling 10: "respeak's renderer keeps a file's final newline; rendered READMEs lose it today". Each ADV10 repro is its act's first test, red before the fix.

## 2. Rulings

Act 1, a committed project file (ADV10-1, high). Under `gate --committed`, a project file counts only when git tracks it: `find_project` walks up as today, but an ancestor whose `.claude/respeak/config.yaml` is untracked or ignored (`git ls-files --error-unmatch` fails) is skipped and named in `dropped` as `<path>: untracked project file`; the nearest TRACKED one is the project, read from the index (`git show :<path>`), not the working tree. No tracked one: plugin defaults. Outside a git work tree `--committed` is a setup failure, so `respeak-gate.sh --committed` exits 3. The hook (no `--committed`) keeps the working-tree rule. `config-layers.md` "Trust boundaries" gets one sentence for it. Tests, in `test_check.sh`: ADV10's first test (an ignored `docs/.claude/respeak/config.yaml` at `fail_on: none`, and one at `enabled: false`, leave `docs/bad.md` BLOCKED, rc 1, the drop printed); a tracked nested file whose working copy says `fail_on: none` but whose index copy does not still blocks. In `test_config_layers.py`: the `--committed` CLI case moves into a `git init` fixture with the project file added; new case, outside git, `gate --committed` exits nonzero.

Act 2, watchdogs outside the kill (ADV10-2 and 7, high and low). `respeak-deadline.sh`: the watcher starts in its own process group (`set -m` around its spawn), so a `killpg` of the caller's group does not reach it. It is a one-second loop, not one long `sleep`: each tick it checks `kill -0` on the deadline script's pid and counts toward SECONDS. The script gone, or SECONDS reached, it stops CMD's group: TERM, then KILL after a grace of 2 s (was 5; the inner grace stays under `scripts/bounded`'s 5 s). On CMD's own exit the script kills the watcher's group, so no `sleep` outlives a run (ADV10-7 falls out of the loop). The renderer's runner runs under this script, so `readme-render.sh` inherits the fix. Tests in `test_render.sh`: ADV10's second test for the helper and for the renderer with a sleeping runner (each started under python `os.setsid`, the group SIGKILLed at 2 s, no survivor 5 s later, found by a marker argument in `ps`); three runs of `respeak-deadline.sh 43 true` leave no `sleep 43`; the existing wall case stays inside 7 s.

Act 3, account failures (ADV10-3, medium; ruling 1). `extract_and_write` fails when `is_error` is true or `subtype` is present and not `success`: nothing is written to `--out` (write to a temp name, move on success only). The failure is an account failure when the result, or a nonzero runner's stderr, matches one pattern list kept at the top of the renderer (usage limit, `/login`, not logged in, invalid API key, credit balance, OAuth token expired; any case): exit 4, one stderr line `respeak-render: account failure: <first line of the result>`. Any other runner error stays exit 2. `readme-render.sh` passes 4 through (exit 4, README.md and the source untouched); its header and the renderer's header list 4. Through `make readme` the code reads 2, so the stderr line is the contract a sitting reads. Tests: ADV10's third test (exit 0 with `is_error: true` and a usage-limit result: rc 4, the line, `--out` absent); `is_error: true` with any other text: rc 2, `--out` absent; a runner exiting 1 with `Please run /login` on stderr: rc 4; `readme-render.sh` on a fixture with that runner: rc 4.

Act 4, the source and the newline (ADV10-6, medium; ruling 10). `readme-render.sh` copies the source into its temp directory, writes the status line into the copy, renders and verifies against the copy, and only after the verifier passes moves the copy over `design/readme/source.md` and the render over `README.md`, then stamps. The renderer keeps the source's final newline: a source ending in `\n` gives an output ending in exactly one `\n`; a source without one gives an output without one. Tests: ADV10-6's repro on a fixture (one added test case, a runner exiting 1: rc 2, the source byte-identical, `git status --short` empty); a runner whose result has no trailing newline writes an output ending in one `\n`.

Act 5, the render (ruling 11). `make readme` once (at most two attempts), so the status line carries the new unittest count; the render, the source and the stamp in one commit. An exit 4 or the account-failure line: stop, commit nothing for this act, write it on the charter as the stop reason, leave `make check` to the relay.

Later, for other rows: ADV10-2's half in `scripts/bounded`, ADV10-4 (`make check` reports a refusal as a failure) and ADV10-5 (the lock race) belong to the canonical `bounded` and the conventions' `check` shape in claude-code-session, and reach this repo by re-sync; ADV10-8 (a `NEXT` naming a missing prompt) goes to the canonical doclint; ADV6-4 stays its own packet.

## 3. Interfaces (signatures, not prose)

- `respeak-config.py gate --for F --committed`: `dropped` may hold `"<rel path>: untracked project file"`; `project` is the nearest tracked one or null; outside git, exit 2 with `respeak-config: --committed needs a git work tree`.
- `respeak-deadline.sh SECONDS CMD [ARGS...]`: unchanged exits (CMD's, 124, 143); new: when the script dies, CMD's group gets TERM, then KILL after 2 s. Env `RESPEAK_DEADLINE_GRACE` (2).
- `respeak-render.sh`: exits 0, 1 (the gate), 2 (setup, refusal, runner error), 4 (account failure: one stderr line, `--out` absent).
- `readme-render.sh`: 0, 1, 2, 4; the source and `README.md` untouched unless 0.
- Commits `r10 act N: <one line>`; the charter title `# Sitting <run day>-<n>: claude-code-respeak, <row id>`.

## 4. Findings that name this row

On `main` `e661812` under the virtualenv (3.12.7): `test_check.sh` 40 passed, `test_render.sh` 31, `test_readme_fresh.sh` 11, `test_gate_hook.sh` 56, `test_bounded.sh` 7; `tests.test_config_layers` OK. `test_config_layers.py:545` runs `gate --committed` outside git today (act 1 moves it). `test_readme.py:38` pins the live unittest count: act 5's render keeps `make check` green. `README.md` has no final newline; `design/readme/source.md` has one.

## 5. Forbidden reads

Every other repo. `~/.claude/`. `research/`; `examples/` beyond the tests' fixtures. `CHANGELOG.md` beyond its first 40 lines. `history/` beyond the builder's charter. The relay's ledgers; any transcript.

## 6. Report (capped: one table, at most five bullets, under 800 words)

Each line's last output on the branch beside `main` at this packet's commit (r10a reports its acts' lines, r10b all):

| line | main | branch |
|---|---|---|
| `bash tests/test_check.sh 2>&1 \| tail -1` | `40 passed, 0 failed` | at least 43 passed, 0 failed |
| `bash tests/test_render.sh 2>&1 \| tail -1` | `31 passed, 0 failed` | at least 40 passed, 0 failed |
| `python3 -m unittest tests.test_config_layers 2>&1 \| tail -1` | `OK` | `OK` |
| `grep -c 'account failure' plugin/scripts/respeak-render.sh` | 0 | at least 1 |
| `tail -c 1 README.md \| od -An -c \| tr -d ' '` | `.` | `\n` |
| `git status --short \| wc -l \| tr -d ' '` after the last commit | 0 | 0 |

Bullets: each act's commit; choices beyond §2 with reasons; what was left undone and for whom; at most ONE open fork. Last line: the branch and its head sha.
