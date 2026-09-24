# Adversarial review ADV11: claude-code-respeak since `adv-10-respeak`

Target: `e661812..4a3dfa4` (packets R10, R11, R12): `respeak-config.py --committed`, `respeak-deadline.sh`, `respeak-render.sh`, `readme-render.sh`, the re-synced `scripts/bounded`, `doclint` and `hygiene`, and their tests. Every reproduction below ran in a temp directory with `CLAUDE_CONFIG_DIR` and the plugin root pinned, never against the real checkout's state.

## Findings

**ADV11-1 (high, wrong green; ADV10-1 regressed): a nested git repository softens `respeak-check`, and the outer status stays clean.** Under `--committed`, `find_project` asks `tracked_name(a, PROJECT_REL)`, which runs `git -C a ls-files --error-unmatch`. When `a` is the top of a nested repository, that git answers for the nested index, so the nested repository's project file counts as "committed" and `index_file_layer` reads it from the nested index. `git_toplevel(given)` is computed but never compared with the project's work tree. Repro: outer repo with a project file at `fail_on: error` and a tracked `docs/bad.md` holding one error hit; the check gives `1 blocked`. Then `git init docs`, commit `docs/.claude/respeak/config.yaml` there at `fail_on: none`, and add `docs/.claude/` to the outer `.git/info/exclude`: `git status --short` prints nothing and the whole-tree check gives `1 passed`, rc 0. Fix: under `--committed`, a project file counts only when `git rev-parse --show-toplevel` from its directory equals the target's work tree; any other is dropped as `untracked project file`.

**ADV11-2 (high, wrong green, fails open): a git failure reads as "untracked", and the gate then skips.** `git_out` returns `None` on a non-zero exit or the 10 s timeout, and `tracked_name` turns `None` into "not tracked". The root project file is then dropped, the plugin defaults apply, and a blocked doc becomes `skipped`. Repro: a `git` shim on `PATH` that exits 128 for `ls-files --error-unmatch` and passes everything else through: `respeak-check.sh` on a tree whose only doc is blocked gives `0 passed, 1 skipped, 0 blocked`, rc 0. A loaded Mac, the condition every bound in this repo exists for, is where a 10 s git timeout happens. Fix: `git_out` tells "git said no" (exit 1 from `--error-unmatch`) apart from "git failed" (any other exit, a timeout, `OSError`), and the second raises `SetupError`, so the check exits 2 and never 0.

**ADV11-3 (medium, wrong red; ADV10-4 half-fixed): `make check` still hides the refusal, and its last stderr line is make's, not bounded's.** The Makefile comment now says the exit alone cannot tell a refusal from a red suite and that "a last stderr line `bounded: stop: lock|load|wall`" does. Make prints its own line after the recipe fails. Repro: `BOUNDED_LOADAVG=1000 BOUNDED_LOAD_MAX=0 make check 2>&1 >/dev/null | tail -2` prints `bounded: stop: load` then `make: *** [check] Error 2`. A gate that reads the last line, as the comment tells it to, sees a red. `make readme` has the same shape: the renderer's account exit 4 reaches the sitting as make's 2. Fix: the gate reads the last `bounded: stop:` line anywhere in stderr (the contract says so in the Makefile and in conventions §5), or the verify line calls `scripts/bounded ... -- make check-unlocked` directly so its exit is the verdict.

**ADV11-4 (medium, wrong red, concurrency): the survivor tests count every matching process on the Mac.** `tests/test_bounded.sh` lines 78 and 93 run `pgrep -f 'sleep 353'` and `pgrep -f 'sleep 32'`; `tests/test_render.sh` line 21 (`survivors`, `gone`) does the same for `sleep 45.25`, `sleep 44.25` and `sleep 43$`. The patterns are not anchored, and the check lock is per tree, so a second worktree running the same suite at the same moment is counted. Repro: start `sleep 3539` and `sleep 327` from an unrelated process, then `bash tests/test_bounded.sh`: `17 passed, 2 failed`, both on the survivor checks. The relay runs sibling worktrees in parallel, and the canonical copy of `bounded` carries the same suite shape. Fix: each case sleeps a per-run value (for example `353.$$`) and matches it anchored (`pgrep -fx`), or the test records the command's pgid and checks `kill -0 -PGID`.

**ADV11-5 (medium, account failure not told apart): the account regex is four phrasings, and stdout outside JSON is never read.** `ACCOUNT_FAILURE_RE` in `respeak-render.sh` matches `usage limit`, `/login`, `not logged in`, `invalid api key`, `credit balance` and an expired OAuth token. Measured against the pattern: `Claude AI usage limit reached|...` and `Invalid API key · Please run /login` match; `5-hour limit reached ∙ resets 3pm`, `Weekly limit reached ∙ resets Mon 9am` and `API Error: 429 rate_limit_error` do not. Separately, a runner that prints `Claude AI usage limit reached|1790000000` as plain text and exits 1 gives rc 2, because the raw stdout is searched only after it parses as JSON. Whether the CLI prints the unmatched phrasings today is not measured here; the regex has no test beyond the one fixture line. Either way the renderer returns 2, the "fix the setup" code, and ruling 1's stop depends on 4. Fix: search the raw stdout as well as the result and stderr, add `limit reached` and `rate_limit` to the pattern, and share one pattern with the relay's account stop so the two cannot drift.

**ADV11-6 (low): ADV10-8 is still open.** `history/sessions/NEXT` holding `design/packets/nope.md` passes doclint (no `next` line in its output). The fix belongs to the canonical doclint and reaches this repo by re-sync.

## The ADV10 fixes as shipped

| ADV10 | severity | as shipped |
|---|---|---|
| 1 nested project file | high | Holds for an untracked or ignored file and for a working copy that differs from the index; regressed through a nested repository (ADV11-1) and through a git failure (ADV11-2). |
| 2 group kill escapes the bound | high | Holds. A SIGKILL of the caller's group at 1.5 s leaves no survivor of `respeak-deadline.sh 30 sleep 3471` or `bounded --wall 30 -- sleep 3531` 4 s later. |
| 3 renderer ignores `is_error` | medium | Holds for `is_error`, a non-success `subtype`, and the fixture's usage-limit line (exit 4, nothing at `--out`); the pattern is narrow (ADV11-5). |
| 4 `make check` flattens exits | medium | Half: `bounded` writes the stop line, but make's line follows it (ADV11-3). |
| 5 lock takeover race | medium | Holds: `flock`; a second runner on a held lock exits 2, and a SIGKILLed holder frees the lock at once. |
| 6 failed render dirties the source | medium | Holds: a runner that exits 1 after one added test case leaves `git status` clean. |
| 7 stray `sleep` | low | Holds: three quick runs leave no timer behind. |
| 8 `NEXT` names a missing prompt | low | Open (ADV11-6). |

## Verdict

Not ready to gate syrvis's docs. The bounds are sound now: no survivor after a group SIGKILL, one lock holder, no dirty source after a failed render. But the CI verdict still moves without a trace in `git status` (ADV11-1), and it fails open when git fails (ADV11-2). Both are wrong greens in `respeak-config.py`, a few lines each, and both come before syrvis. ADV11-3 needs one line in the relay's gate or the verify row, and ADV11-5 needs one shared pattern; both go with the relay's account-stop work. ADV11-4 goes in the next respeak packet and the canonical `bounded` suite. ADV11-6 is hygiene.

## First three tests

1. `tests/test_check.sh`: a nested `git init docs` whose own index holds a `fail_on: none` project file, excluded from the outer repo, still gives `1 blocked`, rc 1, and names the drop.
2. `tests/test_check.sh`: a `git` shim that fails `ls-files --error-unmatch` makes `respeak-check.sh` exit 2 with a `respeak-config:` line, never 0.
3. `tests/test_bounded.sh`: the survivor cases pass while an unrelated `sleep 3539` and `sleep 327` run (the ADV11-4 repro as a regression test).
