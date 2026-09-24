# Adversarial review ADV10: claude-code-respeak since `adv-6-respeak`

Target: `17030b4..353ce7a` (R7, R8, R9: the hermetic check, the bounded spawns, `scripts/bounded`, the README status step). Every repro below ran in a temp repo or a `git archive` copy.

## Findings

**ADV10-1 (high, wrong green; ADV6-1 regressed): a nested project file softens `respeak-check`, and git can hide it.** `--committed` keeps `gate.*` keys from layers graded `project` (`respeak-config.py` `COMMITTED_GATE_KINDS`), and `find_project` picks the nearest ancestor holding `.claude/respeak/config.yaml`. So `docs/.claude/respeak/config.yaml` is "the committed project" for `docs/*`, committed or not. Repro, gate on and `docs/bad.md` holding one error hit: check gives `1 blocked`; add `docs/.claude/respeak/config.yaml` with `gate: {fail_on: none}` and it gives `1 passed`, rc 0; with `gate: {enabled: false}`, `1 skipped`, rc 0; add `docs/.claude/.gitignore` holding `*` and `git status --short` is empty while the whole-tree check exits 0. Fix: under `--committed`, a project file counts only when `git ls-files --error-unmatch` finds it, and is read from the index; an untracked or ignored one is exit 3.

**ADV10-2 (high, unbounded work, fork-storm class): every bound moves its child out of the caller's process group and keeps its watchdog inside it.** `respeak-deadline.sh` starts CMD under `set -m` (a new group) and its watcher in the caller's group; `scripts/bounded` starts CMD with `start_new_session=True` and is its own watchdog. A supervisor that kills its child's group at its own wall (SIGKILL) kills the watchdog and orphans the command with no wall. Repro: `respeak-deadline.sh 20 sleep 347` in a new session, `killpg(SIGKILL)` of that session: the sleep lives past the 20 s wall; the same for `bounded --wall 20 -- sleep 353`; `readme-render.sh` with a runner that sleeps, group-killed at 3 s: one runner orphan. In a sitting, the orphan is `claude -p`, bounded only by `--max-turns 8`. The TERM path works (0 orphans), but both graces are 5 s, so the outer SIGKILL can land before the inner one. Fix: each watchdog also watches its parent (`kill -0 $PPID` or `os.getppid()` changing, once a second) in a process the outer kill does not reach, and kills the child group when the parent dies; inner graces shorter than outer ones.

**ADV10-3 (medium, wrong green; account failure): the renderer ignores `is_error`.** `extract_and_write` in `respeak-render.sh` reads `result` and never `is_error` or `subtype`. Repro: a runner that exits 0 and prints `{"is_error":true,"result":"Claude AI usage limit reached|..."}` gives `wrote ... (passed --fail-on error in round 1)`, rc 0, and the output file is the error line. A runner that exits 1 on a login failure gives rc 2, the same code as a bad argument, so a sitting running `make readme` cannot tell "stop the run" (ruling 1) from "fix the setup" and may retry. Fix: `is_error: true` or a subtype other than `success` is a failure; a usage-limit or login result exits with its own code and one stderr line (`respeak-render: account failure: ...`), which `readme-render.sh` passes through.

**ADV10-4 (medium, wrong red): `make check` turns "not run" into a test failure.** The `check` recipe wraps `scripts/bounded`; make reports any recipe failure as 2, so the lock held, the load breaker, the 900 s wall and a failing suite all read `make check` rc 2. The Makefile comment ("124 at the wall, 2 lock held or load too high") holds for `bounded`, not for `make check`. Repro: `BOUNDED_LOADAVG=1000 BOUNDED_LOAD_MAX=0 make check` gives rc 2 with no suite run; a makefile whose recipe is `bounded --wall 1 -- sleep 5` gives `Error 124` and make rc 2. The relay's gate is `make check`, and gate reds move on (ruling 2), so a loaded Mac reds a good row. Fix: `check` records the outcome (`.check.result`: `ran <rc>` or `refused <reason>`) and the relay reads it, or the verify line calls `bounded` directly; a refusal uses an exit no suite uses (75).

**ADV10-5 (medium, concurrency): `bounded`'s stale-lock takeover lets two runs hold the lock.** `Lock.take` reads the holder, then renames the lock aside. When A takes over a dead holder's lock and B, which read the same dead holder earlier, renames next, B moves A's new lock aside and both run. Repro: two forked takers on a lock owned by a dead pid, the first delayed 0.5 s after `holder()`: both print `taking over ... (dead)` and both report `held`. Fix: `fcntl.flock` on a lock file (the kernel frees it when the holder dies), or after the rename re-read the moved owner and give up unless it is the holder read. The canonical copy lives in the session plugin; this repo carries it verbatim.

**ADV10-6 (medium, dirty tree on failure; ADV6-6 half-fixed): a failed `make readme` rewrites `design/readme/source.md`.** The status step in `scripts/readme-render.sh` (lines 49 to 68) writes the new line into the source before the render. README.md stays untouched, as ADV6-6 asked, but the source does not. Repro in a copy with one added test case and a runner that exits 1: rc 2, `git status` shows ` M design/readme/source.md`, `readme-fresh.sh` reads stale, so `make check` is red until someone reverts the source. Fix: write the status line into a temp copy of the source, render and verify against the copy, and move both files only after the verifier passes.

**ADV10-7 (low): the deadline watcher leaves its `sleep` behind.** `kill "$watcher"` stops the subshell, not its `sleep "$secs"` child. Repro: three runs of `respeak-deadline.sh 43 true` leave one `sleep 43` owned by pid 1. That is one stray per gate hook call (15 s), per suite under `make test` (120 s), per render (600 s). Fix: the watcher runs `sleep & wait $!` under a TERM trap that kills the sleep.

**ADV10-8 (low): doclint admits a `NEXT` that names a missing prompt** (the second half of ADV6-8). Repro: `history/sessions/NEXT` holding `design/packets/nope.md` gives doclint rc 0. Fix, in the canonical doclint: the named path must exist.

## The ADV6 fixes as shipped

| ADV6 | severity | holds? |
|---|---|---|
| 1 folder sidecar | high | Holds for `.respeak.yaml`, `.respeak.local.yaml` and `allow: [".*"]`; regressed through a nested project file (ADV10-1). |
| 2 environment | high | Holds: `RESPEAK_CONFIG`, the provider and the overrides are unset; exit 3 counts as ERROR; the count invariant stands. |
| 3 README stamp | high | Holds for structure and for an orphan stamp. A prose-only sentence added by hand re-stamps `fresh`, rc 0: that door is ADV6-4. |
| 4 prose-only | medium | Open, deferred by R7 to its own packet; the repro still passes. |
| 5 renderer bounds | medium | Holds: depth refusal rc 2, rounds 1 to 5, `--tools`, `--max-turns`, the wall, 0 orphans after TERM. The outer group kill escapes (ADV10-2). |
| 6 failed render | medium | README.md holds; the source does not (ADV10-6). |
| 7 large file | medium | Holds: a 2,760,007-byte file blocks as too large in 0.21 s. |
| 8 doclint | medium | Holds: the `NEXT` exemption and the whole-suite rule landed; the missing-prompt check did not (ADV10-8). |
| 9 public paths | high | As ruled: prompts repo-relative; `home` stays on rows files until ruling 8, `private` on charters (ruling 13). |

## Verdict

Closer, not ready. The CI verdict no longer moves with the environment, a folder file or a hand-stamped README, but it still moves with one untracked file in the right place (ADV10-1), and the bounds that R7 and R8 added escape the one kill a supervisor sends at its wall (ADV10-2). Fix those two before the device project trusts this gate, with ADV10-3, since it is the plugin's only `claude -p` spawn and ruling 1 depends on telling an account failure apart. ADV10-4 and ADV10-5 belong to the shared `bounded` and the conventions' `check` shape, so they go to the session plugin's packet and reach this repo by re-sync. ADV10-6 goes in the next respeak packet; 7 and 8 are hygiene.

## First three tests

1. `tests/test_check.sh`: an ignored `docs/.claude/respeak/config.yaml` at `fail_on: none` leaves `docs/bad.md` BLOCKED, rc 1.
2. `tests/test_render.sh` and `tests/test_bounded.sh`: start the deadline script, `bounded`, and the renderer with a sleeping runner in a new session, SIGKILL the session's group, and assert no survivor after the inner wall.
3. `tests/test_render.sh`: a runner that exits 0 with `is_error: true` makes the renderer exit nonzero and leaves `--out` absent.
