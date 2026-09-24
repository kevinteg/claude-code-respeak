# Packet R13: the ADV11 fixes, a committed project file in the target's own tree and a git failure that fails closed

| item | value |
|---|---|
| from | `design/review-adv11.md` (ADV11-1, 2, 5, 4, 3); ruling 1 (an account failure stops the run) |
| pin | claude-code-respeak `main` at `5daf506` or later. Branch and worktree named by the row id, off it |
| wall | this repo; no push, `--amend`, rebase, device, tag, version bump; no real `claude` beyond `plugin validate` inside `make check`; no `make readme`; no test opens a path under the real checkout except the scripts it tests |
| may touch | `CHANGELOG.md` (a bullet per act under `## Unreleased`), `Makefile` (its comment lines only), `plugin/docs/config-layers.md`, `plugin/scripts/respeak-check.sh`, `plugin/scripts/respeak-config.py`, `plugin/scripts/respeak-render.sh`, `tests/test_bounded.sh`, `tests/test_check.sh`, `tests/test_render.sh`; the charter. Nothing else |
| acceptance | the lines of §6 with their baselines, targeted, under a minute each |
| verify | `make check` |
| budget | one row, `r13-fixes-adv11`, 80 turns; 144k context; one commit per act; the charter's open names doclint's five rows; checkpoint at 80% |
| close | `make check` in the foreground, then commit in the same turn; before the last commit measure the charter: under 4,096 bytes (`wc -c`), no home path (`scripts/hygiene`), `grep -c '(filled at close)'` reads 0 |

## 1. What the source says (quoted)

ADV11: "a nested git repository softens `respeak-check`, and the outer status stays clean"; "a git failure reads as 'untracked', and the gate then skips"; "the account regex is four phrasings, and stdout outside JSON is never read"; "the survivor tests count every matching process on the Mac"; "`make check` still hides the refusal, and its last stderr line is make's". Each repro is its act's first test, red before the fix.

## 2. Rulings

Act 1, the target's own work tree (ADV11-1, high). Under `--committed`, `find_project` judges an ancestor `a` holding `.claude/respeak/config.yaml` in this order: `a` not under the target's toplevel (path-wise, after `real`): dropped as `<path>: untracked project file`, no git call. `a` under it: `git -C a rev-parse --show-toplevel` (strict, act 2); an answer other than the target's toplevel is a nested repository, dropped the same way. Only then `tracked_name`. `index_file_layer` reads through the same checked path. The hook (no `--committed`) keeps the working-tree rule. `config-layers.md` "Trust boundaries" gets one sentence. Tests in `test_check.sh`: ADV11's first test (`git init docs`, its index holds `docs/.claude/respeak/config.yaml` at `fail_on: none`, `docs/.claude/` in the outer `.git/info/exclude`, outer `git status --short` empty: `docs/bad.md` still `1 blocked`, rc 1, the drop printed); the same at `enabled: false`; a project file tracked in the outer repo beside the nested one still governs.

Act 2, git fails closed (ADV11-2, high). A new `git_ask(cwd, *args)` beside `git_out`: stdout on exit 0, `None` on exit 1 (git's "no" for `--error-unmatch`), and `SetupError("git failed: git <args>: <reason>")` on any other exit, a timeout, or `OSError`. `tracked_name`, `index_file_layer` and act 1's nested check use it; `git_toplevel` keeps `git_out` (outside a repo is an answer there, and `resolve` already raises on it). The timeout reads `RESPEAK_GIT_TIMEOUT` (default 10 s) so a test can shorten it. `respeak-gate.sh --committed` exits 3 on it as today. `respeak-check.sh`: a gate exit 3 whose output holds `respeak-config: git failed` prints that line and exits 2 at once (fail early: a git failure spoils every file, not one). Tests in `test_check.sh`: ADV11's second test (a `git` shim first on `PATH` that exits 128 for `ls-files --error-unmatch` and execs the real git otherwise: rc 2, the `respeak-config: git failed` line, no `skipped`); a shim that sleeps 3 s on `ls-files` under `RESPEAK_GIT_TIMEOUT=1`: rc 2; an untracked project file with a healthy git still drops (rc 1, the drop).

Act 3, account failures (ADV11-5, medium; ruling 1). `ACCOUNT_FAILURE_RE` adds `limit reached` and `rate_limit`. On a failed run the renderer searches the result, the runner's stderr, and the raw stdout, whether or not it parsed as JSON; the first matching line is the one printed. Everything else is unchanged: exit 4, `--out` absent. Choice inside ruling 1: the relay owns the account stop, so its pattern is the canonical one; this renderer keeps its own copy until a re-sync brings the relay's, and the drift guard is a test per measured phrasing. Tests in `test_render.sh`: `5-hour limit reached ∙ resets 3pm`, `Weekly limit reached ∙ resets Mon 9am` and `API Error: 429 rate_limit_error` as an `is_error` result each give rc 4; a runner printing `Claude AI usage limit reached|1790000000` as plain text and exiting 1 gives rc 4; a plain-text `boom` with exit 1 still gives rc 2.

Act 4, survivors counted by this run only (ADV11-4, medium). Every survivor marker in `test_bounded.sh` and `test_render.sh` carries the run's pid (for example `sleep 353.$$`) and is matched whole with `pgrep -fx`; a marker the test does not choose (the deadline's own timer) is matched whole too. The regression test is ADV11's third: before the survivor cases, the suite starts decoys that an unanchored pattern would count (the run's marker with one digit appended, for each marker) and kills them on exit (a trap); every survivor case passes while they run.

Act 5, the refusal line (ADV11-3, respeak's half). The Makefile comment says the gate reads the last `bounded: stop:` line anywhere in stderr, because make prints its own `Error 2` line after it, and that `make readme`'s account failure is likewise the `respeak-render: account failure` line, never the exit. The reading itself is the relay gate's, carried by the relay's packet.

No new unittest case and no new `tests/*.sh` file: `tests/test_readme.py` pins both counts against the README's status line, and this packet renders nothing.

Later, for other rows: ADV11-6 (a `NEXT` naming a missing prompt) belongs to the canonical doclint and reaches this repo by re-sync; the canonical `bounded` suite takes act 4's shape through its own row; ADV11-3's gate reading and one shared account pattern belong to the relay.

## 3. Interfaces (signatures, not prose)

- `respeak-config.py gate --for F --committed`: `dropped` may hold `"<rel path>: untracked project file"` for a file outside the target's work tree or in a nested repository; a git failure exits 2 with `respeak-config: git failed: ...`.
- `respeak-gate.sh --committed`: 0, 2 (blocked), 3 (setup, including a git failure).
- `respeak-check.sh`: 0, 1, 2; 2 now also for a git failure, with the line.
- `respeak-render.sh`: 0, 1, 2, 4 unchanged; 4 is reached from stdout text as well.
- Env `RESPEAK_GIT_TIMEOUT` (seconds, default 10).
- Commits `r13 act N: <one line>`; the charter title `# Sitting <run day>-<n>: claude-code-respeak, r13-fixes-adv11`.

## 4. Findings that name this row

On `main` `5daf506` under the virtualenv (3.12.7): `test_check.sh` 45 passed, `test_render.sh` 51, `test_bounded.sh` 19; `tests.test_config_layers` OK. `respeak-config.py:451` `git_out` returns `None` for every failure; `:473` `tracked_name` reads that as untracked; `:520` is the only caller under `--committed`; `:828` computes the toplevel that act 1 compares against. `git ls-files --error-unmatch` exits 1 for an untracked path and 128 outside a repository (measured). `respeak-check.sh:142` counts a gate exit 3 as an error, rc 1. `respeak-render.sh:86` is the pattern; `:248` and `:251` search the result and stderr only. `test_bounded.sh:78` and `:93`, `test_render.sh:21` are the unanchored `pgrep -f`. `Makefile:22` is the comment act 5 corrects.

## 5. Forbidden reads

Every other repo. `~/.claude/`. `research/`; `examples/` beyond the tests' fixtures. `CHANGELOG.md` beyond its first 40 lines. `history/` beyond the builder's charter. The relay's ledgers; any transcript.

## 6. Report (capped: one table, at most five bullets, under 800 words)

Each line's last output on the branch beside `main` at this packet's commit:

| line | main | branch |
|---|---|---|
| `bash tests/test_check.sh 2>&1 \| tail -1` | `45 passed, 0 failed` | at least 50 passed, 0 failed |
| `bash tests/test_render.sh 2>&1 \| tail -1` | `51 passed, 0 failed` | at least 56 passed, 0 failed |
| `bash tests/test_bounded.sh 2>&1 \| tail -1` | `19 passed, 0 failed` | at least 20 passed, 0 failed |
| `python3 -m unittest tests.test_config_layers 2>&1 \| tail -1` | `OK` | `OK` |
| `grep -c 'limit reached' plugin/scripts/respeak-render.sh` | 0 | at least 1 |
| `grep -c 'anywhere in stderr' Makefile` | 0 | 1 |
| `git status --short \| wc -l \| tr -d ' '` after the last commit | 0 | 0 |

Bullets: each act's commit; choices beyond §2 with reasons; what was left undone and for whom; at most ONE open fork. Last line: the branch and its head sha.
